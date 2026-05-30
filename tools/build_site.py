#!/usr/bin/env python3
"""Ulmer Schachtel – build a static, user-friendly website.

Generates a self-contained ``site/index.html`` with an interactive Leaflet map
(routes, stations, destinations, info markers) plus a server-side-rendered
route and destination overview. Data is inlined into the HTML so the page
works without a web server (even via ``file://``).

GeoJSON/CSV remain the versioned source; this page is a generated artefact
(gitignored, deployed to GitHub Pages by CI).

Reuses loading logic from ``reiseplan_cli`` (same tools/ directory).
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

from reiseplan_cli import (  # gleicher Ordner -> direkter Import
    DATA_DIR,
    POI_PATH,
    ROUTES_PATH,
    load_geojson,
    load_timetable,
    stops_for,
)

STATIONS_PATH = DATA_DIR / "rail_stations.geojson"
INFO_PATH = DATA_DIR / "info_markers.geojson"

# Source files also copied as raw downloads to site/data/.
GEOJSON_SOURCES = [
    "poi_destinations.geojson",
    "rail_stations.geojson",
    "rail_lines.geojson",
    "info_markers.geojson",
    "route_stops.csv",
    "timetable.csv",
]

# POI categories -> (German display label, colour, shape) — matches AGENTS.md/QGIS styles.
CATEGORY_META: dict[str, tuple[str, str, str]] = {
    "dracula_city": ("Dracula-Städte", "#8b1a1a", "circle"),
    "city": ("Städte", "#9c7a3c", "square"),
    "danube_delta": ("Donaudelta", "#1f6f6f", "triangle"),
}

ROUTE_COLOR = "#6b4f2a"
STATION_COLOR = "#4c4c4c"
BG_COLOR = "#f3ecd5"

INFOFER = "https://mersultrenurilor.infofer.ro"

# Habsburg military surveys (Arcanum) — (key, label, XYZ URL).
# URL source: qgis/xyz_connections.xml. © Arcanum Maps (mapire.eu).
ARCANUM_SURVEYS = [
    ("first", "1. Militäraufnahme (1763–1787)",
     "https://tiles.arcanum.com/mercator/europe-18century-firstsurvey/{z}/{x}/{y}"),
    ("second", "2. Militäraufnahme (1806–1869)",
     "https://tiles.arcanum.com/mercator/europe-19century-secondsurvey/{z}/{x}/{y}"),
    ("third", "3. Militäraufnahme (1869–1887)",
     "https://tiles.arcanum.com/mercator/europe-19century-thirdsurvey/{z}/{x}/{y}"),
]


def collect_data() -> dict:
    """Read all GeoJSON/CSV and assemble the data object for the map and overview."""
    routes = load_geojson(ROUTES_PATH)
    pois = load_geojson(POI_PATH)
    stations = load_geojson(STATIONS_PATH)
    info = load_geojson(INFO_PATH)

    # Prepare stops and connection data per route for the overview.
    timetable = load_timetable()
    overview = []
    for feature in routes["features"]:
        props = feature["properties"]
        overview.append(
            {
                "props": props,
                "stops": stops_for(props["route_id"]),
                "timetable": timetable.get(props["route_id"], {}),
            }
        )

    return {
        "routes": routes,
        "pois": pois,
        "stations": stations,
        "info": info,
        "overview": overview,
    }


def embed_json(obj: dict) -> str:
    """Serialize JSON safe for embedding inside a <script> tag."""
    text = json.dumps(obj, ensure_ascii=False)
    # Neutralise </ sequences (e.g. </script>) without altering the data.
    return text.replace("</", "<\\/")


def render_connection(tt: dict) -> str:
    """Render a compact connection line from a timetable.csv row (or '' if empty)."""
    dep, arr, days = tt.get("dep_time", ""), tt.get("arr_time", ""), tt.get("days", "")
    if not (dep or arr or days):
        return ""  # no times entered yet — render nothing
    bits: list[str] = []
    if days:
        bits.append(html.escape(days))
    if dep:
        bits.append(f'ab {html.escape(dep)}')
    if arr:
        bits.append(f'an {html.escape(arr)}')
    if tt.get("duration"):
        bits.append(f'({html.escape(tt["duration"])})')
    line = " · ".join(bits)
    train = f' <span class="hint">{html.escape(tt["train"])}</span>' if tt.get("train") else ""
    notes = f'<br><span class="hint">{html.escape(tt["notes"])}</span>' if tt.get("notes") else ""
    return f'<p class="conn">🚆 {line}{train}{notes}</p>'


def render_overview(overview: list[dict], pois: dict) -> str:
    """Server-side HTML overview (readable without JavaScript)."""
    parts: list[str] = ["<h2>Routen im Überblick</h2>"]

    for entry in overview:
        p = entry["props"]
        tags = " ".join(
            f'<span class="tag">{html.escape(t)}</span>'
            for t in p.get("tags", "").split(",")
            if t
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

        conn = render_connection(entry.get("timetable", {}))
        if conn:
            parts.append(conn)

        if entry["stops"]:
            parts.append("<ol class=\"stops\">")
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

    # Ziele nach Kategorie gruppiert.
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
                + (f' – {html.escape(notes)}' if notes else "")
                + "</li>"
            )
        parts.append("</ul>")

    return "\n".join(parts)


def render_legend() -> str:
    rows = [
        ('<span class="lg-line"></span>', "Routenkorridor"),
        (f'<span class="lg-dot" style="background:{STATION_COLOR}"></span>', "Bahnstation"),
    ]
    for _cat, (label, color, shape) in CATEGORY_META.items():
        rows.append((f'<span class="lg-{shape}" style="--c:{color}"></span>', label))
    rows.append(('<span class="lg-info">ℹ</span>', "Info zur Karte"))
    return "".join(
        f'<div class="lg-row">{sym}<span>{html.escape(text)}</span></div>'
        for sym, text in rows
    )


def render_history() -> str:
    """SSR section for the historical map overlays (readable without JavaScript)."""
    rows = "".join(
        f'<li><b>{html.escape(name)}</b> '
        f'<span class="hint">{html.escape(period)}'
        + (f' · {html.escape(extra)}' if extra else "")
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


def render_html(data: dict) -> str:
    payload = {
        "routes": data["routes"],
        "pois": data["pois"],
        "stations": data["stations"],
        "info": data["info"],
        "categoryMeta": {k: {"label": v[0], "color": v[1], "shape": v[2]}
                         for k, v in CATEGORY_META.items()},
        "routeColor": ROUTE_COLOR,
        "stationColor": STATION_COLOR,
    }
    overview_html = render_overview(data["overview"], data["pois"])
    legend_html = render_legend()
    history_html = render_history()
    data_js = embed_json(payload)
    hist_surveys = json.dumps(
        [{"key": k, "label": l, "url": u} for k, l, u in ARCANUM_SURVEYS],
        ensure_ascii=False,
    )

    return TEMPLATE.format(
        bg=BG_COLOR,
        route_color=ROUTE_COLOR,
        station_color=STATION_COLOR,
        legend=legend_html,
        overview=overview_html,
        hist_blurb=history_html,
        hist_surveys=hist_surveys,
        data_js=data_js,
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ulmer Schachtel – Rumänien-Reiseplaner</title>
<link rel="stylesheet"
      href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
      crossorigin="">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;1,400&display=swap">
<style>
  :root {{ --bg: {bg}; --route: {route_color}; --station: {station_color}; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: #2b2113;
    font: 16px/1.5 -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
  }}
  header {{ padding: 1rem 1.25rem; border-bottom: 2px solid var(--route); }}
  header h1 {{ margin: 0; font-size: 1.4rem; }}
  header p {{ margin: .25rem 0 0; color: #5b4a30; }}
  #map {{ height: 65vh; min-height: 380px; width: 100%; }}
  .legend {{
    display: flex; flex-wrap: wrap; gap: .75rem 1.25rem;
    padding: .75rem 1.25rem; background: #fffdf5;
    border-bottom: 1px solid #d8caa0; font-size: .9rem;
  }}
  .lg-row {{ display: flex; align-items: center; gap: .4rem; }}
  .lg-line {{ width: 22px; height: 0; border-top: 3px dashed var(--route); }}
  .lg-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
  .lg-circle {{ width: 13px; height: 13px; border-radius: 50%; background: var(--c); }}
  .lg-square {{ width: 12px; height: 12px; background: var(--c); }}
  .lg-triangle {{
    width: 0; height: 0; border-left: 7px solid transparent;
    border-right: 7px solid transparent; border-bottom: 13px solid var(--c);
  }}
  .lg-info {{
    width: 16px; height: 16px; border-radius: 50%; background: #2b6cb0;
    color: #fff; font-size: 11px; line-height: 16px; text-align: center;
  }}
  main {{ max-width: 880px; margin: 0 auto; padding: 1.5rem 1.25rem 4rem; }}
  h2 {{ border-bottom: 1px solid #d8caa0; padding-bottom: .25rem; margin-top: 2rem; }}
  .route {{
    background: #fffdf5; border: 1px solid #e3d6ac; border-radius: 6px;
    padding: .75rem 1rem; margin: 1rem 0;
  }}
  .route h3 {{ margin: 0 0 .25rem; }}
  .meta {{ margin: 0; color: #5b4a30; }}
  .conn {{ margin: .4rem 0 0; color: #5b4a30; font-weight: 600; }}
  .tags {{ margin: .4rem 0 0; }}
  .tag {{
    display: inline-block; background: #ece0bd; color: #5b4a30;
    border-radius: 10px; padding: .05rem .55rem; margin: 0 .25rem .25rem 0;
    font-size: .8rem;
  }}
  ol.stops {{ margin: .5rem 0 0; padding-left: 1.4rem; }}
  ol.stops li {{ margin: .15rem 0; }}
  .hint {{ color: #7a6645; font-size: .9rem; }}
  .empty, .note {{ color: #7a6645; font-style: italic; }}
  ul.dests {{ margin: .25rem 0 0; padding-left: 1.2rem; }}
  .swatch {{
    display: inline-block; width: 12px; height: 12px; border-radius: 2px;
    margin-right: .4rem; vertical-align: middle;
  }}
  .poi-marker {{ display: block; }}
  .poi-marker.circle {{ width: 14px; height: 14px; border-radius: 50%;
    border: 2px solid #fff; box-shadow: 0 0 0 1px rgba(0,0,0,.4); }}
  .poi-marker.square {{ width: 13px; height: 13px; border: 2px solid #fff;
    box-shadow: 0 0 0 1px rgba(0,0,0,.4); }}
  .poi-marker.triangle {{ width: 0; height: 0; border-left: 8px solid transparent;
    border-right: 8px solid transparent; filter: drop-shadow(0 0 1px #000); }}
  a {{ color: #6b4f2a; }}

  /* ---------- Vintage / Eye-Candy ---------- */
  body {{
    background-image:
      radial-gradient(circle at 18% 8%, rgba(255,255,255,.55), transparent 42%),
      radial-gradient(circle at 82% 0%, rgba(176,140,80,.16), transparent 48%),
      repeating-linear-gradient(0deg, rgba(120,90,40,.028) 0 2px, transparent 2px 5px);
  }}
  h1, h2, h3, .ulm-panel-title {{
    font-family: "EB Garamond", Georgia, "Times New Roman", serif;
    font-weight: 600; letter-spacing: .01em;
  }}
  header {{ text-align: center; background: linear-gradient(#fffdf5, #f6efd8); }}
  header h1 {{ font-size: 1.95rem; letter-spacing: .04em; }}
  header h1::after {{
    content: "\\2726  \\2767  \\2726"; display: block; color: var(--route);
    font-size: .8rem; letter-spacing: .4em; margin-top: .3rem; opacity: .65;
  }}
  header p {{ font-style: italic; }}
  #map {{
    border: 6px solid #efe6c8; outline: 2px solid var(--route);
    outline-offset: -8px; box-shadow: inset 0 0 40px rgba(80,55,20,.25);
  }}
  /* Sepia-Look nur auf den modernen Basiskacheln */
  .leaflet-container.sepia .leaflet-tile-pane {{
    filter: sepia(.7) saturate(.85) contrast(.95) brightness(1.03);
  }}
  /* animierte Routenkorridore ("marching ants") */
  .route-ants {{ animation: ants 1.4s linear infinite; }}
  @keyframes ants {{ to {{ stroke-dashoffset: -22; }} }}
  /* Popups im Pergament-Stil */
  .leaflet-popup-content-wrapper {{
    background: #fffdf5; color: #2b2113; border: 1px solid #d8caa0;
    border-radius: 5px; box-shadow: 0 2px 10px rgba(60,40,10,.35);
    font-family: "EB Garamond", Georgia, serif; font-size: 1.02rem;
  }}
  .leaflet-popup-tip {{ background: #fffdf5; }}
  /* POI-Marker: sanfter Hover */
  .poi-marker {{ transition: transform .12s ease; }}
  .leaflet-marker-icon:hover .poi-marker {{ transform: scale(1.25); }}
  /* Eigene Bedienfelder (Historische Karte + Sepia) */
  .ulm-panel {{
    background: #fffdf5; border: 1px solid #d8caa0; border-radius: 5px;
    padding: .5rem .6rem; font-size: .85rem; max-width: 220px;
    box-shadow: 0 1px 6px rgba(60,40,10,.25);
  }}
  .ulm-panel-title {{ font-weight: 700; margin-bottom: .35rem; color: var(--route); }}
  .ulm-sel {{ width: 100%; margin-bottom: .45rem; }}
  .ulm-op {{ display: block; font-size: .8rem; color: #5b4a30; }}
  .ulm-range {{ width: 100%; margin-top: .2rem; }}
  .ulm-btn {{
    font: inherit; background: #fffdf5; color: var(--route); cursor: pointer;
    border: 1px solid #d8caa0; border-radius: 5px; padding: .25rem .55rem;
    box-shadow: 0 1px 6px rgba(60,40,10,.25);
  }}
  .ulm-btn:hover {{ background: #f3ead0; }}
</style>
</head>
<body>
<header>
  <h1>Ulmer Schachtel – Rumänien-Reiseplaner</h1>
  <p>Bahnreise-Planung: Dracula-Städte, Temeschburg, Bukarest und Donaudelta.</p>
</header>
<div id="map"></div>
<div class="legend">{legend}</div>
<main>
{overview}
{hist_blurb}
</main>

<script
  src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
  crossorigin=""></script>
<script id="reiseplan-data" type="application/json">
{data_js}
</script>
<script>
(function () {{
  var DATA = JSON.parse(document.getElementById('reiseplan-data').textContent);

  var map = L.map('map');

  // Basiskarten (umschaltbar): OSM bringt eigene Labels mit, CARTO-"nolabels" ist bewusst beschriftungsfrei.
  var osm = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 19, attribution: '&copy; OpenStreetMap-Mitwirkende'
  }}).addTo(map);
  var clean = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_nolabels/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 20, attribution: '&copy; OpenStreetMap-Mitwirkende, &copy; CARTO'
  }});

  // Optionales Label-Overlay (moderne Orts-/Straßennamen, im Tileset zoom-abhängig:
  // Orte weit draußen, Straßen beim Reinzoomen). Eigene Pane über der Basis, unter den Daten.
  map.createPane('labelPane');
  map.getPane('labelPane').style.zIndex = 350;
  map.getPane('labelPane').style.pointerEvents = 'none';
  var labels = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{{z}}/{{x}}/{{y}}.png', {{
    pane: 'labelPane', maxZoom: 20, attribution: '&copy; CARTO'
  }});

  function esc(s) {{
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }}

  // Routenkorridore (LineStrings)
  var routes = L.geoJSON(DATA.routes, {{
    style: {{ color: DATA.routeColor, weight: 3, dashArray: '6 5', opacity: .9, className: 'route-ants' }},
    onEachFeature: function (f, layer) {{
      var p = f.properties;
      layer.bindPopup(
        '<b>' + esc(p.route_name) + '</b><br>' +
        esc(p.from_city) + ' → ' + esc(p.to_city) +
        '<br>ca. ' + esc(p.length_km) + ' km' +
        '<br><small>' + esc(p.tags) + '</small>'
      );
    }}
  }}).addTo(map);

  // Bahnstationen (Punkte)
  var stations = L.geoJSON(DATA.stations, {{
    pointToLayer: function (f, latlng) {{
      return L.circleMarker(latlng, {{
        radius: 4, color: '#fff', weight: 1,
        fillColor: DATA.stationColor, fillOpacity: 1
      }});
    }},
    onEachFeature: function (f, layer) {{
      var p = f.properties;
      layer.bindPopup('<b>' + esc(p.name) + '</b><br>Station ' + esc(p.station_id));
    }}
  }}).addTo(map);

  // Reiseziele (POIs) – Form/Farbe je Kategorie
  var pois = L.geoJSON(DATA.pois, {{
    pointToLayer: function (f, latlng) {{
      var meta = DATA.categoryMeta[f.properties.category] || {{}};
      var shape = meta.shape || 'circle';
      var color = meta.color || '#333';
      var style = shape === 'triangle'
        ? 'border-bottom-color:' + color
        : 'background:' + color;
      var icon = L.divIcon({{
        className: '',
        html: '<span class="poi-marker ' + shape + '" style="' + style + '"></span>',
        iconSize: [16, 16], iconAnchor: [8, 8]
      }});
      return L.marker(latlng, {{ icon: icon }});
    }},
    onEachFeature: function (f, layer) {{
      var p = f.properties;
      layer.bindPopup(
        '<b>' + esc(p.name) + '</b><br>' + esc(p.notes || '')
      );
    }}
  }}).addTo(map);

  // Info-Marker ("Über diese Karte") – body enthält bewusst HTML.
  var info = L.geoJSON(DATA.info, {{
    pointToLayer: function (f, latlng) {{
      var icon = L.divIcon({{
        className: '',
        html: '<span class="lg-info" style="width:22px;height:22px;' +
              'line-height:22px;font-size:14px">i</span>',
        iconSize: [22, 22], iconAnchor: [11, 11]
      }});
      return L.marker(latlng, {{ icon: icon }});
    }},
    onEachFeature: function (f, layer) {{
      var p = f.properties;
      layer.bindPopup('<div style="max-width:260px">' + (p.body || '') + '</div>');
    }}
  }}).addTo(map);

  L.control.layers(
    {{ 'OpenStreetMap': osm, 'Hell, ohne Labels (CARTO)': clean }},
    {{
      'Orts-/Straßennamen': labels,
      'Routen': routes,
      'Bahnstationen': stations,
      'Reiseziele': pois,
      'Info': info
    }}, {{ collapsed: false }}).addTo(map);

  // --- Historische Karten (Arcanum): Overlay in eigener Pane + Transparenz-Regler ---
  var HIST = {hist_surveys};
  map.createPane('histPane');
  map.getPane('histPane').style.zIndex = 300;   // über Basis (200), unter Labels (350)
  var histLayer = null;
  function setHist(key, opacity) {{
    if (histLayer) {{ map.removeLayer(histLayer); histLayer = null; }}
    var s = HIST.filter(function (x) {{ return x.key === key; }})[0];
    if (s) {{
      histLayer = L.tileLayer(s.url, {{
        pane: 'histPane', maxNativeZoom: 14, maxZoom: 20,
        opacity: opacity, attribution: '&copy; Arcanum Maps (mapire.eu)'
      }}).addTo(map);
    }}
  }}
  var HistControl = L.Control.extend({{
    options: {{ position: 'topright' }},
    onAdd: function () {{
      var d = L.DomUtil.create('div', 'ulm-panel');
      var opts = '<option value="">— keine —</option>';
      HIST.forEach(function (s) {{
        opts += '<option value="' + s.key + '">' + s.label + '</option>';
      }});
      d.innerHTML =
        '<div class="ulm-panel-title">Historische Karte</div>' +
        '<select class="ulm-sel">' + opts + '</select>' +
        '<label class="ulm-op">Transparenz' +
        '<input class="ulm-range" type="range" min="0" max="100" value="70"></label>';
      L.DomEvent.disableClickPropagation(d);
      L.DomEvent.disableScrollPropagation(d);
      var sel = d.querySelector('.ulm-sel'), rng = d.querySelector('.ulm-range');
      sel.addEventListener('change', function () {{ setHist(sel.value, rng.value / 100); }});
      rng.addEventListener('input', function () {{
        if (histLayer) histLayer.setOpacity(rng.value / 100);
      }});
      return d;
    }}
  }});
  map.addControl(new HistControl());

  // --- Sepia-Umschalter (nur moderne Basiskacheln) ---
  var SepiaControl = L.Control.extend({{
    options: {{ position: 'topright' }},
    onAdd: function () {{
      var b = L.DomUtil.create('button', 'ulm-btn');
      b.type = 'button'; b.textContent = 'Sepia: aus';
      L.DomEvent.disableClickPropagation(b);
      b.addEventListener('click', function () {{
        var on = map.getContainer().classList.toggle('sepia');
        b.textContent = 'Sepia: ' + (on ? 'an' : 'aus');
      }});
      return b;
    }}
  }});
  map.addControl(new SepiaControl());

  L.control.scale({{ metric: true, imperial: false }}).addTo(map);

  // Ausschnitt über alle Features.
  var group = L.featureGroup([routes, stations, pois, info]);
  var bounds = group.getBounds();
  if (bounds.isValid()) {{
    map.fitBounds(bounds, {{ padding: [20, 20] }});
  }} else {{
    map.setView([45.9, 25.0], 6);
  }}
}})();
</script>
</body>
</html>
"""


def build(out_dir: Path) -> None:
    data = collect_data()
    html_text = render_html(data)

    out_dir.mkdir(parents=True, exist_ok=True)
    index = out_dir / "index.html"
    index.write_text(html_text, encoding="utf-8")

    # Copy raw data files for download.
    data_out = out_dir / "data"
    data_out.mkdir(exist_ok=True)
    for name in GEOJSON_SOURCES:
        src = DATA_DIR / name
        if src.is_file():
            shutil.copyfile(src, data_out / name)

    print(f"Seite gebaut: {index}")
    print(f"Rohdaten kopiert nach: {data_out}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="build-site",
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
