#!/usr/bin/env python3
"""Ulmer Schachtel – CLI für den Reiseplaner (Basic-Dateninspektion).

Jeder Daten-Befehl unterstützt ``--json`` für maschinenlesbare Ausgabe
(Pipes/jq); ohne Flag rendert er eine Rich-Tabelle. ``build-gpkg`` ist ein
Build-Schritt ohne JSON-Variante.
"""

from __future__ import annotations

import argparse
import csv
import functools
import json
import shutil
import subprocess
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from _paths import PROCESSED
from timetable import TIMETABLE_PATH, approx_fields, load_timetable


DATA_DIR = PROCESSED
POI_PATH = DATA_DIR / "poi_destinations.geojson"
ROUTES_PATH = DATA_DIR / "rail_lines.geojson"
ROUTE_STOPS_PATH = DATA_DIR / "route_stops.csv"
GPKG_PATH = DATA_DIR / "reiseplan.gpkg"

# Layername im GPKG -> Quell-GeoJSON. Reihenfolge = Reihenfolge der ogr2ogr-Aufrufe.
GPKG_LAYERS: list[tuple[str, str]] = [
    ("poi_destinations", "poi_destinations.geojson"),
    ("rail_stations", "rail_stations.geojson"),
    ("rail_lines", "rail_lines.geojson"),
    ("info_markers", "info_markers.geojson"),
]

# Eine gemeinsame Console – Breite wird von rich aus dem Terminal erkannt.
console = Console()


# --------------------------------------------------------------------------- #
# Laden                                                                       #
# --------------------------------------------------------------------------- #
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


def _routes() -> list[dict]:
    return [feature["properties"] for feature in load_geojson(ROUTES_PATH)["features"]]


def _emit_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


