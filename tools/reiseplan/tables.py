"""Rich terminal rendering — presentation layer for the CLI.

One function per CLI command; each receives the parsed argparse Namespace and
prints either a Rich table (default) or JSON (``--json`` flag).

All imports from the domain / repository layer are explicit so that this module
stays in the presentation tier and never mixes IO with rendering logic.
"""

from __future__ import annotations

import json

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .domain import Connection
from .repository import (
    POI_PATH,
    ROUTES_PATH,
    TimetableRepository,
    load_geojson,
    routes,
    stops_for,
)
from .repository import ROUTE_STOPS_PATH as _STOPS_PATH  # only for SystemExit msg

console = Console()

_DASH = "–"


def _emit_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Individual command renderers
# ---------------------------------------------------------------------------

def list_destinations(args) -> None:
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


def list_routes(args) -> None:
    route_list = routes()
    if args.json:
        _emit_json(route_list)
        return

    table = Table(title="CFR-Magistralen", box=box.ROUNDED, header_style="bold #b8860b")
    table.add_column("Linie", style="bold", no_wrap=True)
    table.add_column("Strecke", no_wrap=True)
    table.add_column("Tags", style="dim", overflow="fold")
    for p in route_list:
        table.add_row(
            p.get("route_id", "?"),
            f'{p.get("from_city", "?")} → {p.get("to_city", "?")}',
            p.get("tags", ""),
        )
    console.print(table)


def show_route(args) -> None:
    rows = stops_for(args.route_id)
    if not rows:
        from .repository import _stops_index  # access cached index for error msg
        valid = ", ".join(sorted(_stops_index()))
        raise SystemExit(
            f"Keine Route mit route_id={args.route_id} gefunden. Bekannt: {valid}"
        )

    if args.json:
        _emit_json({"route_id": args.route_id, "stops": rows})
        return

    table = Table(
        title=f"Route {args.route_id}", box=box.ROUNDED, header_style="bold #b8860b"
    )
    table.add_column("#", justify="right", no_wrap=True)
    table.add_column("Station", style="bold")
    table.add_column("Rolle", style="dim")
    for row in rows:
        table.add_row(str(row["sequence"]), row["station"], row["trip_hint"])
    console.print(table)


def overview(args) -> None:
    """Compact overview: all magistralen with their stop sequences."""
    route_list = routes()
    if args.json:
        _emit_json([{**p, "stops": stops_for(p.get("route_id", ""))} for p in route_list])
        return

    for p in route_list:
        rid = p.get("route_id", "?")
        console.print(
            f'\n[bold #b8860b]{rid}[/bold #b8860b]  {p.get("route_name", "")}  '
            f'[dim]({p.get("from_city", "?")} → {p.get("to_city", "?")} · '
            f'{p.get("tags", "")})[/dim]'
        )
        stop_rows = stops_for(rid)
        if not stop_rows:
            console.print("  [dim](keine Haltedaten)[/dim]")
            continue
        for row in stop_rows:
            console.print(
                f'  {row["sequence"]}. [bold]{row["station"]}[/bold] '
                f'– [dim]{row["trip_hint"]}[/dim]'
            )


def timetable(args) -> None:
    """Connection overview from the hand-maintained timetable.csv."""
    data = TimetableRepository().load()
    if not data:
        from .repository import TIMETABLE_PATH
        raise SystemExit(f"Keine timetable.csv unter {TIMETABLE_PATH} gefunden.")

    if args.json:
        _emit_json([data.get(rid).as_dict() for rid in sorted(data)])
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

    note_lines: list[str] = []

    for route_id in sorted(data):
        conn: Connection = data.get(route_id)  # type: ignore[assignment]
        approx = conn.approximate

        route_cell = Text(route_id)
        if approx:
            route_cell.stylize("dim")

        strecke = f"{conn.from_city} → {conn.to_city}"
        dep = conn.dep_time or _DASH
        arr = conn.arr_time or _DASH
        dur = conn.duration or _DASH
        train = conn.train or _DASH
        via = conn.via or _DASH
        days = conn.days or _DASH

        if "dep" in approx and dep != _DASH:
            dep = f"~{dep}"
        if "arr" in approx and arr != _DASH:
            arr = f"~{arr}"

        t.add_row(route_cell, strecke, days, dep, arr, dur, train, via)

        if conn.notes:
            note_lines.append(f"  [dim]{route_id}[/dim]  {conn.notes}")

    console.print()
    console.print(t)
    if note_lines:
        console.print()
        console.print("[dim]Hinweise:[/dim]")
        for line in note_lines:
            console.print(line)
    console.print(
        "\n[dim]Zeiten nach infofer.ro (Stand: Mai 2026) · ~ = Richtwert · "
        "Verbindlich: [link=https://mersultrenurilor.infofer.ro]"
        "mersultrenurilor.infofer.ro[/link][/dim]"
    )


def list_categories(args) -> None:
    cats = sorted({
        f["properties"].get("category")
        for f in load_geojson(POI_PATH)["features"]
        if f["properties"].get("category")
    })
    if args.json:
        _emit_json(cats)
        return

    console.print("[bold]Verfügbare Kategorien:[/bold]")
    for value in cats:
        console.print(f"  • {value}")
