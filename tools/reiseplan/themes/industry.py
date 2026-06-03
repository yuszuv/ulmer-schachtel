"""Industry theme spec — power plants, works, and industrial sites.

Piktogram-style atlas layer: one Point per named industrial installation.
A ``branch`` property classifies the site type for QGIS rule-based styling
(hydro/thermal/wind/nuclear power; iron/steel/chemical/textile/other works).

OSM tags covered:
  man_made=works          — factories, mills, processing plants
  power=plant             — power stations (with plant:source sub-type)
  landuse=industrial      — general industrial zones (area → centroid)

Output layers (EPSG:4326)
--------------------------
  data/processed/industry_sites.geojson    — Point
  data/processed/industry_attribution.json — ODbL attribution sidecar

Usage (via CLI)
---------------
  uv run reiseplan-cli fetch-industry
  uv run reiseplan-cli fetch-industry --offline
  uv run reiseplan-cli fetch-industry --no-enrich

Attribution: © OpenStreetMap contributors, ODbL 1.0.
"""

from __future__ import annotations

import datetime

from ..overpass import OVERPASS_URL
from . import KUK_ROI, OutputLayer, ThemeSpec, _register

# ---------------------------------------------------------------------------
# Branch mapping
# ---------------------------------------------------------------------------

# power plant:source=* → branch class
_POWER_SOURCE_MAP: dict[str, str] = {
    "hydro":   "power_hydro",
    "water":   "power_hydro",
    "thermal": "power_thermal",
    "coal":    "power_thermal",
    "gas":     "power_thermal",
    "oil":     "power_thermal",
    "nuclear": "power_nuclear",
    "wind":    "power_wind",
    "solar":   "power_solar",
}

# product=* / industrial=* → branch class for works
_WORKS_BRANCH_MAP: dict[str, str] = {
    "steel":      "steel",
    "iron":       "steel",
    "iron_steel": "steel",
    "chemicals":  "chemical",
    "chemical":   "chemical",
    "textiles":   "textile",
    "textile":    "textile",
    "paper":      "paper",
    "pulp":       "paper",
    "sugar":      "food",
    "food":       "food",
    "beer":       "food",
    "glass":      "glass",
    "ceramics":   "ceramics",
    "cement":     "cement",
    "sawmill":    "wood",
    "lumber":     "wood",
}


def _branch(tags: dict) -> str:
    """Return branch classification from OSM tags."""
    power = tags.get("power", "")
    man_made = tags.get("man_made", "")

    if power == "plant":
        source = tags.get("plant:source", "").lower()
        return _POWER_SOURCE_MAP.get(source, "power_other")

    if man_made == "works":
        product    = (tags.get("product") or "").lower()
        industrial = (tags.get("industrial") or "").lower()
        return (
            _WORKS_BRANCH_MAP.get(product)
            or _WORKS_BRANCH_MAP.get(industrial)
            or "works_other"
        )

    return "industrial"


# ---------------------------------------------------------------------------
# extra_props
# ---------------------------------------------------------------------------

def _industry_extra_props(el: dict, tags: dict, opts: dict) -> dict | None:
    name = tags.get("name")
    has_wd = "wikidata" in tags
    has_wp = "wikipedia" in tags
    has_rel = has_wd or has_wp
    
    # Filter: Skip if no name and no wikidata/wikipedia
    if not name and not has_rel:
        return None
        
    branch = _branch(tags)
    
    # Filter: Skip generic industrial zones unless they are major (have wikidata or operator info)
    if branch == "industrial" and not has_rel and not tags.get("operator"):
        return None
        
    # Determine importance (1-3)
    # 1: Has Wikidata/Wikipedia, or nuclear power plants
    # 2: Power plants (hydro, thermal, wind, solar) or heavy industries (steel, chemical, cement, paper)
    # 3: Other works/factories (food, wood, textile, works_other) or named/documented industrial zones
    if has_rel or branch == "power_nuclear":
        imp = 1
    elif branch.startswith("power_") or branch in ("steel", "chemical", "cement", "paper"):
        imp = 2
    else:
        imp = 3

    return {
        "branch":     branch,
        "operator":   tags.get("operator"),
        "start_date": tags.get("start_date"),
        "importance": imp,
    }


# ---------------------------------------------------------------------------
# Sort keys
# ---------------------------------------------------------------------------

def _industry_sort_key(f: dict) -> tuple[int, str]:
    """Sort industry features by ascending importance (priority), then name."""
    importance = f["properties"].get("importance", 3)
    return (importance, f["properties"].get("name") or "")


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------

def _attribution() -> dict:
    return {
        "generated":       __import__("datetime").date.today().isoformat(),
        "source":          "OpenStreetMap via Overpass API",
        "url":             OVERPASS_URL,
        "license":         "ODbL 1.0 — © OpenStreetMap contributors",
        "attribution_url": "https://www.openstreetmap.org/copyright",
        "roi_bbox": {
            "south": KUK_ROI.south, "west": KUK_ROI.west,
            "north": KUK_ROI.north, "east": KUK_ROI.east,
            "description": "Austria-Hungary + Romania extent ~1880",
        },
        "methodology": (
            "Named industrial installations → industry_sites.geojson (Point). "
            "Covers power plants (power=plant), factories (man_made=works), "
            "and industrial zones (landuse=industrial, way centroid). "
            "Filters out unnamed/generic features without Wikidata/Wikipedia links to reduce noise. "
            "branch field classifies the installation type for QGIS "
            "piktogram styling. "
            "importance field represents feature priority (1 = Major, 2 = Significant, 3 = Minor). "
            "German names enriched via Wikidata (CC0) where available."
        ),
    }


# ---------------------------------------------------------------------------
# OutputLayer + ThemeSpec
# ---------------------------------------------------------------------------

INDUSTRY_LAYER = OutputLayer(
    key="industry_sites",
    filename="industry_sites.geojson",
    geom="Point",
    accepts=lambda el: True,
    sort_key=_industry_sort_key,
)

SPEC = _register(ThemeSpec(
    name="industry",
    roi=KUK_ROI,
    node_filters=(
        "power=plant",
        "man_made=works",
    ),
    way_filters=(),
    area_filters=(
        "power=plant",
        "man_made=works",
        "landuse=industrial",
    ),
    require_name=False,   # keep False to allow unnamed features with wikidata (they are filtered in extra_props if they lack both)
    layers=(INDUSTRY_LAYER,),
    extra_props=_industry_extra_props,
    filter_el=None,
    attribution=_attribution,
    enrich_de=True,
))
