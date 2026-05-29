#!/usr/bin/env python3
"""Ulmer Schachtel – CLI für den Reiseplaner (Basic-Dateninspektion)."""

from __future__ import annotations

import argparse
import csv
import functools
import json
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

from _paths import PROCESSED


DATA_DIR = PROCESSED
POI_PATH = DATA_DIR / "poi_destinations.geojson"
ROUTES_PATH = DATA_DIR / "rail_lines.geojson"
ROUTE_STOPS_PATH = DATA_DIR / "route_stops.csv"
TIMETABLE_PATH = DATA_DIR / "timetable.csv"
GPKG_PATH = DATA_DIR / "reiseplan.gpkg"

# Layername im GPKG -> Quell-GeoJSON. Reihenfolge = Reihenfolge der ogr2ogr-Aufrufe.
GPKG_LAYERS: list[tuple[str, str]] = [
    ("poi_destinations", "poi_destinations.geojson"),
    ("rail_stations", "rail_stations.geojson"),
    ("rail_lines", "rail_lines.geojson"),
    ("info_markers", "info_markers.geojson"),
]


def load_geojson(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@functools.lru_cache(maxsize=1)
def _stops_index() -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    with ROUTE_STOPS_PATH.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            index.setdefault(row["route_id"], []).append(row)
    for rows in index.values():
        rows.sort(key=lambda r: int(r["sequence"]))
    return index


def load_route_stops() -> list[dict]:
    return [row for rows in _stops_index().values() for row in rows]


def stops_for(route_id: str) -> list[dict]:
    return _stops_index().get(route_id, [])


def load_timetable() -> dict[str, dict]:
    """``route_id`` → Verbindungszeile aus timetable.csv (leer, wenn Datei fehlt)."""
    if not TIMETABLE_PATH.is_file():
        return {}
    with TIMETABLE_PATH.open("r", encoding="utf-8") as f:
        return {row["route_id"]: row for row in csv.DictReader(f)}


def list_destinations(category: str | None) -> None:
    features = load_geojson(POI_PATH)["features"]
    for feature in features:
        props = feature["properties"]
        if category and props["category"] != category:
            continue
        lon, lat = feature["geometry"]["coordinates"]
        print(
            f'{props["id"]}: {props["name"]} '
            f'[{props["category"]}, {props["priority"]}] @ {lat:.4f}, {lon:.4f}'
        )


def list_routes() -> None:
    features = load_geojson(ROUTES_PATH)["features"]
    for feature in features:
        props = feature["properties"]
        print(
            f'{props["route_id"]}: {props["route_name"]} '
            f'({props["from_city"]} -> {props["to_city"]}) | tags={props["tags"]}'
        )


def show_route(route_id: str) -> None:
    rows = stops_for(route_id)
    if not rows:
        print(f"Keine Route mit route_id={route_id} gefunden.")
        return
    print(f"Route {route_id}")
    for row in rows:
        print(f'  {row["sequence"]}. {row["station"]} ({row["trip_hint"]})')


def overview() -> None:
    """Kompakte Gesamtübersicht: alle Magistralen mit ihrer Haltefolge."""
    features = load_geojson(ROUTES_PATH)["features"]
    for feature in features:
        props = feature["properties"]
        print(
            f'\n{props["route_id"]}: {props["route_name"]} '
            f'({props["from_city"]} -> {props["to_city"]}) | tags={props["tags"]}'
        )
        rows = stops_for(props["route_id"])
        if not rows:
            print("  (keine Haltedaten)")
            continue
        for row in rows:
            print(f'  {row["sequence"]}. {row["station"]:<22} – {row["trip_hint"]}')


def timetable() -> None:
    """Verbindungsübersicht aus timetable.csv (eine Zeile je Magistrale)."""
    table = load_timetable()
    if not table:
        print(f"Keine timetable.csv unter {TIMETABLE_PATH} gefunden.")
        return
    dash = "–"
    for route_id in sorted(table):
        r = table[route_id]
        dep, arr = r.get("dep_time") or dash, r.get("arr_time") or dash
        dur = f' ({r["duration"]})' if r.get("duration") else ""
        train = f' [{r["train"]}]' if r.get("train") else ""
        via = f' via {r["via"]}' if r.get("via") else ""
        print(
            f'{route_id}  {r.get("from_city", "?")} → {r.get("to_city", "?")}'
            f'  | {r.get("days") or dash} ab {dep} an {arr}{dur}{via}{train}'
        )
        if r.get("notes"):
            print(f'        ↳ {r["notes"]}')


def list_categories() -> None:
    features = load_geojson(POI_PATH)["features"]
    values: Iterable[str] = sorted({f["properties"]["category"] for f in features})
    print("Verfügbare Kategorien:")
    for value in values:
        print(f"  - {value}")


def build_gpkg() -> None:
    """Baut aus den GeoJSON-Quellen ein konsolidiertes ``reiseplan.gpkg``.

    Die GeoJSON bleiben versionierte Quelle; die GPKG ist ein generiertes,
    gitignoriertes Bündel für QGIS/QField (ein File, drei Layer).
    """
    if shutil.which("ogr2ogr") is None:
        raise SystemExit(
            "ogr2ogr nicht gefunden – bitte GDAL installieren "
            "(Arch: 'pacman -S gdal')."
        )

    # Vorhandene GPKG entfernen → idempotenter, sauberer Neubau.
    GPKG_PATH.unlink(missing_ok=True)

    for index, (layer_name, source_file) in enumerate(GPKG_LAYERS):
        source = DATA_DIR / source_file
        if not source.is_file():
            raise SystemExit(f"Quelle fehlt: {source}")
        # Erster Aufruf legt die GPKG an, weitere ergänzen Layer via -update.
        update_flags = [] if index == 0 else ["-update"]
        # GeoJSON liegt per Standard in EPSG:4326 vor; in EPSG:3844 (Stereo70)
        # reprojizieren, damit das Projekt-CRS beim QGIS-Import nicht umspringt.
        subprocess.run(
            ["ogr2ogr", "-f", "GPKG", *update_flags,
             "-t_srs", "EPSG:3844",
             str(GPKG_PATH), str(source), "-nln", layer_name],
            check=True,
        )

    print(f"GPKG gebaut: {GPKG_PATH}")
    for layer_name, _ in GPKG_LAYERS:
        print(f"  - {layer_name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reiseplan-cli",
        description="Basis-CLI für den Rumänien-Reiseplaner",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-routes", help="Alle Magistralen anzeigen")
    sub.add_parser("list-categories", help="POI-Kategorien anzeigen")
    sub.add_parser("overview", help="Alle Magistralen inkl. Haltefolge kompakt")
    sub.add_parser("timetable", help="Verbindungen (Abfahrt/Ankunft/via) je Magistrale")
    sub.add_parser("build-gpkg", help="GeoJSON zu einer reiseplan.gpkg bündeln")

    dest = sub.add_parser("list-destinations", help="Destinationen anzeigen")
    dest.add_argument("--category", help="Filter nach Kategorie")

    route = sub.add_parser("show-route", help="Haltefolge einer Magistrale")
    route.add_argument("route_id", help="z. B. M300")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "list-routes":
        list_routes()
        return
    if args.command == "list-categories":
        list_categories()
        return
    if args.command == "overview":
        overview()
        return
    if args.command == "timetable":
        timetable()
        return
    if args.command == "build-gpkg":
        build_gpkg()
        return
    if args.command == "list-destinations":
        list_destinations(args.category)
        return
    if args.command == "show-route":
        show_route(args.route_id)
        return
    parser.print_help()


if __name__ == "__main__":
    main()
