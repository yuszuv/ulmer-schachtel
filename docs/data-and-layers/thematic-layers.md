# 10 — Thematic Atlas Layers (Pattern 4 Pipeline)

## Overview

The thematic-layer pipeline provides a generic, declarative way to fetch OSM
features, enrich them with Wikidata German names, and write GeoJSON layers
ready for QGIS piktogram styling.

**Three themes** are implemented:

| Theme | CLI command | Output file | Source |
|-------|------------|-------------|--------|
| Natural features | `fetch-natural` | `natural_ridges.geojson`<br>`mountain_peaks.geojson`<br>`landscape_labels.geojson` | OSM © ODbL |
| Mineral resources | `fetch-mining` | `mineral_resources.geojson` | OSM © ODbL |
| Industry sites | `fetch-industry` | `industry_sites.geojson` | OSM © ODbL |

All outputs land in `data/processed/` (EPSG:4326 GeoJSON).  QGIS styling
scripts live in `tools/qgis_{natural_features,mining,industry}.py`.

---

## Usage

```bash
# Fetch online + write GeoJSON + attribution sidecar
uv run reiseplan-cli fetch-mining
uv run reiseplan-cli fetch-industry

# Offline rebuild from raw cache (no network)
uv run reiseplan-cli fetch-mining   --offline
uv run reiseplan-cli fetch-industry --offline

# Skip Wikidata enrichment
uv run reiseplan-cli fetch-mining --no-enrich
```

---

## Architecture — Pattern 4 (Strategy + Registry)

### Core types (`tools/reiseplan/themes/__init__.py`)

```
ThemeSpec(frozen dataclass)
  name          str            registry key + raw-cache filename stem
  roi           BBox           region of interest (WGS84 degrees)
  node_filters  tuple[str]     OSM tag selectors for node queries
  way_filters   tuple[str]     OSM tag selectors for way/LineString queries
  area_filters  tuple[str]     OSM tag selectors for area→centroid queries
  require_name  bool           add ["name"] filter to all selectors
  layers        tuple[OutputLayer, ...]
  extra_props   Callable       (el, tags, opts) → dict | None  (None = skip)
  filter_el     Callable|None  (el, tags, opts) → bool
  attribution   Callable|None  () → dict
  enrich_de     bool           attempt Wikidata German-name enrichment

OutputLayer(frozen dataclass)
  key      str            e.g. "mineral_resources"
  filename str            → data/processed/<filename>
  geom     str            "Point" | "LineString"
  accepts  Callable       el → True if this layer claims the element
  sort_key Callable|None  feature-level sort (default: sort by name)
```

### Generic runner (`tools/reiseplan/thematic.py`)

```python
from reiseplan.thematic import run
from reiseplan.themes import REGISTRY

run(REGISTRY["mining"], offline=False, enrich=True)
```

The runner:
1. `tiles.fetch_tiled` → tiled Overpass fetch + deduplicate + cache
2. `enrich.german_names` → Wikidata labels (additive shared cache)
3. `_build_features` → classify elements into per-layer GeoJSON features
4. Sort each layer's features by `OutputLayer.sort_key`
5. `repository.write_json` → GeoJSON output + attribution sidecar

### Shared infrastructure

| Module | Role |
|--------|------|
| `tiles.py` | BBox, tile_grid, fetch_tiled, offline cache |
| `geo.py` | way_to_linestring, node_to_point, centroid_of, parse_ele |
| `enrich.py` | resolve_name_de, german_names (shared Wikidata cache) |
| `wikidata.py` | WikidataLabelGateway (batched wbgetentities) |

---

## Adding a new theme

1. **Create `tools/reiseplan/themes/mytheme.py`**:

```python
from . import KUK_ROI, OutputLayer, ThemeSpec, _register

MY_LAYER = OutputLayer(
    key="my_features",
    filename="my_features.geojson",
    geom="Point",
    accepts=lambda el: True,
)

def _extra_props(el, tags, opts):
    return {"my_field": tags.get("my_tag", "")}

def _attribution():
    import datetime
    return {"generated": datetime.date.today().isoformat(), ...}

SPEC = _register(ThemeSpec(
    name="mytheme",
    roi=KUK_ROI,
    node_filters=("my_tag=my_value",),
    way_filters=(),
    area_filters=(),
    require_name=False,
    layers=(MY_LAYER,),
    extra_props=_extra_props,
    attribution=_attribution,
))
```

