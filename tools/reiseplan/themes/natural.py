"""Natural-feature theme spec — mountain ridges, peaks, valleys, landscapes.

Defines the ThemeSpec for the natural-feature pipeline that was previously
embedded in fetch_natural.py.  The logic, output structure, and sort order
are preserved exactly so existing GeoJSON outputs remain byte-identical when
running ``reiseplan-natural --offline`` after this refactor.

Output layers (EPSG:4326)
--------------------------
  natural_ridges.geojson    — LineString  (natural=ridge ways)
  mountain_peaks.geojson    — Point       (natural=peak nodes, ele ≥ min_ele)
  landscape_labels.geojson  — Point       (mountain_range + valley label anchors)

German names are enriched via Wikidata (see enrich.py).

Attribution: © OpenStreetMap contributors, ODbL 1.0 + Wikidata CC0.
"""

from __future__ import annotations

import datetime

from ..geo import parse_ele
from ..overpass import OVERPASS_URL
from ..paths import ROOT
from ..tiles import BBox
from . import KUK_ROI, OutputLayer, ThemeSpec, _register

# ---------------------------------------------------------------------------
# Overpass query templates for the attribution sidecar
# ---------------------------------------------------------------------------

_TILE_STEP       = 4.0
_QUERY_TIMEOUT   = 75
_WIKIDATA_CACHE  = ROOT / "data" / "raw"       / "wikidata_de_labels.json"
_ATTRIBUTION_SRC = ROOT / "data" / "processed" / "natural_features_attribution.json"


def _example_way_query() -> str:
    """Way query template used in the attribution sidecar."""
    s, w = KUK_ROI.south, KUK_ROI.west
    n, e = s + _TILE_STEP, w + _TILE_STEP
    bb = f"{s},{w},{n},{e}"
    return (
        f"[out:json][timeout:{_QUERY_TIMEOUT}];\n"
        f'way["natural"="ridge"]["name"]({bb});\n'
        "out geom;\n"
    )


def _example_node_query() -> str:
    """Node query template used in the attribution sidecar."""
    s, w = KUK_ROI.south, KUK_ROI.west
    n, e = s + _TILE_STEP, w + _TILE_STEP
    bb = f"{s},{w},{n},{e}"
    return (
        f"[out:json][timeout:{_QUERY_TIMEOUT}];\n"
        "(\n"
        f'  node["natural"="peak"]["name"]({bb});\n'
        f'  node["natural"="mountain_range"]["name"]({bb});\n'
        f'  node["natural"="valley"]["name"]({bb});\n'
        ");\n"
        "out geom;\n"
    )


def _attribution() -> dict:
    tiles_n = len(list(_iter_tile_count()))
    return {
        "generated":       datetime.date.today().isoformat(),
        "source":          "OpenStreetMap via Overpass API",
        "url":             OVERPASS_URL,
        "license":         "ODbL 1.0 — © OpenStreetMap contributors",
        "attribution_url": "https://www.openstreetmap.org/copyright",
        "name_de_source": {
            "source":  "Wikidata (wbgetentities labels, languages=de)",
            "license": "CC0",
            "cache":   str(_WIKIDATA_CACHE.relative_to(ROOT)),
            "note": (
                "Where OSM has no name:de tag but the feature carries a "
                "wikidata QID, the German label is used as name_de "
                "(name_de_src='wikidata'); otherwise name_de_src='osm'."
            ),
        },
        "roi_bbox": {
            "south":       KUK_ROI.south,
            "west":        KUK_ROI.west,
            "north":       KUK_ROI.north,
            "east":        KUK_ROI.east,
            "description": (
                "Austria-Hungary + Romania extent ~1880 "
                "(derived from data/reference/historical/kuk_clip.geojson)"
            ),
        },
        "tile_strategy": (
            f"{tiles_n} tiles of {_TILE_STEP}° × {_TILE_STEP}° "
            f"with 0.1° overlap; 2 Overpass calls per tile "
            f"(ways + nodes separately) to avoid combined timeouts in the "
            f"dense Alpine area; per-call server timeout {_QUERY_TIMEOUT}s."
        ),
        "methodology": (
            "Named ridge ways → natural_ridges.geojson (LineString, for QGIS "
            "Curved label placement). "
            "Named peak nodes → mountain_peaks.geojson (Point, ele ≥ default "
            "1500 m). "
            "Named mountain_range + valley nodes → landscape_labels.geojson "
            "(Point, straight labels). "
            "Relations excluded — mountain-range names are duplicated on OSM "
            "nodes. "
            "For large arcing names without OSM line geometry (Karpaten, "
            "Südkarpaten, Siebenbürgen), add hand-drawn lines per "
            "docs/08_curved_labels.md."
        ),
        "way_query_template":  _example_way_query(),
        "node_query_template": _example_node_query(),
    }


