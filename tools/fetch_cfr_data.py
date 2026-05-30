#!/usr/bin/env python3
"""Ingest CFR main lines (Romanian railways) from OpenStreetMap.

Data sources
------------
* **Geometry / coordinates:** OpenStreetMap via Overpass API.
  © OpenStreetMap contributors, licensed under ODbL 1.0.
  Attribution must be included when redistributing derived data.
* **Line definitions:** CFR magistrale 200–900 ("Căile Ferate Române main
  lines", Wikipedia). These are Romania's busiest main axes carrying regular
  IC/IR services between major cities.

The script intentionally covers only *main routes* and *major cities* — no
branch lines, not every stop. Only regularly served junction/city stations are
included per magistrală.

CRS rationale
-------------
GeoJSON output is **deliberately EPSG:4326 (WGS84 lon/lat)** — not the
Romanian EPSG:3844 (Stereo70). This is not a display compromise but a spec
requirement: RFC 7946 §4 mandates WGS84 for GeoJSON. Web consumers (Leaflet,
Mapbox, GitHub preview) interpret coordinates as lon/lat regardless. The
*projected* working CRS 3844 enters one step later: ``reiseplan-cli build-gpkg``
reprojects to EPSG:3844 via ``ogr2ogr -t_srs EPSG:3844``. Short: GeoJSON =
exchange format (4326), GPKG = working bundle (3844). Do not "clean up" the
GeoJSON by switching to 3844.

Output files (all EPSG:4326, schema compatible with the rest of the project)
---------------------------------------------------------------------------
* ``data/processed/rail_stations.geojson``  – stations (Point)
* ``data/processed/rail_lines.geojson``     – magistrale (LineString), enriched
                                              with connection data from ``timetable.csv``
* ``data/processed/route_stops.csv``        – stop sequences per magistrală
* ``data/raw/osm_ro_stations.json``         – raw Overpass response cache

``data/processed/timetable.csv`` is created as a scaffold template (one row per
magistrală) **only if it does not yet exist** — it is the *hand-maintained*
source for real connections (dep/arr/days/via) and is never overwritten here.

Timetable times: CFR does not publish an open GTFS feed. Times in
``timetable.csv`` are maintained manually (live lookup at
https://mersultrenurilor.infofer.ro). ``trip_hint`` in ``route_stops.csv``
describes each stop's role qualitatively (start / end / interchange).

Usage
-----
    uv run python tools/fetch_cfr_data.py            # query Overpass, cache, build
    uv run python tools/fetch_cfr_data.py --offline  # rebuild from cache only

After entering real times into ``timetable.csv``, re-run with ``--offline`` —
the times will be merged into ``rail_lines.geojson``.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from _paths import PROCESSED, ROOT
from timetable import (
    TIMETABLE_COLUMNS,
    TIMETABLE_FIELDS,
    TIMETABLE_PATH,
    load_timetable,
)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "reisefuehrer-dataintegration/0.1 (jan@sternprodukt.de)"

# Fetch all named rail stops (station/halt/stop) in Romania. Filtering down to
# the defined magistrală stops happens locally — one network request, then offline.
OVERPASS_QUERY = """
[out:json][timeout:120];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
node["railway"~"^(station|halt|stop)$"]["name"](area.ro);
out tags center;
"""


# --------------------------------------------------------------------------- #
# Line definitions                                                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Stop:
    """A stop on a magistrală.

    ``name`` is the canonical (display) name, ``city`` the city it belongs to.
    ``osm_names`` lists alternative OSM spellings used for name matching;
    the canonical name is always searched first.
    """

    name: str
    city: str
    osm_names: tuple[str, ...] = field(default_factory=tuple)

    def lookup_names(self) -> tuple[str, ...]:
        return (self.name, *self.osm_names)


@dataclass(frozen=True)
class Line:
    ref: str          # CFR magistrală, e.g. "M300"
    route_name: str   # display name (DE)
    tags: str         # comma-separated topic tags
    length_km: int    # official route length (Wikipedia)
    stops: tuple[Stop, ...]

    @property
    def from_city(self) -> str:
        return self.stops[0].city

    @property
    def to_city(self) -> str:
        return self.stops[-1].city


# Known OSM name deviations, maintained as aliases:
#   "Gara de Nord"  -> București Nord
#   "Gara Iași"     -> Iași
#   "Cluj Napoca"   -> Cluj-Napoca (OSM omits the hyphen)
MAIN_LINES: tuple[Line, ...] = (
    Line(
        ref="M200",
        route_name="M200 · Brașov – Sibiu – Arad (Karpatenrand)",
        tags="hauptstrecke,siebenbürgen,karpaten",
        length_km=500,
        stops=(
            Stop("Brașov", "Brașov"),
            Stop("Făgăraș", "Făgăraș"),
            Stop("Sibiu", "Sibiu"),
            Stop("Simeria", "Simeria"),
            Stop("Deva", "Deva"),
            Stop("Arad", "Arad"),
            Stop("Curtici", "Curtici"),
        ),
    ),
    Line(
        ref="M300",
        route_name="M300 · București – Brașov – Cluj-Napoca – Oradea (Transsilvanien-Magistrale)",
        tags="hauptstrecke,siebenbürgen,dracula,city",
        length_km=647,
        stops=(
            Stop("București Nord", "București", ("Gara de Nord",)),
            Stop("Ploiești Vest", "Ploiești"),
            Stop("Brașov", "Brașov"),
            Stop("Sighișoara", "Sighișoara"),
            Stop("Mediaș", "Mediaș"),
            Stop("Teiuș", "Teiuș"),
            Stop("Cluj-Napoca", "Cluj-Napoca", ("Cluj Napoca",)),
            Stop("Oradea", "Oradea"),
        ),
    ),
    Line(
        ref="M400",
        route_name="M400 · Brașov – Dej – Satu Mare (Nordsiebenbürgen)",
        tags="hauptstrecke,maramuresch,nord",
        length_km=560,
        stops=(
            Stop("Brașov", "Brașov"),
            Stop("Dej Călători", "Dej"),
            Stop("Baia Mare", "Baia Mare"),
            Stop("Satu Mare", "Satu Mare"),
        ),
    ),
    Line(
        ref="M500",
        route_name="M500 · București – Bacău – Suceava (Moldau-Magistrale)",
        tags="hauptstrecke,moldau,city",
        length_km=488,
        stops=(
            Stop("București Nord", "București", ("Gara de Nord",)),
            Stop("Ploiești Vest", "Ploiești"),
            Stop("Buzău", "Buzău"),
            Stop("Focșani", "Focșani"),
            Stop("Bacău", "Bacău"),
            Stop("Pașcani", "Pașcani"),
            Stop("Suceava", "Suceava"),
        ),
    ),
    Line(
        ref="M600",
        route_name="M600 · Făurei – Bârlad – Iași (Ost-Moldau)",
        tags="hauptstrecke,moldau,ost",
        length_km=395,
        stops=(
            Stop("Făurei", "Făurei"),
            Stop("Bârlad", "Bârlad"),
            Stop("Vaslui", "Vaslui"),
            Stop("Iași", "Iași", ("Gara Iași",)),
        ),
    ),
    Line(
        ref="M700",
        route_name="M700 · București – Brăila – Galați (Donau-Anschluss)",
        tags="hauptstrecke,donau,galați",
        length_km=229,
        stops=(
            Stop("București Nord", "București", ("Gara de Nord",)),
            Stop("Buzău", "Buzău"),
            Stop("Făurei", "Făurei"),
            Stop("Brăila", "Brăila"),
            Stop("Galați", "Galați"),
        ),
    ),
    Line(
        ref="M800",
        route_name="M800 · București – Constanța – Mangalia (Schwarzmeer-Küste)",
        tags="hauptstrecke,küste,schwarzmeer,delta",
        length_km=225,
        stops=(
            Stop("București Nord", "București", ("Gara de Nord",)),
            Stop("Fetești", "Fetești"),
            Stop("Medgidia", "Medgidia"),
            Stop("Constanța", "Constanța"),
            Stop("Mangalia", "Mangalia"),
        ),
    ),
    Line(
        ref="M900",
        route_name="M900 · București – Craiova – Timișoara (Banat-Magistrale)",
        tags="hauptstrecke,banat,donau,city",
        length_km=533,
        stops=(
            Stop("București Nord", "București", ("Gara de Nord",)),
            Stop("Craiova", "Craiova"),
            Stop("Drobeta-Turnu Severin", "Drobeta-Turnu Severin", ("Drobeta Turnu Severin",)),
            Stop("Caransebeș", "Caransebeș"),
            Stop("Timișoara Nord", "Timișoara"),
        ),
    ),
)


# --------------------------------------------------------------------------- #
# Paths                                                                       #
# --------------------------------------------------------------------------- #
RAW_PATH = ROOT / "data" / "raw" / "osm_ro_stations.json"
STATIONS_OUT = PROCESSED / "rail_stations.geojson"
LINES_OUT = PROCESSED / "rail_lines.geojson"
ROUTE_STOPS_OUT = PROCESSED / "route_stops.csv"

# TIMETABLE_PATH / TIMETABLE_COLUMNS / TIMETABLE_FIELDS / load_timetable
# live in tools/timetable.py (shared schema, see import above).


# --------------------------------------------------------------------------- #
# Overpass fetch (defensive)                                                  #
# --------------------------------------------------------------------------- #
def fetch_overpass() -> dict:
    """Query Overpass and return parsed JSON.

    Raises ``SystemExit`` with a clear message on network or parse errors
    instead of propagating a broken response.
    """
    request = urllib.request.Request(
        OVERPASS_URL,
        data=urllib.parse.urlencode({"data": OVERPASS_QUERY}).encode("utf-8"),
        headers={"User-Agent": USER_AGENT,
                 "Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as resp:
            payload = resp.read()
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Overpass HTTP-Fehler {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Overpass nicht erreichbar: {exc.reason}")

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Overpass lieferte kein gültiges JSON: {exc}")

    elements = data.get("elements")
    if not elements:
        raise SystemExit("Overpass-Antwort enthält keine Elemente – Abbruch.")
    return data


def load_or_fetch(offline: bool) -> dict:
    if offline:
        if not RAW_PATH.is_file():
            raise SystemExit(f"--offline, aber Cache fehlt: {RAW_PATH}")
        print(f"[offline] lese Roh-Cache: {RAW_PATH}")
        return json.loads(RAW_PATH.read_text(encoding="utf-8"))

    print("[online]  frage Overpass ab …")
    data = fetch_overpass()
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[online]  {len(data['elements'])} Bahn-Halte gecacht → {RAW_PATH}")
    return data


# --------------------------------------------------------------------------- #
# Index + resolution                                                          #
# --------------------------------------------------------------------------- #
# Higher-ranked railway types win on name collision.
_RAILWAY_RANK = {"station": 0, "halt": 1, "stop": 2}


def build_index(data: dict) -> dict[str, tuple[float, float]]:
    """Return name → (lon, lat). On duplicate names, highest-ranked type wins."""
    best: dict[str, tuple[int, float, float]] = {}
    for el in data["elements"]:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        # Nodes carry lat/lon directly; ways/relations only have ``center``.
        # Use explicit ``in`` check (not ``or``) so lat/lon == 0.0 is not
        # treated as missing and does not incorrectly fall back to center.
        center = el.get("center", {})
        lat = el["lat"] if "lat" in el else center.get("lat")
        lon = el["lon"] if "lon" in el else center.get("lon")
        if lat is None or lon is None:
            continue
        rank = _RAILWAY_RANK.get(tags.get("railway", ""), 9)
        if name not in best or rank < best[name][0]:
            best[name] = (rank, lon, lat)
    return {name: (lon, lat) for name, (_, lon, lat) in best.items()}


def resolve(stop: Stop, index: dict[str, tuple[float, float]]) -> tuple[float, float] | None:
    for candidate in stop.lookup_names():
        if candidate in index:
            return index[candidate]
    return None


# --------------------------------------------------------------------------- #
# Output                                                                      #
# --------------------------------------------------------------------------- #
def feature_collection(name: str, features: list[dict]) -> dict:
    return {
        "type": "FeatureCollection",
        "name": name,
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": features,
    }


def write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Timetable (hand-maintained)                                                 #
# --------------------------------------------------------------------------- #
def scaffold_timetable() -> None:
    """Create ``timetable.csv`` as a template — only if it does not yet exist.

    One row per magistrală, pre-filled with ``route_id``/``from_city``/
    ``to_city`` and the ``via`` city chain. Times/days/train are left empty for
    hand-entry. Existing files are **never** overwritten.
    """
    if TIMETABLE_PATH.is_file():
        return
    rows = []
    for line in MAIN_LINES:
        cities = [stop.city for stop in line.stops]
        rows.append({
            "route_id": line.ref,
            "from_city": cities[0],
            "to_city": cities[-1],
            "days": "",
            "dep_time": "",
            "arr_time": "",
            "duration": "",
            "via": ", ".join(cities[1:-1]),
            "train": "",
            "approx": "",
            "notes": "",
        })
    with TIMETABLE_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(TIMETABLE_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  → {TIMETABLE_PATH.relative_to(ROOT)} (Vorlage, {len(rows)} Zeilen – Zeiten bitte ergänzen)")


def build_outputs(index: dict[str, tuple[float, float]]) -> None:
    timetable = load_timetable()
    station_ids: dict[str, str] = {}          # canonical name -> ST-ID
    station_features: list[dict] = []
    route_features: list[dict] = []
    stop_rows: list[dict] = []
    missing: list[str] = []

    def station_id_for(stop: Stop, coords: tuple[float, float]) -> str:
        if stop.name not in station_ids:
            sid = f"ST{len(station_ids) + 1:02d}"
            station_ids[stop.name] = sid
            station_features.append({
                "type": "Feature",
                "properties": {"station_id": sid, "name": stop.name, "city": stop.city},
                "geometry": {"type": "Point", "coordinates": [coords[0], coords[1]]},
            })
        return station_ids[stop.name]

    for line in MAIN_LINES:
        resolved: list[tuple[Stop, tuple[float, float]]] = []
        for stop in line.stops:
            coords = resolve(stop, index)
            if coords is None:
                missing.append(f"{line.ref}: {stop.name}")
                continue
            resolved.append((stop, coords))

        if len(resolved) < 2:
            print(f"  ! {line.ref}: zu wenige auflösbare Halte – übersprungen.")
            continue

        for seq, (stop, coords) in enumerate(resolved, start=1):
            station_id_for(stop, coords)
            if seq == 1:
                hint = f"Start ({stop.city})"
            elif seq == len(resolved):
                hint = f"Ziel ({stop.city})"
            else:
                hint = f"Halt / Umstieg ({stop.city})"
            stop_rows.append({
                "route_id": line.ref,
                "sequence": seq,
                "station": stop.name,
                "city": stop.city,
                "trip_hint": hint,
            })

        # Merge connection data from the hand-maintained timetable.csv
        # (1:1 per magistrală via route_id; missing rows leave fields empty).
        tt = timetable.get(line.ref, {})
        properties = {
            "route_id": line.ref,
            "route_name": line.route_name,
            "from_city": resolved[0][0].city,
            "to_city": resolved[-1][0].city,
            "tags": line.tags,
            "line_ref": line.ref,
            "length_km": line.length_km,
        }
        for field_name in TIMETABLE_FIELDS:
            properties[field_name] = tt.get(field_name, "")

        route_features.append({
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "LineString",
                "coordinates": [[lon, lat] for _, (lon, lat) in resolved],
            },
        })

    write_json(STATIONS_OUT, feature_collection("rail_stations", station_features))
    write_json(LINES_OUT, feature_collection("rail_lines", route_features))

    with ROUTE_STOPS_OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["route_id", "sequence", "station", "city", "trip_hint"],
        )
        writer.writeheader()
        writer.writerows(stop_rows)

    print(f"  → {STATIONS_OUT.relative_to(ROOT)} ({len(station_features)} Bahnhöfe)")
    print(f"  → {LINES_OUT.relative_to(ROOT)} ({len(route_features)} Magistralen)")
    print(f"  → {ROUTE_STOPS_OUT.relative_to(ROOT)} ({len(stop_rows)} Halte)")
    if missing:
        print("  ! nicht aufgelöst (in Geometrie ausgelassen):")
        for item in missing:
            print(f"      - {item}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true",
                        help="Nur aus data/raw/osm_ro_stations.json neu bauen (kein Netz).")
    args = parser.parse_args()

    data = load_or_fetch(args.offline)
    index = build_index(data)
    print(f"[index]   {len(index)} eindeutige Halte-Namen indiziert.")
    scaffold_timetable()   # create template only if missing, before we read it
    build_outputs(index)
    print("[fertig]  GPKG erneuern? → uv run reiseplan-cli build-gpkg")


if __name__ == "__main__":
    main()
