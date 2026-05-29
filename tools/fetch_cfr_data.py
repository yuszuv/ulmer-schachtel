#!/usr/bin/env python3
"""Ingestion der CFR-Hauptstrecken (rumänische Eisenbahn) aus OpenStreetMap.

Datenquellen
------------
* **Geometrie / Koordinaten:** OpenStreetMap via Overpass API.
  © OpenStreetMap-Mitwirkende, lizenziert unter ODbL 1.0.
  Bei Weitergabe der Daten ist diese Attribution beizulegen.
* **Liniendefinition:** Die CFR-Magistralen 200–900 ("Căile Ferate Române
  main lines", Wikipedia). Das sind die meistbefahrenen Hauptachsen Rumäniens
  und tragen die regelmäßigen IC/IR-Verbindungen zwischen den größeren Städten.

Das Skript ist bewusst auf die *Haupt-Routen* und die *größeren Städte*
beschränkt – keine Lokalbahnen, nicht jeder Haltepunkt. Pro Magistrale sind
nur die regelmäßig bedienten Knoten-/Stadtbahnhöfe hinterlegt.

Erzeugte Dateien (alle EPSG:4326, Schema kompatibel zum bestehenden Projekt)
----------------------------------------------------------------------------
* ``data/processed/rail_stations.geojson``       – Bahnhöfe (Point)
* ``data/processed/rail_route_options.geojson``  – Magistralen (LineString)
* ``data/processed/sample_connections.csv``      – Haltefolgen je Magistrale
* ``data/raw/osm_ro_stations.json``              – Roh-Cache der Overpass-Antwort

Fahrplanzeiten: CFR stellt keinen offenen GTFS-Feed bereit. Die Spalten
``arrival_local`` / ``departure_local`` bleiben daher leer; exakte Zeiten sind
unter https://mersultrenurilor.infofer.ro abrufbar. ``trip_hint`` beschreibt
die Rolle des Halts (Start/Ziel/Umstieg) qualitativ.

Aufruf
------
    uv run python tools/fetch_cfr_data.py            # Overpass abfragen + cachen + bauen
    uv run python tools/fetch_cfr_data.py --offline  # nur aus Roh-Cache neu bauen
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

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "reisefuehrer-dataintegration/0.1 (jan@sternprodukt.de)"

# Alle benannten Bahn-Halte (station/halt/stop) in Rumänien. Wir filtern lokal
# auf die unten definierten Magistralen-Halte – ein Abruf, danach offline.
OVERPASS_QUERY = """
[out:json][timeout:120];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
node["railway"~"^(station|halt|stop)$"]["name"](area.ro);
out tags center;
"""


# --------------------------------------------------------------------------- #
# Liniendefinition                                                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Stop:
    """Ein Halt auf einer Magistrale.

    ``name`` ist der kanonische (angezeigte) Name, ``city`` die Stadt.
    ``osm_names`` listet alternative OSM-Schreibweisen für das Matching auf;
    der kanonische Name wird automatisch mitgesucht.
    """

    name: str
    city: str
    osm_names: tuple[str, ...] = field(default_factory=tuple)

    def lookup_names(self) -> tuple[str, ...]:
        return (self.name, *self.osm_names)


@dataclass(frozen=True)
class Line:
    ref: str          # CFR-Magistrale, z. B. "M300"
    route_name: str   # Anzeigename (DE)
    tags: str         # kommaseparierte Themen-Tags
    length_km: int    # offizielle Streckenlänge (Wikipedia)
    stops: tuple[Stop, ...]

    @property
    def from_city(self) -> str:
        return self.stops[0].city

    @property
    def to_city(self) -> str:
        return self.stops[-1].city


# OSM-Namensabweichungen, die häufiger auftreten, als Alias gepflegt:
#   "Gara de Nord"  -> București Nord
#   "Gara Iași"     -> Iași
#   "Cluj Napoca"   -> Cluj-Napoca (OSM ohne Bindestrich)
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
# Pfade                                                                       #
# --------------------------------------------------------------------------- #
def find_repo_root() -> Path:
    """Repo-Wurzel = erstes Verzeichnis mit ``data/processed`` (vgl. CLI)."""
    for base in (Path.cwd(), *Path.cwd().parents,
                 Path(__file__).resolve().parent, *Path(__file__).resolve().parents):
        if (base / "data" / "processed").is_dir():
            return base
    raise SystemExit("data/processed nicht gefunden – bitte aus dem Repo ausführen.")


ROOT = find_repo_root()
RAW_PATH = ROOT / "data" / "raw" / "osm_ro_stations.json"
PROCESSED = ROOT / "data" / "processed"
STATIONS_OUT = PROCESSED / "rail_stations.geojson"
ROUTES_OUT = PROCESSED / "rail_route_options.geojson"
CONNECTIONS_OUT = PROCESSED / "sample_connections.csv"


# --------------------------------------------------------------------------- #
# Overpass-Abruf (defensiv)                                                   #
# --------------------------------------------------------------------------- #
def fetch_overpass() -> dict:
    """Fragt Overpass ab und liefert das geparste JSON.

    Wirft ``SystemExit`` mit klarer Meldung bei Netz-/Parse-Fehlern, statt
    eine kaputte Antwort weiterzureichen.
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
# Index + Auflösung                                                           #
# --------------------------------------------------------------------------- #
# Höherwertige railway-Typen gewinnen bei Namensgleichheit.
_RAILWAY_RANK = {"station": 0, "halt": 1, "stop": 2}


def build_index(data: dict) -> dict[str, tuple[float, float]]:
    """Name → (lon, lat). Bei Duplikaten gewinnt der höchstrangige Typ."""
    best: dict[str, tuple[int, float, float]] = {}
    for el in data["elements"]:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
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
# Ausgabe                                                                     #
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


def build_outputs(index: dict[str, tuple[float, float]]) -> None:
    station_ids: dict[str, str] = {}          # kanonischer Name -> ST-ID
    station_features: list[dict] = []
    route_features: list[dict] = []
    connection_rows: list[dict] = []
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
            connection_rows.append({
                "route_id": line.ref,
                "sequence": seq,
                "station": stop.name,
                "arrival_local": "",
                "departure_local": "",
                "trip_hint": hint,
            })

        route_features.append({
            "type": "Feature",
            "properties": {
                "route_id": line.ref,
                "route_name": line.route_name,
                "from_city": resolved[0][0].city,
                "to_city": resolved[-1][0].city,
                "tags": line.tags,
                "line_ref": line.ref,
                "length_km": line.length_km,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[lon, lat] for _, (lon, lat) in resolved],
            },
        })

    write_json(STATIONS_OUT, feature_collection("rail_stations", station_features))
    write_json(ROUTES_OUT, feature_collection("rail_route_options", route_features))

    with CONNECTIONS_OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["route_id", "sequence", "station",
                        "arrival_local", "departure_local", "trip_hint"],
        )
        writer.writeheader()
        writer.writerows(connection_rows)

    print(f"  → {STATIONS_OUT.relative_to(ROOT)} ({len(station_features)} Bahnhöfe)")
    print(f"  → {ROUTES_OUT.relative_to(ROOT)} ({len(route_features)} Magistralen)")
    print(f"  → {CONNECTIONS_OUT.relative_to(ROOT)} ({len(connection_rows)} Halte)")
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
    build_outputs(index)
    print("[fertig]  GeoJSON erneuern? → uv run reiseplan-cli build-gpkg")


if __name__ == "__main__":
    main()
