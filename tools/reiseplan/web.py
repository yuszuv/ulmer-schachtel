#!/usr/bin/env python3
"""Static site builder — presentation layer for GitHub Pages.

Generates ``site/index.html``: a self-contained Leaflet map with all routes,
stations, POIs, and info markers inlined as JSON.  Also copies the raw
GeoJSON/CSV files to ``site/data/`` for public download.

The HTML/CSS/JS template lives in ``template.html`` (same directory).
Python-side placeholders use ``.format()`` syntax: ``{data_js}``, ``{legend}``,
etc.  Literal CSS/JS braces in the template are escaped as ``{{`` / ``}}``.

Usage (via entrypoint):
    uv run reiseplan-site --out site
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

from .domain import Connection
from .repository import (
    INFO_PATH,
    POI_PATH,
    ROUTES_PATH,
    STATIONS_PATH,
    TimetableRepository,
    load_geojson,
    stops_for,
)
from .paths import PROCESSED

HERE = Path(__file__).resolve().parent

# Raw data files also copied to site/data/ for public download.
GEOJSON_SOURCES = [
    "poi_destinations.geojson",
    "rail_stations.geojson",
    "rail_lines.geojson",
    "info_markers.geojson",
    "route_stops.csv",
    "timetable.csv",
]

# POI categories → (German display label, colour, CSS shape class).
# Must match QGIS styles (AGENTS.md colour palette) and the JavaScript
# ``categoryMeta`` object embedded in the page.
CATEGORY_META: dict[str, tuple[str, str, str]] = {
    "dracula_city": ("Dracula-Städte", "#8b1a1a", "circle"),
    "city":         ("Städte",         "#9c7a3c", "square"),
    "danube_delta": ("Donaudelta",     "#1f6f6f", "triangle"),
}

ROUTE_COLOR   = "#6b4f2a"
STATION_COLOR = "#4c4c4c"
BG_COLOR      = "#f3ecd5"

INFOFER = "https://mersultrenurilor.infofer.ro"

# Habsburg military surveys (Arcanum) — (key, label, XYZ URL).
# Source: qgis/xyz_connections.xml.  © Arcanum Maps (mapire.eu).
ARCANUM_SURVEYS = [
    ("first",  "1. Militäraufnahme (1763–1787)",
     "https://tiles.arcanum.com/mercator/europe-18century-firstsurvey/{z}/{x}/{y}"),
    ("second", "2. Militäraufnahme (1806–1869)",
     "https://tiles.arcanum.com/mercator/europe-19century-secondsurvey/{z}/{x}/{y}"),
    ("third",  "3. Militäraufnahme (1869–1887)",
     "https://tiles.arcanum.com/mercator/europe-19century-thirdsurvey/{z}/{x}/{y}"),
]


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def collect() -> dict:
    """Read all GeoJSON / CSV and assemble the data object for render()."""
    routes = load_geojson(ROUTES_PATH)
    pois   = load_geojson(POI_PATH)
    stations = load_geojson(STATIONS_PATH)
    info   = load_geojson(INFO_PATH)

    timetable = TimetableRepository().load()
    overview = []
    for feature in routes["features"]:
        props = feature["properties"]
        overview.append({
            "props": props,
            "stops": stops_for(props["route_id"]),
            "timetable": timetable.get(props["route_id"]),  # Connection | None
        })

    return {
        "routes":   routes,
        "pois":     pois,
        "stations": stations,
        "info":     info,
        "overview": overview,
    }


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------

def _embed_json(obj: dict) -> str:
    """Serialize JSON safe for embedding inside a <script> tag."""
    text = json.dumps(obj, ensure_ascii=False)
    return text.replace("</", "<\\/")  # neutralise </script> sequences


def _render_connection(conn: Connection | None) -> str:
    """Render a compact connection line from a Connection value object."""
    if conn is None:
        return ""
    dep, arr, days = conn.dep_time, conn.arr_time, conn.days
    if not (dep or arr or days):
        return ""
    bits: list[str] = []
    if days: bits.append(html.escape(days))
    if dep:  bits.append(f"ab {html.escape(dep)}")
    if arr:  bits.append(f"an {html.escape(arr)}")
    if conn.duration: bits.append(f"({html.escape(conn.duration)})")
    line  = " · ".join(bits)
    train = (f' <span class="hint">{html.escape(conn.train)}</span>'
             if conn.train else "")
    notes = (f'<br><span class="hint">{html.escape(conn.notes)}</span>'
             if conn.notes else "")
    return f'<p class="conn">🚆 {line}{train}{notes}</p>'


def _render_overview(overview: list[dict], pois: dict) -> str:
    """Server-side HTML route and destination overview (no JS required)."""
    parts: list[str] = ["<h2>Routen im Überblick</h2>"]

    for entry in overview:
        p = entry["props"]
        tags = " ".join(
            f'<span class="tag">{html.escape(t)}</span>'
            for t in p.get("tags", "").split(",") if t
        )
        parts.append('<section class="route">')
        parts.append(f'<h3>{html.escape(p["route_name"])}</h3>')
        parts.append(
            f'<p class="meta">{html.escape(p["from_city"])} → '
            f'{html.escape(p["to_city"])}'
            f' · ca. {p.get("length_km", "?")} km</p>'
        )
        if tags:
            parts.append(f'<p class="tags">{tags}</p>')

        conn_html = _render_connection(entry.get("timetable"))
        if conn_html:
            parts.append(conn_html)

        if entry["stops"]:
            parts.append('<ol class="stops">')
            for row in entry["stops"]:
                parts.append(
                    f'<li><b>{html.escape(row["station"])}</b> '
                    f'<span class="hint">{html.escape(row["trip_hint"])}</span></li>'
                )
            parts.append("</ol>")
        else:
            parts.append('<p class="empty">(keine Verbindungsdaten)</p>')
        parts.append("</section>")

    parts.append(
        f'<p class="note">Fahrzeiten – soweit eingetragen – sind Richtwerte für '
        f'die einfachste Direktverbindung; verbindliche und aktuelle Zeiten unter '
        f'<a href="{INFOFER}">{INFOFER}</a>.</p>'
    )

    # Destinations grouped by category.
    parts.append("<h2>Reiseziele</h2>")
    by_cat: dict[str, list[dict]] = {}
    for feature in pois["features"]:
        by_cat.setdefault(feature["properties"]["category"], []).append(
            feature["properties"]
        )
    for cat, (label, color, _shape) in CATEGORY_META.items():
        items = by_cat.get(cat, [])
        if not items:
            continue
        parts.append(
            f'<h3><span class="swatch" style="background:{color}"></span>'
            f"{html.escape(label)}</h3>"
        )
        parts.append('<ul class="dests">')
        for props in items:
            notes = props.get("notes", "")
            parts.append(
                f'<li><b>{html.escape(props["name"])}</b>'
                + (f" – {html.escape(notes)}" if notes else "")
                + "</li>"
            )
        parts.append("</ul>")

    return "\n".join(parts)


def _render_legend() -> str:
    rows = [
        ('<span class="lg-line"></span>', "Routenkorridor"),
        (f'<span class="lg-dot" style="background:{STATION_COLOR}"></span>',
         "Bahnstation"),
    ]
    for _cat, (label, color, shape) in CATEGORY_META.items():
        rows.append((f'<span class="lg-{shape}" style="--c:{color}"></span>', label))
    rows.append(('<span class="lg-info">ℹ</span>', "Info zur Karte"))
    return "".join(
        f'<div class="lg-row">{sym}<span>{html.escape(text)}</span></div>'
        for sym, text in rows
    )


def _render_history() -> str:
    """SSR section for historical map overlays (readable without JavaScript)."""
    rows = "".join(
        f'<li><b>{html.escape(name)}</b> '
        f'<span class="hint">{html.escape(period)}'
        + (f" · {html.escape(extra)}" if extra else "")
        + "</span></li>"
        for name, period, extra in [
            ("1. Militäraufnahme", "1763–1787", "josephinisch"),
            ("2. Militäraufnahme", "1806–1869", "franziszeisch"),
            ("3. Militäraufnahme", "1869–1887", ""),
        ]
    )
    return (
        "<h2>Historische Karten</h2>"
        '<p>Über das Bedienfeld <em>„Historische Karte"</em> (oben rechts auf der '
        "Karte) lassen sich die <b>Habsburger Militäraufnahmen</b> stufenlos über die "
        "moderne Karte einblenden – die heutigen Orts- und Straßennamen bleiben "
        "darüber lesbar. So sieht man Siebenbürgen und das Banat vor der Moderne: "
        "alte Sachsenstädte, deutsch-ungarische Ortsnamen und die ersten Bahnlinien.</p>"
        f'<ul class="dests">{rows}</ul>'
        '<p class="note">Kartenwerk © Arcanum Maps (mapire.eu).</p>'
    )


# ---------------------------------------------------------------------------
# Main render + build
# ---------------------------------------------------------------------------

def render(data: dict) -> str:
    """Assemble the full HTML string from collected data."""
    payload = {
        "routes":       data["routes"],
        "pois":         data["pois"],
        "stations":     data["stations"],
        "info":         data["info"],
        "categoryMeta": {
            k: {"label": v[0], "color": v[1], "shape": v[2]}
            for k, v in CATEGORY_META.items()
        },
        "routeColor":   ROUTE_COLOR,
        "stationColor": STATION_COLOR,
    }
    template = (HERE / "template.html").read_text(encoding="utf-8")
    return template.format(
        bg=BG_COLOR,
        route_color=ROUTE_COLOR,
        station_color=STATION_COLOR,
        legend=_render_legend(),
        overview=_render_overview(data["overview"], data["pois"]),
        hist_blurb=_render_history(),
        hist_surveys=json.dumps(
            [{"key": k, "label": l, "url": u} for k, l, u in ARCANUM_SURVEYS],
            ensure_ascii=False,
        ),
        data_js=_embed_json(payload),
    )


def build(out_dir: Path) -> None:
    """Build the site into ``out_dir``: write index.html and copy raw data."""
    data = collect()
    out_dir.mkdir(parents=True, exist_ok=True)
    index = out_dir / "index.html"
    index.write_text(render(data), encoding="utf-8")

    data_out = out_dir / "data"
    data_out.mkdir(exist_ok=True)
    for name in GEOJSON_SOURCES:
        src = PROCESSED / name
        if src.is_file():
            shutil.copyfile(src, data_out / name)

    print(f"Seite gebaut: {index}")
    print(f"Rohdaten kopiert nach: {data_out}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="reiseplan-site",
        description="Baut die statische Reiseplaner-Webseite (GitHub Pages).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("site"),
        help="Zielverzeichnis (Default: ./site)",
    )
    args = parser.parse_args()
    build(args.out)


if __name__ == "__main__":
    main()
