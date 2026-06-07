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
import re
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
from .paths import PROCESSED, ROOT

HERE = Path(__file__).resolve().parent

# Vendored design system (populated by `reiseplan-vendor-design`).
VENDOR_DIR  = ROOT / "vendor" / "muris-atlas"
TOKENS_CSS  = VENDOR_DIR / "colors_and_type.css"
VENDOR_FONTS = VENDOR_DIR / "fonts"


def load_tokens() -> dict[str, str]:
    """Parse CSS custom properties from the vendored design token file.

    Reads ``vendor/muris-atlas/colors_and_type.css`` and returns a mapping of
    ``{property-name: value}`` where property-name omits the leading ``--``.
    One level of ``var(--x)`` aliases is resolved so callers receive concrete
    values without needing to chase references.

    Raises ``SystemExit`` with a human-readable message when the vendor
    directory is missing (i.e. ``reiseplan-vendor-design`` has never been run).
    """
    if not TOKENS_CSS.is_file():
        raise SystemExit(
            "vendor/muris-atlas/colors_and_type.css fehlt.\n"
            "Bitte zuerst ausführen: uv run reiseplan-vendor-design"
        )
    text = TOKENS_CSS.read_text(encoding="utf-8")
    # Extract all  --name: value;  declarations (value may contain spaces).
    raw: dict[str, str] = {}
    for m in re.finditer(r"--([a-zA-Z0-9-]+)\s*:\s*([^;]+?)\s*;", text):
        raw[m.group(1)] = m.group(2).strip()

    # Resolve one level of var(--x) aliases.
    tokens: dict[str, str] = {}
    _var = re.compile(r"^var\(--([a-zA-Z0-9-]+)\)$")
    for name, value in raw.items():
        m = _var.match(value)
        tokens[name] = raw.get(m.group(1), value) if m else value
    return tokens


# Raw data files also copied to site/data/ for public download.
GEOJSON_SOURCES = [
    "poi_destinations.geojson",
    "rail_stations.geojson",
    "rail_lines.geojson",
    "info_markers.geojson",
    "route_stops.csv",
    "timetable.csv",
]

# POI categories → (German display label, CSS shape class).
# Colours are resolved at render time from the vendored design tokens so they
# always match the upstream design system (no hex literals duplicated here).
# Token name → CSS custom-property: dracula_city=--hansa-rot-hi, city=--ink,
# danube_delta=--ink-soft.  QGIS alignment is a separate pass.
CATEGORY_META: dict[str, tuple[str, str]] = {
    "dracula_city": ("Dracula-Städte", "circle"),
    "city":         ("Städte",         "square"),
    "danube_delta": ("Donaudelta",     "triangle"),
}
CATEGORY_TOKEN: dict[str, str] = {
    "dracula_city": "hansa-rot-hi",
    "city":         "ink",
    "danube_delta": "ink-soft",
}

INFOFER = "https://mersultrenurilor.infofer.ro"

# Muris Atlas typefaces — copied from the vendored design system into site/fonts/
# at build time so GitHub Pages can serve them via the inlined @font-face rules.
# Century Schoolbook L = period German Antiqua (labels, body, italic hydrography).
# BetecknaGS / BetecknaGS Condensed = geometric grotesque (sheet titles, legends).
# Libre Franklin = modern UI chrome (panels, controls).
# Keep in sync with the @font-face declarations in vendor/muris-atlas/colors_and_type.css.
FONT_FACES = [
    "CenturySchL-Roma.ttf",
    "CenturySchL-Ital.ttf",
    "CenturySchL-Bold.ttf",
    "CenturySchL-BoldItal.ttf",
    "BetecknaGS.ttf",
    "BetecknaGS-Bold.ttf",
    "BetecknaGS-Italic.ttf",
    "BetecknaGSCondensed-Bold.ttf",
    "LibreFranklin-Regular.otf",
    "LibreFranklin-Medium.otf",
    "LibreFranklin-Bold.otf",
]

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
    return f'<p class="conn">{line}{train}{notes}</p>'


def _render_overview(overview: list[dict], pois: dict, palette: dict[str, str]) -> str:
    """Server-side HTML route and destination overview (no JS required).

    ``palette`` is the resolved token dict from ``load_tokens()``; category
    colours are looked up via ``CATEGORY_TOKEN`` so no hex literals are
    embedded in the rendered HTML.
    """
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
    for cat, (label, _shape) in CATEGORY_META.items():
        items = by_cat.get(cat, [])
        if not items:
            continue
        color = palette.get(CATEGORY_TOKEN[cat], "#3a2a26")
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


def _render_legend(palette: dict[str, str]) -> str:
    """Render the map legend bar.

    ``palette`` is the resolved token dict from ``load_tokens()``; colours
    are read from tokens so no hex literals are duplicated here.
    """
    station_color = palette.get("ink", "#3a2a26")
    rows = [
        ('<span class="lg-line"></span>', "Routenkorridor"),
        (f'<span class="lg-dot" style="background:{station_color}"></span>',
         "Bahnstation"),
    ]
    for cat, (label, shape) in CATEGORY_META.items():
        color = palette.get(CATEGORY_TOKEN[cat], "#3a2a26")
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
    """Assemble the full HTML string from collected data.

    Loads design tokens from ``vendor/muris-atlas/colors_and_type.css`` and
    inlines that file verbatim into the ``<style>`` block so the built page
    is self-contained and always reflects the vendored token values exactly.
    """
    palette = load_tokens()
    route_color   = palette.get("hansa-rot", "#e2566f")
    station_color = palette.get("ink",       "#3a2a26")

    paper_color = palette.get("paper", "#f4e7d1")

    payload = {
        "routes":       data["routes"],
        "pois":         data["pois"],
        "stations":     data["stations"],
        "info":         data["info"],
        "categoryMeta": {
            k: {
                "label": label,
                "color": palette.get(CATEGORY_TOKEN[k], "#3a2a26"),
                "shape": shape,
            }
            for k, (label, shape) in CATEGORY_META.items()
        },
        "routeColor":   route_color,
        "stationColor": station_color,
        "paperColor":   paper_color,   # station-dot border; matches --paper token
    }
    tokens_css = TOKENS_CSS.read_text(encoding="utf-8")
    template = (HERE / "template.html").read_text(encoding="utf-8")
    return template.format(
        tokens_css=tokens_css,
        legend=_render_legend(palette),
        overview=_render_overview(data["overview"], data["pois"], palette),
        hist_blurb=_render_history(),
        hist_surveys=json.dumps(
            [{"key": k, "label": l, "url": u} for k, l, u in ARCANUM_SURVEYS],
            ensure_ascii=False,
        ),
        data_js=_embed_json(payload),
    )


def build(out_dir: Path) -> None:
    """Build the site into ``out_dir``: write index.html and copy raw data and fonts."""
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

    # Copy Muris atlas typefaces from the vendored design system so GitHub Pages
    # can serve them via the @font-face rules inlined from colors_and_type.css.
    fonts_out = out_dir / "fonts"
    fonts_out.mkdir(exist_ok=True)
    copied = 0
    for face in FONT_FACES:
        src = VENDOR_FONTS / face
        if src.is_file():
            shutil.copyfile(src, fonts_out / face)
            copied += 1
    print(f"Schriften kopiert nach: {fonts_out} ({copied}/{len(FONT_FACES)} Dateien)")

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