def _iter_tile_count():
    """Helper to count tiles without importing tile_grid (avoids circular dep)."""
    from ..tiles import tile_grid
    yield from tile_grid(KUK_ROI)


# ---------------------------------------------------------------------------
# extra_props for the natural theme
# ---------------------------------------------------------------------------

def _natural_extra_props(el: dict, tags: dict, opts: dict) -> dict | None:
    """Add natural/place/ele props; return None to skip peaks below min_ele."""
    props: dict = {
        "natural": tags.get("natural"),
        "place":   tags.get("place"),
    }

    ele_raw = tags.get("ele", "").strip()
    if ele_raw:
        ele_val = parse_ele(ele_raw)
        if ele_val is not None:
            props["ele"] = ele_val

    # Apply the min_ele filter for peaks.
    if tags.get("natural") == "peak" and el.get("type") == "node":
        min_ele = opts.get("min_ele", 1500)
        ele_val = props.get("ele")
        if ele_val is not None:
            try:
                if int(float(str(ele_val))) < min_ele:
                    return None
            except (ValueError, TypeError):
                pass  # unparseable ele → include anyway

    return props


# ---------------------------------------------------------------------------
# Sort keys (must match original fetch_natural.py for byte-identical output)
# ---------------------------------------------------------------------------

def _peak_sort_key(f: dict) -> tuple[int, str]:
    """Sort peaks by descending elevation, then name (stable, reproducible)."""
    ele = f["properties"].get("ele")
    try:
        ele_int = int(float(str(ele))) if ele is not None else 0
    except (ValueError, TypeError):
        ele_int = 0
    return (-ele_int, f["properties"].get("name") or "")


def _name_sort_key(f: dict) -> str:
    return f["properties"].get("name") or ""


# ---------------------------------------------------------------------------
# OutputLayer definitions
# ---------------------------------------------------------------------------

RIDGES_LAYER = OutputLayer(
    key="natural_ridges",
    filename="natural_ridges.geojson",
    geom="LineString",
    accepts=lambda el: el.get("type") == "way",
    sort_key=_name_sort_key,
)

PEAKS_LAYER = OutputLayer(
    key="mountain_peaks",
    filename="mountain_peaks.geojson",
    geom="Point",
    accepts=lambda el: (
        el.get("type") == "node"
        and el.get("tags", {}).get("natural") == "peak"
    ),
    sort_key=_peak_sort_key,
)

LANDSCAPE_LAYER = OutputLayer(
    key="landscape_labels",
    filename="landscape_labels.geojson",
    geom="Point",
    accepts=lambda el: (
        el.get("type") == "node"
        and el.get("tags", {}).get("natural") in ("mountain_range", "valley")
    ),
    sort_key=_name_sort_key,
)

# ---------------------------------------------------------------------------
# ThemeSpec
# ---------------------------------------------------------------------------

SPEC = _register(ThemeSpec(
    name="natural",
    roi=KUK_ROI,
    # way query: ridge lines
    way_filters=("natural=ridge",),
    # node query: peaks, mountain ranges, valleys
    node_filters=("natural=peak", "natural=mountain_range", "natural=valley"),
    area_filters=(),
    require_name=True,
    layers=(RIDGES_LAYER, PEAKS_LAYER, LANDSCAPE_LAYER),
    extra_props=_natural_extra_props,
    filter_el=None,
    attribution=_attribution,
    enrich_de=True,
))
