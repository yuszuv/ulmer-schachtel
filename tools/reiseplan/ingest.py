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
from .overpass import StationIndex, load_or_fetch
from .paths import ROOT
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


# ---------------------------------------------------------------------------
# Output builder
# ---------------------------------------------------------------------------

def _build_outputs(index: StationIndex) -> None:
    """Translate the station index + catalog into GeoJSON / CSV outputs.

    Steps:
    1. For each magistrală in MAIN_LINES, resolve stops via StationIndex.
    2. Assign stable station IDs (ST01, ST02, …) per canonical name.
    3. Merge timetable.csv connection fields into the LineString properties.
    4. Write rail_stations.geojson, rail_lines.geojson, route_stops.csv.
    """
    timetable = TimetableRepository().load()
    station_ids: dict[str, str] = {}          # canonical name → ST-ID
    station_features: list[dict] = []
    route_features: list[dict] = []
    stop_rows: list[dict] = []
    missing: list[str] = []

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
                **timetable_props,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [coord.as_list() for _, coord in resolved],
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
    _build_outputs(index)
    print("[fertig]  GPKG erneuern? → uv run reiseplan-cli build-gpkg")


if __name__ == "__main__":
    main()
