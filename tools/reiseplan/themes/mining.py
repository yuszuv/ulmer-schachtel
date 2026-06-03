"""Mining theme spec — mineral resources, quarries, oil & gas wells.

Piktogram-style atlas layer: one Point per named mine, quarry, or extraction
site.  A ``commodity`` property maps the OSM ``resource=*`` tag to a canonical
value for QGIS-rule-based piktogram assignment (coal, iron_ore, salt, gold,
oil, gas, stone, other).

OSM is a good source for this layer: mining features are well-covered and
consistently tagged in the k.u.k. / Romania region.

Output layers (EPSG:4326)
--------------------------
  data/processed/mineral_resources.geojson  — Point (mines, quarries, wells)
  data/processed/mining_attribution.json    — ODbL attribution sidecar

Usage (via CLI)
---------------
  uv run reiseplan-cli fetch-mining
  uv run reiseplan-cli fetch-mining --offline
  uv run reiseplan-cli fetch-mining --no-enrich

Attribution: © OpenStreetMap contributors, ODbL 1.0.
"""

from __future__ import annotations

import datetime

from ..overpass import OVERPASS_URL
from ..paths import ROOT
from . import KUK_ROI, OutputLayer, ThemeSpec, _register

# ---------------------------------------------------------------------------
# Commodity mapping
# ---------------------------------------------------------------------------

# OSM resource=* → canonical commodity class for QGIS piktogram styling.
# Unmapped values fall through to "other".
_COMMODITY_MAP: dict[str, str] = {
    "coal":       "coal",
    "lignite":    "coal",
    "anthracite": "coal",
    "iron_ore":   "iron_ore",
    "iron":       "iron_ore",
    "salt":       "salt",
    "halite":     "salt",
    "gold":       "gold",
    "oil":        "oil",
    "petroleum":  "oil",
    "gas":        "gas",
    "natural_gas":"gas",
    "copper":     "copper",
    "silver":     "silver",
    "lead":       "lead",
    "zinc":       "zinc",
    "manganese":  "manganese",
    "bauxite":    "bauxite",
    "chromite":   "chromite",
    "uranium":    "uranium",
    "stone":      "stone",
    "limestone":  "stone",
    "granite":    "stone",
    "sandstone":  "stone",
    "gravel":     "gravel",
    "sand":       "gravel",
    "clay":       "clay",
    "kaolin":     "clay",
}


def _commodity(tags: dict) -> str:
    """Return canonical commodity class from OSM tags."""
    raw = (tags.get("resource") or tags.get("mineral") or "").lower().strip()
    return _COMMODITY_MAP.get(raw, "other" if raw else "")


# ---------------------------------------------------------------------------
# Mining type
# ---------------------------------------------------------------------------

def _mining_type(tags: dict) -> str:
    """Classify the extraction method from OSM tags."""
    man_made   = tags.get("man_made", "")
    industrial = tags.get("industrial", "")
    historic   = tags.get("historic", "")
    landuse    = tags.get("landuse", "")
    if man_made in ("mineshaft", "adit"):
        return man_made
    if man_made == "petroleum_well":
        return "petroleum_well"
    if landuse == "quarry" or industrial == "quarry":
        return "quarry"
    if historic in ("mine", "mine_shaft"):
        return "mine_historic"
    if industrial == "mine":
        return "mine"
    return "mine"


# ---------------------------------------------------------------------------
# extra_props
# ---------------------------------------------------------------------------

def _mining_extra_props(el: dict, tags: dict, opts: dict) -> dict | None:
    return {
        "mining_type": _mining_type(tags),
        "commodity":   _commodity(tags),
        "operator":    tags.get("operator"),
        "start_date":  tags.get("start_date"),
    }


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------

def _attribution() -> dict:
    return {
        "generated":       datetime.date.today().isoformat(),
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
            "Named mine nodes (man_made=mineshaft|adit, man_made=petroleum_well, "
            "industrial=mine, historic=mine|mine_shaft) and quarry way centroids "
            "(landuse=quarry) → mineral_resources.geojson (Point). "
            "commodity field maps OSM resource=* to a canonical class for "
            "QGIS piktogram styling. "
            "German names enriched via Wikidata (CC0) where available."
        ),
    }


# ---------------------------------------------------------------------------
# OutputLayer + ThemeSpec
# ---------------------------------------------------------------------------

MINERAL_LAYER = OutputLayer(
    key="mineral_resources",
    filename="mineral_resources.geojson",
    geom="Point",
    accepts=lambda el: True,  # everything this theme fetches is a mineral resource
)

SPEC = _register(ThemeSpec(
    name="mining",
    roi=KUK_ROI,
    node_filters=(
        "man_made=mineshaft",
        "man_made=adit",
        "man_made=petroleum_well",
        "industrial=mine",
        "historic=mine",
        "historic=mine_shaft",
    ),
    way_filters=(),
    area_filters=(
        "landuse=quarry",
        "industrial=mine",
    ),
    require_name=False,   # show unnamed mines too; labels use name when available
    layers=(MINERAL_LAYER,),
    extra_props=_mining_extra_props,
    filter_el=None,
    attribution=_attribution,
    enrich_de=True,
))
