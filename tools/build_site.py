#!/usr/bin/env python3
"""Ulmer Schachtel – baut eine statische, laienfreundliche Webseite.

Erzeugt eine self-contained ``site/index.html`` mit interaktiver Leaflet-Karte
(Routen, Stationen, Ziele, Info-Marker) plus einer server-seitig gerenderten
Routen- und Ziel-Übersicht. Die Daten werden inline in die HTML eingebettet,
damit die Seite ohne Webserver (auch per ``file://``) funktioniert.

Die GeoJSON/CSV bleiben die versionierte Quelle; diese Seite ist ein
generiertes Artefakt (gitignoriert, in CI nach GitHub Pages deployt).

Wiederverwendung der Lade-Logik aus ``reiseplan_cli`` (gleicher tools/-Ordner).
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
    connections_for,
    load_geojson,
)

STATIONS_PATH = DATA_DIR / "rail_stations.geojson"
INFO_PATH = DATA_DIR / "info_markers.geojson"

# Quell-GeoJSON, die zusätzlich als Roh-Download nach site/data/ kopiert werden.
GEOJSON_SOURCES = [
    "poi_destinations.geojson",
    "rail_stations.geojson",
    "rail_route_options.geojson",
    "info_markers.geojson",
    "sample_connections.csv",
]

# POI-Kategorien -> (deutsches Label, Farbe, Form) – analog AGENTS.md/QGIS-Styles.
CATEGORY_META: dict[str, tuple[str, str, str]] = {
    "dracula_city": ("Dracula-Städte", "#8b1a1a", "circle"),
    "city": ("Städte", "#9c7a3c", "square"),
    "danube_delta": ("Donaudelta", "#1f6f6f", "triangle"),
}

ROUTE_COLOR = "#6b4f2a"
STATION_COLOR = "#4c4c4c"
BG_COLOR = "#f3ecd5"

INFOFER = "https://mersultrenurilor.infofer.ro"


def collect_data() -> dict:
    """Liest alle GeoJSON/CSV und baut das Datenobjekt für Karte + Übersicht."""
    routes = load_geojson(ROUTES_PATH)
    pois = load_geojson(POI_PATH)
    stations = load_geojson(STATIONS_PATH)
    info = load_geojson(INFO_PATH)

    # Halte je Route für die Übersicht vorbereiten (CSV via reiseplan_cli).
    overview = []
    for feature in routes["features"]:
        props = feature["properties"]
        overview.append(
            {
                "props": props,
                "stops": connections_for(props["route_id"]),
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
    """JSON für sicheres Einbetten in ein <script>-Tag serialisieren."""
    text = json.dumps(obj, ensure_ascii=False)
    # </script> bzw. allgemein </ neutralisieren, ohne die Daten zu verändern.
    return text.replace("</", "<\\/")


def render_overview(overview: list[dict], pois: dict) -> str:
    """Server-seitige HTML-Übersicht (auch ohne JavaScript lesbar)."""
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
        f'<p class="note">Fahrzeiten sind illustrativ und nicht hinterlegt – '
        f'aktuelle Zeiten unter <a href="{INFOFER}">{INFOFER}</a>.</p>'
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
    data_js = embed_json(payload)

    return TEMPLATE.format(
        bg=BG_COLOR,
        route_color=ROUTE_COLOR,
        station_color=STATION_COLOR,
        legend=legend_html,
        overview=overview_html,
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
    style: {{ color: DATA.routeColor, weight: 3, dashArray: '6 5', opacity: .9 }},
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

    # Roh-Daten zum Download bereitstellen.
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
