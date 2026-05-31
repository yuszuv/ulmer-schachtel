#!/usr/bin/env python3
"""CFR data ingest use-case — orchestrates OSM fetch → GeoJSON/CSV output.

Data sources
------------
* Geometry:   OpenStreetMap via Overpass API.
              © OpenStreetMap contributors, ODbL 1.0.
              Attribution required when redistributing derived data.
* Definitions: CFR magistrale 200–900 from catalog.py (hand-curated).

CRS
---
Output is deliberately EPSG:4326 — RFC 7946 mandates WGS84 for GeoJSON and
web consumers (Leaflet, GitHub preview) assume lon/lat.
Reprojection to EPSG:3844 (Stereo70) happens later: ``reiseplan-cli build-gpkg``
runs ``ogr2ogr -t_srs EPSG:3844``.  Do not "fix" the GeoJSON to 3844.

Output files (EPSG:4326)
------------------------
  data/processed/rail_stations.geojson   stations (Point)
  data/processed/rail_lines.geojson      magistralen (LineString) + timetable attrs
  data/processed/route_stops.csv         stop sequences per magistrală
  data/raw/osm_ro_stations.json          raw Overpass cache

Usage
-----
  uv run reiseplan-fetch            # query Overpass, cache, build
  uv run reiseplan-fetch --offline  # rebuild from cache (no network)

After editing timetable.csv re-run with --offline to merge the new times into
rail_lines.geojson.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .catalog import MAIN_LINES
from .domain import TIMETABLE_FIELDS, Coordinate, Magistrale, Stop
from .overpass import StationIndex, load_or_fetch, load_or_fetch_rail
from .paths import ROOT
from .routing import RailNetwork
from .repository import (
    ROUTE_STOPS_PATH,
    STATIONS_PATH,
    TimetableRepository,
    feature_collection,
    write_json,
)

# Avoid circular import — LINES_OUT is defined here because it is an output
# of this use-case (other modules read it via repository.ROUTES_PATH).
LINES_OUT = ROOT / "data" / "processed" / "rail_lines.geojson"

# Padding (degrees) around a magistrală's stations → the Overpass corridor bbox
# from which its rail-track geometry is fetched.
_CORRIDOR_BUFFER_DEG = 0.25


# ---------------------------------------------------------------------------
# Output builder
# ---------------------------------------------------------------------------

def _corridors(
    index: StationIndex, magistrales: tuple[Magistrale, ...]
) -> dict[str, tuple[float, float, float, float]]:
    """Bounding box (south, west, north, east) per magistrală from its stations.

    Buffered by _CORRIDOR_BUFFER_DEG so the rail-ways query around the straight
    station chain also captures the real (curving) alignment between them.
    """
    out: dict[str, tuple[float, float, float, float]] = {}
    for mag in magistrales:
        coords = [index.resolve(s).unwrap() for s in mag.stops if index.resolve(s).is_some]
        if len(coords) < 2:
            continue
        lons = [c.lon for c in coords]
        lats = [c.lat for c in coords]
        b = _CORRIDOR_BUFFER_DEG
        out[mag.ref] = (min(lats) - b, min(lons) - b, max(lats) + b, max(lons) + b)
    return out


def _build_outputs(index: StationIndex, rail_data: dict[str, dict]) -> None:
    """Translate the station index + catalog into GeoJSON / CSV outputs.

    Steps:
    1. For each magistrală in MAIN_LINES, resolve stops via StationIndex.
    2. Assign stable station IDs (ST01, ST02, …) per canonical name.
    3. Route the stop sequence along the real OSM tracks (``RailNetwork`` built
       from ``rail_data[ref]``) → the LineString geometry; tag ``geom_source``.
    4. Merge timetable.csv connection fields into the LineString properties.
    5. Write rail_stations.geojson, rail_lines.geojson, route_stops.csv.
    """
    timetable = TimetableRepository().load()
    station_ids: dict[str, str] = {}          # canonical name → ST-ID
    station_features: list[dict] = []
    route_features: list[dict] = []
    stop_rows: list[dict] = []
    missing: list[str] = []
    straight_fallback: list[str] = []          # magistralen with a routing gap

    def _station_id(stop: Stop, coord: Coordinate) -> str:
        if stop.name not in station_ids:
            sid = f"ST{len(station_ids) + 1:02d}"
            station_ids[stop.name] = sid
            station_features.append({
                "type": "Feature",
                "properties": {
                    "station_id": sid,
                    "name": stop.name,
                    "city": stop.city,
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": coord.as_list(),
                },
            })
        return station_ids[stop.name]

    for mag in MAIN_LINES:
        resolved: list[tuple[Stop, Coordinate]] = []
        for stop in mag.stops:
            maybe_coord = index.resolve(stop)
            if not maybe_coord.is_some:
                missing.append(f"{mag.ref}: {stop.name}")
                continue
            resolved.append((stop, maybe_coord.unwrap()))

        if len(resolved) < 2:
            print(f"  ! {mag.ref}: zu wenige auflösbare Halte – übersprungen.")
            continue

        for seq, (stop, coord) in enumerate(resolved, start=1):
            _station_id(stop, coord)
            if seq == 1:
                hint = f"Start ({stop.city})"
            elif seq == len(resolved):
                hint = f"Ziel ({stop.city})"
            else:
                hint = f"Halt / Umstieg ({stop.city})"
            stop_rows.append({
                "route_id": mag.ref,
                "sequence": seq,
                "station": stop.name,
                "city": stop.city,
                "trip_hint": hint,
            })

        # Route the stop sequence along the real OSM tracks (falls back to a
        # straight line per leg only where the rail graph has a gap).
        network = RailNetwork.from_overpass(rail_data.get(mag.ref, {}))
        line_coords, routed = network.route_stops([coord for _, coord in resolved])
        if not routed:
            straight_fallback.append(mag.ref)

        # Merge hand-maintained connection data (1:1 per magistrală via route_id).
        conn = timetable.get(mag.ref)
        timetable_props = conn.geojson_fields() if conn else {f: "" for f in TIMETABLE_FIELDS}

        route_features.append({
            "type": "Feature",
            "properties": {
                "route_id": mag.ref,
                "route_name": mag.route_name,
                "from_city": resolved[0][0].city,
                "to_city": resolved[-1][0].city,
                "tags": mag.tags,
                "line_ref": mag.ref,
                "length_km": mag.length_km,
                "geom_source": "osm-routed" if routed else "fallback-straight",
                **timetable_props,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [c.as_list() for c in line_coords],
            },
        })

    write_json(STATIONS_OUT := ROOT / "data" / "processed" / "rail_stations.geojson",
               feature_collection("rail_stations", station_features))
    write_json(LINES_OUT,
               feature_collection("rail_lines", route_features))

    with ROUTE_STOPS_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["route_id", "sequence", "station", "city", "trip_hint"]
        )
        writer.writeheader()
        writer.writerows(stop_rows)

    print(f"  → {STATIONS_OUT.relative_to(ROOT)} ({len(station_features)} Bahnhöfe)")
    print(f"  → {LINES_OUT.relative_to(ROOT)} ({len(route_features)} Magistralen)")
    print(f"  → {ROUTE_STOPS_PATH.relative_to(ROOT)} ({len(stop_rows)} Halte)")
    if missing:
        print("  ! nicht aufgelöst (in Geometrie ausgelassen):")
        for item in missing:
            print(f"      - {item}")
    if straight_fallback:
        print("  ! Gleis-Routing-Lücke – Luftlinie als Fallback für: "
              + ", ".join(straight_fallback))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Nur aus data/raw/osm_ro_stations.json neu bauen (kein Netz).",
    )
    args = parser.parse_args()

    # unwrap_or_exit() translates Err → SystemExit at the application boundary.
    data = load_or_fetch(args.offline).unwrap_or_exit()
    index = StationIndex.from_overpass(data)
    print(f"[index]   {len(index)} eindeutige Halte-Namen indiziert.")

    # scaffold() is a no-op when timetable.csv already exists.
    TimetableRepository().scaffold(MAIN_LINES)

    # Fetch real track geometry per corridor (bbox from the resolved stations),
    # then build the routed line geometry. --offline rebuilds from the cache.
    corridors = _corridors(index, MAIN_LINES)
    rail_data = load_or_fetch_rail(args.offline, corridors).unwrap_or_exit()

    _build_outputs(index, rail_data)
    print("[fertig]  GPKG erneuern? → uv run reiseplan-cli build-gpkg")


if __name__ == "__main__":
    main()
