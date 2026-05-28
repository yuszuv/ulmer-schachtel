#!/usr/bin/env python3
"""Kleine CLI fuer den Reiseplaner (Basic-Dateninspektion)."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
POI_PATH = DATA_DIR / "poi_destinations.geojson"
ROUTES_PATH = DATA_DIR / "rail_route_options.geojson"
CONNECTIONS_PATH = DATA_DIR / "sample_connections.csv"


def load_geojson(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_connections() -> list[dict]:
    with CONNECTIONS_PATH.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


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
    rows = [row for row in load_connections() if row["route_id"] == route_id]
    if not rows:
        print(f"Keine Verbindung mit route_id={route_id} gefunden.")
        return
    print(f"Route {route_id}")
    for row in sorted(rows, key=lambda r: int(r["sequence"])):
        print(
            f'  {row["sequence"]}. {row["station"]} '
            f'Ankunft: {row["arrival_local"] or "-"} '
            f'Abfahrt: {row["departure_local"] or "-"} '
            f'({row["trip_hint"]})'
        )


def list_categories() -> None:
    features = load_geojson(POI_PATH)["features"]
    values: Iterable[str] = sorted({f["properties"]["category"] for f in features})
    print("Verfuegbare Kategorien:")
    for value in values:
        print(f"  - {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reiseplan-cli",
        description="Basis-CLI fuer den Rumaenien-Reiseplaner",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-routes", help="Alle Routenoptionen anzeigen")
    sub.add_parser("list-categories", help="POI-Kategorien anzeigen")

    dest = sub.add_parser("list-destinations", help="Destinationen anzeigen")
    dest.add_argument("--category", help="Filter nach Kategorie")

    route = sub.add_parser("show-route", help="Stationen mit Zeiten fuer eine Route")
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
    if args.command == "list-destinations":
        list_destinations(args.category)
        return
    if args.command == "show-route":
        show_route(args.route_id)
        return
    parser.print_help()


if __name__ == "__main__":
    main()