2. **Import in `thematic.py`** (adds to REGISTRY automatically):

```python
from .themes import mytheme as _th_mytheme  # noqa: F401
```

3. **Register CLI command in `cli.py`**:

```python
@command("fetch-mytheme", help="Mein neues Thema", args=[...])
def _fetch_mytheme(args):
    thematic.run(_THEME_REGISTRY["mytheme"], offline=args.offline)
```

4. **Add QGIS styling script** `tools/qgis_mytheme.py` (copy from `qgis_mining.py`).

---

## Data sources and attribution

| Theme | Source | License |
|-------|--------|---------|
| All OSM themes | OpenStreetMap via Overpass API | © ODbL 1.0 |
| German names | Wikidata `wbgetentities` labels | CC0 |

Attribution sidecars are written to `data/processed/{name}_attribution.json`.

**Commodity classes (mining)**:
coal, iron_ore, salt, gold, silver, oil, gas, copper, lead, zinc, manganese,
bauxite, chromite, uranium, stone, gravel, clay, other.
Mapped from OSM `resource=*` tag.

**Branch classes (industry)**:
power_hydro, power_thermal, power_nuclear, power_wind, power_solar,
steel, chemical, textile, paper, food, glass, ceramics, cement, wood,
works_other, industrial.
Mapped from `power=plant` + `plant:source=*` and `man_made=works` + `product=*`.

---

## Clutter Prevention & Importance Categorization

Due to the huge amount of OSM data within the k.u.k. / Romania bounding box, all layers are filtered to remove local noise and categorized by an `importance` property (values 1–4, where 1 is highest priority). This allows QGIS and QField to use scale-dependent rendering rules to display only major landmarks when zoomed out and gradually reveal minor elements when zooming in.

### 1. General Noise Filters
*   **Unnamed elements** without a Wikidata QID or Wikipedia link are filtered out entirely for `mining` and `industry` themes.
*   **Generic industrial zones** (`branch = industrial`) without an operator or Wikidata are skipped.
*   **Minor peaks** without Wikidata/Wikipedia are skipped if their elevation is below 2000m, and all peaks without both elevation and Wikidata are skipped.
*   **Short ridges** less than 0.005° (~500m) without Wikidata are skipped.

### 2. Importance Classifications
| Theme | Level 1 (Major) | Level 2 (Significant) | Level 3 (Minor) | Level 4 (Local) |
|---|---|---|---|---|
| **Natural Peaks** | Has Wikidata/WP and `ele` $\ge 2000$ | Has Wikidata/WP and `ele` $\ge 1500$, or no Wikidata and `ele` $\ge 2500$ | Has Wikidata/WP and `ele` $\ge 1000$, or no Wikidata and `ele` $\ge 2000$ | Has Wikidata/WP but no parsed elevation |
| **Natural Ridges** | Has Wikidata/WP and length $\ge 0.02^\circ$ | Has Wikidata/WP and length $< 0.02^\circ$, or no Wikidata and length $\ge 0.04^\circ$ | Others | — |
| **Landscape Labels** | Has Wikidata/Wikipedia | Others | — | — |
| **Mineral Resources** | Has Wikidata/WP, or gold/silver/salt/uranium commodity | Coal, iron_ore, oil, gas, copper commodity | Others | — |
| **Industry Sites** | Has Wikidata/WP, or `power_nuclear` | Other power plants, or major works (steel, chemical, cement, paper) | Others (food, wood, textile, works_other, industrial) | — |

---

## Wikidata cache

All themes share a single committed cache at
`data/raw/wikidata_de_labels.json` (CC0, small).  The cache is additive:
a QID resolved for one theme run is available to all subsequent runs.  The
file is safe to commit — it doesn't contain PII and grows slowly.