# --------------------------------------------------------------------------- #
# Befehle (je: bei --json strukturiert, sonst Rich-Tabelle)                   #
# --------------------------------------------------------------------------- #
def list_destinations(args: argparse.Namespace) -> None:
    rows: list[dict] = []
    for feature in load_geojson(POI_PATH)["features"]:
        props = feature["properties"]
        if args.category and props.get("category") != args.category:
            continue
        lon, lat = feature["geometry"]["coordinates"]
        rows.append({**props, "lon": lon, "lat": lat})

    if args.json:
        _emit_json(rows)
        return

    table = Table(title="Destinationen", box=box.ROUNDED, header_style="bold #b8860b")
    table.add_column("ID", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Kategorie")
    table.add_column("Prio", justify="center")
    table.add_column("Lat", justify="right", style="dim")
    table.add_column("Lon", justify="right", style="dim")
    for r in rows:
        table.add_row(
            str(r.get("id", "?")),
            str(r.get("name", "")),
            str(r.get("category", "")),
            str(r.get("priority", "")),
            f'{r["lat"]:.4f}',
            f'{r["lon"]:.4f}',
        )
    console.print(table)


def list_routes(args: argparse.Namespace) -> None:
    routes = _routes()
    if args.json:
        _emit_json(routes)
        return

    table = Table(title="CFR-Magistralen", box=box.ROUNDED, header_style="bold #b8860b")
    table.add_column("Linie", style="bold", no_wrap=True)
    table.add_column("Strecke", no_wrap=True)
    table.add_column("Tags", style="dim", overflow="fold")
    for p in routes:
        table.add_row(
            p.get("route_id", "?"),
            f'{p.get("from_city", "?")} → {p.get("to_city", "?")}',
            p.get("tags", ""),
        )
    console.print(table)


def show_route(args: argparse.Namespace) -> None:
    rows = stops_for(args.route_id)
    if not rows:
        valid = ", ".join(sorted(_stops_index()))
        raise SystemExit(
            f"Keine Route mit route_id={args.route_id} gefunden. Bekannt: {valid}"
        )

    if args.json:
        _emit_json({"route_id": args.route_id, "stops": rows})
        return

    table = Table(title=f"Route {args.route_id}", box=box.ROUNDED,
                  header_style="bold #b8860b")
    table.add_column("#", justify="right", no_wrap=True)
    table.add_column("Station", style="bold")
    table.add_column("Rolle", style="dim")
    for row in rows:
        table.add_row(str(row["sequence"]), row["station"], row["trip_hint"])
    console.print(table)


def overview(args: argparse.Namespace) -> None:
    """Kompakte Gesamtübersicht: alle Magistralen mit ihrer Haltefolge."""
    routes = _routes()
    if args.json:
        _emit_json([{**p, "stops": stops_for(p.get("route_id", ""))} for p in routes])
        return

    for p in routes:
        rid = p.get("route_id", "?")
        console.print(
            f'\n[bold #b8860b]{rid}[/bold #b8860b]  {p.get("route_name", "")}  '
            f'[dim]({p.get("from_city", "?")} → {p.get("to_city", "?")} · '
            f'{p.get("tags", "")})[/dim]'
        )
        rows = stops_for(rid)
        if not rows:
            console.print("  [dim](keine Haltedaten)[/dim]")
            continue
        for row in rows:
            console.print(
                f'  {row["sequence"]}. [bold]{row["station"]}[/bold] '
                f'– [dim]{row["trip_hint"]}[/dim]'
            )


def timetable(args: argparse.Namespace) -> None:
    """Verbindungsübersicht aus timetable.csv."""
    data = load_timetable()
    if not data:
        raise SystemExit(f"Keine timetable.csv unter {TIMETABLE_PATH} gefunden.")

    if args.json:
        _emit_json([data[route_id] for route_id in sorted(data)])
        return

    t = Table(
        title="🚂  CFR-Verbindungsübersicht  (M200 – M900)",
        box=box.ROUNDED,
        header_style="bold #b8860b",
        title_style="bold",
        show_lines=False,
        padding=(0, 1),
    )
    t.add_column("Linie", style="bold", no_wrap=True)
    t.add_column("Strecke", no_wrap=True)
    t.add_column("Tage", justify="center", no_wrap=True)
    t.add_column("Abf.", justify="right", style="#5f8700", no_wrap=True)
    t.add_column("Ank.", justify="right", style="#5f8700", no_wrap=True)
    t.add_column("Dauer", justify="right", no_wrap=True)
    t.add_column("Zug", style="#005f87", no_wrap=True)
    t.add_column("Zwischenstopps", min_width=25, overflow="fold")

    dash = "–"
    note_lines: list[str] = []

    for route_id in sorted(data):
        r = data[route_id]
        notes = r.get("notes") or ""
        approx = approx_fields(r)   # Teilmenge von {dep, arr} – pro Feld, nicht pauschal

        route_cell = Text(route_id)
        if approx:
            route_cell.stylize("dim")

        strecke = f'{r.get("from_city", "?")} → {r.get("to_city", "?")}'
        dep = r.get("dep_time") or dash
        arr = r.get("arr_time") or dash
        dur = r.get("duration") or dash
        train = r.get("train") or dash
        via = r.get("via") or dash
        days = r.get("days") or dash

        if "dep" in approx and dep != dash:
            dep = f"~{dep}"
        if "arr" in approx and arr != dash:
            arr = f"~{arr}"

        t.add_row(route_cell, strecke, days, dep, arr, dur, train, via)

        if notes:
            note_lines.append(f"  [dim]{route_id}[/dim]  {notes}")

    console.print()
    console.print(t)
    if note_lines:
        console.print()
        console.print("[dim]Hinweise:[/dim]")
        for line in note_lines:
            console.print(line)
    console.print(
        "\n[dim]Zeiten nach infofer.ro (Stand: Mai 2026) · ~ = Richtwert · "
        "Verbindlich: [link=https://mersultrenurilor.infofer.ro]mersultrenurilor.infofer.ro[/link][/dim]"
    )


def list_categories(args: argparse.Namespace) -> None:
    cats = sorted({
        feature["properties"].get("category")
        for feature in load_geojson(POI_PATH)["features"]
        if feature["properties"].get("category")
    })
    if args.json:
        _emit_json(cats)
        return

    console.print("[bold]Verfügbare Kategorien:[/bold]")
    for value in cats:
        console.print(f"  • {value}")


def build_gpkg(args: argparse.Namespace) -> None:
    """Baut aus den GeoJSON-Quellen ein konsolidiertes ``reiseplan.gpkg``.

    Die GeoJSON bleiben versionierte Quelle (EPSG:4326, GeoJSON-Spec); die GPKG
    ist ein generiertes, gitignoriertes Bündel für QGIS/QField (ein File, mehrere
    Layer) und wird dabei ins Projekt-CRS EPSG:3844 reprojiziert.
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


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reiseplan-cli",
        description="Basis-CLI für den Rumänien-Reiseplaner",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Eltern-Parser: --json für alle Daten-Befehle (nicht für den Build-Schritt).
    jsonp = argparse.ArgumentParser(add_help=False)
    jsonp.add_argument("--json", action="store_true",
                       help="Maschinenlesbare JSON-Ausgabe (für Pipes/jq)")

    sub.add_parser("list-routes", parents=[jsonp],
                   help="Alle Magistralen anzeigen").set_defaults(func=list_routes)
    sub.add_parser("list-categories", parents=[jsonp],
                   help="POI-Kategorien anzeigen").set_defaults(func=list_categories)
    sub.add_parser("overview", parents=[jsonp],
                   help="Alle Magistralen inkl. Haltefolge kompakt").set_defaults(func=overview)
    sub.add_parser("timetable", parents=[jsonp],
                   help="Verbindungen (Abfahrt/Ankunft/via) je Magistrale").set_defaults(func=timetable)
    sub.add_parser("build-gpkg",
                   help="GeoJSON zu einer reiseplan.gpkg bündeln").set_defaults(func=build_gpkg)

    dest = sub.add_parser("list-destinations", parents=[jsonp], help="Destinationen anzeigen")
    dest.add_argument("--category", help="Filter nach Kategorie")
    dest.set_defaults(func=list_destinations)

    route = sub.add_parser("show-route", parents=[jsonp], help="Haltefolge einer Magistrale")
    route.add_argument("route_id", help="z. B. M300")
    route.set_defaults(func=show_route)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
