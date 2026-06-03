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
_ATTRIBUTION_SRC = ROOT / "data" / "processed" / "natural_attribution.json"


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
            "docs/data-and-layers/curved-labels.md."
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
    """Add natural/place/ele/importance props; return None to skip filtered elements."""
    natural = tags.get("natural")
    props: dict = {
        "natural": natural,
        "place":   tags.get("place"),
    }

    ele_raw = tags.get("ele", "").strip()
    if ele_raw:
        ele_val = parse_ele(ele_raw)
        if ele_val is not None:
            props["ele"] = ele_val

    # 1. PEAKS
    if natural == "peak" and el.get("type") == "node":
        min_ele = opts.get("min_ele", 1500)
        has_wd = "wikidata" in tags
        has_wp = "wikipedia" in tags
        has_rel = has_wd or has_wp
        
        # Calculate scaled thresholds relative to min_ele
        wd_threshold = max(0, min_ele - 500)
        no_wd_threshold = min_ele + 500
        
        ele_val = props.get("ele")
        ele_num = None
        if ele_val is not None:
            try:
                ele_num = float(str(ele_val))
            except (ValueError, TypeError):
                pass

        # Filter: Skip if no elevation and no wikidata/wikipedia
        if ele_num is None and not has_rel:
            return None

        # Filter: Skip based on elevation thresholds
        if ele_num is not None:
            if has_rel:
                if ele_num < wd_threshold:
                    return None
            else:
                if ele_num < no_wd_threshold:
                    return None
        
        # Determine importance (1-4)
        if has_rel and ele_num is not None and ele_num >= min_ele + 500:
            imp = 1  # Major Peak
        elif (has_rel and ele_num is not None and ele_num >= min_ele) or (not has_rel and ele_num is not None and ele_num >= min_ele + 1000):
            imp = 2  # Significant Peak
        elif (has_rel and ele_num is not None and ele_num >= wd_threshold) or (not has_rel and ele_num is not None and ele_num >= no_wd_threshold):
            imp = 3  # Minor Peak
        else:
            imp = 4  # Unknown elevation/low priority but has wikidata/wikipedia
        
        props["importance"] = imp

    # 2. RIDGES
    elif natural == "ridge" and el.get("type") == "way":
        has_wd = "wikidata" in tags
        has_wp = "wikipedia" in tags
        has_rel = has_wd or has_wp
        
        # Calculate approximate length of way geometry in degrees
        geom = el.get("geometry", [])
        length = 0.0
        import math
        for i in range(len(geom) - 1):
            p1 = geom[i]
            p2 = geom[i+1]
            if "lon" in p1 and "lat" in p1 and "lon" in p2 and "lat" in p2:
                length += math.sqrt((p2["lon"] - p1["lon"])**2 + (p2["lat"] - p1["lat"])**2)
                
        props["length_deg"] = round(length, 4)
        
        # Filter: Skip short ridges with no wikidata/wikipedia as local noise
        if length < 0.005 and not has_rel:
            return None
            
        # Determine importance (1-3)
        if has_rel and length >= 0.02:
            imp = 1  # Major Ridge
        elif (has_rel and length < 0.02) or (not has_rel and length >= 0.04):
            imp = 2  # Significant Ridge
        else:
            imp = 3  # Minor Ridge
            
        props["importance"] = imp

    # 3. LANDSCAPE LABELS (mountain ranges, valleys)
    elif natural in ("mountain_range", "valley") and el.get("type") == "node":
        has_wd = "wikidata" in tags
        has_wp = "wikipedia" in tags
        
        # Determine importance (1-2)
        if has_wd or has_wp:
            imp = 1  # Major range/valley
        else:
            imp = 2  # Minor/local range/valley
            
        props["importance"] = imp

    return props


# ---------------------------------------------------------------------------
# Sort keys
# ---------------------------------------------------------------------------

def _peak_sort_key(f: dict) -> tuple[int, int, str]:
    """Sort peaks by ascending importance (priority), then descending elevation, then name."""
    importance = f["properties"].get("importance", 4)
    ele = f["properties"].get("ele")
    try:
        ele_int = int(float(str(ele))) if ele is not None else 0
    except (ValueError, TypeError):
        ele_int = 0
    return (importance, -ele_int, f["properties"].get("name") or "")


def _ridge_sort_key(f: dict) -> tuple[int, float, str]:
    """Sort ridges by ascending importance (priority), then descending length, then name."""
    importance = f["properties"].get("importance", 3)
    length = f["properties"].get("length_deg", 0.0)
    return (importance, -length, f["properties"].get("name") or "")


def _landscape_sort_key(f: dict) -> tuple[int, str]:
    """Sort landscape labels by ascending importance (priority), then name."""
    importance = f["properties"].get("importance", 2)
    return (importance, f["properties"].get("name") or "")


# ---------------------------------------------------------------------------
# OutputLayer definitions
# ---------------------------------------------------------------------------

RIDGES_LAYER = OutputLayer(
    key="natural_ridges",
    filename="natural_ridges.geojson",
    geom="LineString",
    accepts=lambda el: el.get("type") == "way",
    sort_key=_ridge_sort_key,
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
    sort_key=_landscape_sort_key,
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
