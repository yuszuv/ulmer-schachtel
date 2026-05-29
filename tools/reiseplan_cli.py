#!/usr/bin/env python3
"""Ulmer Schachtel – CLI für den Reiseplaner (Basic-Dateninspektion)."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


def find_data_dir() -> Path:
    """Sucht ``data/processed`` ausgehend vom CWD bzw. vom Skript-Ort.

    So funktioniert die CLI sowohl per ``uv run python tools/reiseplan_cli.py``
    als auch per installiertem Entrypoint ``uv run reiseplan-cli`` (dann liegt
    ``__file__`` im venv, nicht im Repo).
    """
    candidates = [
        Path.cwd(),
        *Path.cwd().parents,
        Path(__file__).resolve().parent,
        *Path(__file__).resolve().parents,
    ]
    for base in candidates:
        processed = base / "data" / "processed"
        if processed.is_dir():
            return processed
    raise SystemExit(
        "data/processed nicht gefunden – bitte aus dem Repo-Wurzelverzeichnis ausführen."
    )


DATA_DIR = find_data_dir()
POI_PATH = DATA_DIR / "poi_destinations.geojson"
ROUTES_PATH = DATA_DIR / "rail_route_options.geojson"
CONNECTIONS_PATH = DATA_DIR / "sample_connections.csv"
GPKG_PATH = DATA_DIR / "reiseplan.gpkg"

# Layername im GPKG -> Quell-GeoJSON. Reihenfolge = Reihenfolge der ogr2ogr-Aufrufe.
GPKG_LAYERS: list[tuple[str, str]] = [
    ("poi_destinations", "poi_destinations.geojson"),
    ("rail_stations", "rail_stations.geojson"),
    ("rail_route_options", "rail_route_options.geojson"),
    ("info_markers", "info_markers.geojson"),
]


def load_geojson(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_connections() -> list[dict]:
    with CONNECTIONS_PATH.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def connections_for(route_id: str) -> list[dict]:
    rows = [row for row in load_connections() if row["route_id"] == route_id]
    return sorted(rows, key=lambda r: int(r["sequence"]))


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
    rows = connections_for(route_id)
    if not rows:
        print(f"Keine Verbindung mit route_id={route_id} gefunden.")
        return
    print(f"Route {route_id}")
    for row in rows:
        print(
            f'  {row["sequence"]}. {row["station"]} '
            f'Ankunft: {row["arrival_local"] or "-"} '
            f'Abfahrt: {row["departure_local"] or "-"} '
            f'({row["trip_hint"]})'
        )


def overview() -> None:
    """Kompakte Gesamtübersicht: alle Routen mit ihren Halten und Zeiten."""
    features = load_geojson(ROUTES_PATH)["features"]
    for feature in features:
        props = feature["properties"]
        print(
            f'\n{props["route_id"]}: {props["route_name"]} '
            f'({props["from_city"]} -> {props["to_city"]}) | tags={props["tags"]}'
        )
        rows = connections_for(props["route_id"])
        if not rows:
            print("  (keine Verbindungsdaten)")
            continue
        for row in rows:
            print(
                f'  {row["sequence"]}. {row["station"]:<16} '
                f'an {row["arrival_local"] or "  -  "}  '
                f'ab {row["departure_local"] or "  -  "}  '
                f'– {row["trip_hint"]}'
            )


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

    sub.add_parser("list-routes", help="Alle Routenoptionen anzeigen")
    sub.add_parser("list-categories", help="POI-Kategorien anzeigen")
    sub.add_parser("overview", help="Alle Routen inkl. An-/Abfahrten kompakt")
    sub.add_parser("build-gpkg", help="GeoJSON zu einer reiseplan.gpkg bündeln")

    dest = sub.add_parser("list-destinations", help="Destinationen anzeigen")
    dest.add_argument("--category", help="Filter nach Kategorie")

    route = sub.add_parser("show-route", help="Stationen mit Zeiten für eine Route")
    route.add_argument("route_id", help="z. B. R1")
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
