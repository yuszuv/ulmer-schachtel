# Code Architecture: DDD + Four Patterns

This document explains the design decisions behind the Python codebase refactoring
(v0.2.0, May 2026).

---

## Why refactor?

The five original scripts under `tools/` were quick prototypes with no separation
of concerns:

| File | Lines | Problems |
|---|---|---|
| `reiseplan_cli.py` | 461 | data loading + Rich tables + GPKG + QField + argparse |
| `fetch_cfr_data.py` | 497 | line definitions + network + index + output |
| `build_site.py` | 636 | ~330 lines of embedded template string |
| `_paths.py`, `timetable.py` | 68 | helper files without a clear home |

The problem: understanding one function meant holding the entire context of a
500-line file in your head.

---

## Target structure: Domain-Driven Design (DDD)

DDD organises code around **domain language** (here: Romanian railways,
travel destinations, timetables) rather than technical layers.

```
tools/reiseplan/
  paths.py       ← path resolution (no domain knowledge)
  result.py      ← monads (pure error handling, no IO)
  domain.py      ← Value Objects (pure domain objects, no IO)
  catalog.py     ← static line data (pure domain data)
  repository.py  ← data access (GeoJSON/CSV)
  overpass.py    ← external service gateway
  ingest.py      ← use case (orchestration)
  packaging.py   ← infrastructure (GPKG/QField build)
  tables.py      ← presentation (Rich terminal)
  web.py         ← presentation (website)
  template.html  ← presentation (HTML template)
  cli.py         ← entry point (argparse)
```

### Layer rule

Imports must only point **inward** (toward the domain):

```
cli.py → tables.py, packaging.py  (presentation uses domain)
web.py → repository.py, domain.py
ingest.py → overpass.py, catalog.py, repository.py
overpass.py → domain.py, result.py
repository.py → domain.py, paths.py
domain.py → (nothing from the package)
result.py → (nothing from the package)
```

**Circular imports are forbidden.** `cli.py` imports `tables` and `packaging`,
but `tables` does **not** import `cli`.

---

## Pattern 1 – Command Registry (Decorator)

**Problem:** `build_parser()` was a long block that manually called `add_parser`,
`add_argument`, and `set_defaults` for every sub-command. It felt like
configuration, not program logic.

**Solution in `cli.py`:**

```python
# Infrastructure:
REGISTRY: list[_CommandSpec] = []

def command(name, *, help, json=False, args=None):
    def decorator(fn):
        REGISTRY.append(_CommandSpec(name=name, help=help, ...))
        return fn
    return decorator

# Registration:
@command("list-routes", help="Show all magistrale", json=True)
def _list_routes(args):
    tables.list_routes(args)

# Parser built from the registry:
def build_parser():
    for spec in REGISTRY:
        p = sub.add_parser(spec.name, ...)
        p.set_defaults(func=spec.handler)
```

**Key insight:** A decorator is a function that *returns* another function and
may have side effects (here: writing to the registry). The `@` syntax is just
syntactic sugar for `fn = command(...)(fn)`.

**Benefits:**
- Adding a new command = one decorated function, zero boilerplate
- The registry is inspectable at runtime (`tests/test_cli.py` uses this)
- Argument declarations live next to the handler, not 100 lines away

---

## Pattern 2 – Result/Maybe Monads

**Problem:** Error handling was scattered: `SystemExit` buried inside
`fetch_overpass()`, `None` returned from `resolve()`. Callers had no idea what
to expect.

**Solution in `result.py`:**

```python
# Maybe: a value that may be absent
some_coord = Some(Coordinate(26.07, 44.45))  # station found
no_coord   = Nothing                          # station not in OSM

if some_coord.is_some:
    lon = some_coord.unwrap().lon

# Result: an operation that may fail
data = load_or_fetch(offline=True)  # → Ok(dict) or Err("cache missing")
parsed = data.unwrap_or_exit()      # SystemExit on Err, dict on Ok
```

**Usage (deliberately sparse):**

| Function | Return type | Why |
|---|---|---|
| `OverpassGateway.fetch()` | `Result[dict]` | network/JSON errors are expected |
| `StationIndex.resolve()` | `Maybe[Coordinate]` | name not in OSM is a normal outcome |

**Key insight:** The monad pattern says: *failure and absence are values, not
exceptions.* `Nothing.map(fn)` never calls `fn` and propagates `Nothing` —
the caller must explicitly check `.is_some`. At the system boundary (in
`ingest.main()`) `.unwrap_or_exit()` translates back to `SystemExit`.

**Why not everywhere?** For internal errors (missing file, wrong GPKG paths)
`SystemExit` is still the right choice — failing loudly is better than a
silently half-assembled package.

---

## Pattern 3 – Repository

**Problem:** `json.load`, `csv.DictReader`, and path constants were scattered
across all files. `reiseplan_cli.py` knew `POI_PATH`, `build_site.py` had its
own copy of `STATIONS_PATH`, `fetch_cfr_data.py` had yet another set.

**Solution in `repository.py`:**

```python
# All path constants in one place:
POI_PATH       = PROCESSED / "poi_destinations.geojson"
ROUTES_PATH    = PROCESSED / "rail_lines.geojson"
TIMETABLE_PATH = PROCESSED / "timetable.csv"
...

# Data access as named functions / class:
def load_geojson(path: Path) -> dict: ...
def stops_for(route_id: str) -> list[dict]: ...

class TimetableRepository:
    def __init__(self, path: Path = TIMETABLE_PATH): ...
    def load(self) -> Timetable: ...     # returns domain objects
    def scaffold(self, magistralen): ... # idempotent, never overwrites
```

**Key insight:** The Repository pattern hides *how* data is stored behind a
domain-language API. Tests can pass a different `path` instance without needing
real files (`TimetableRepository(tmp_path / "t.csv")`).

**Difference from an ORM repository:** There is no database here, only files —
but the principle is identical: the rest of the code should not know *whether*
data lives in a CSV, a JSON, or a SQLite file.

---

## Rename: `Line` → `Magistrale`

In DDD this is called **Ubiquitous Language**: the same terms in code, docs, and
conversation. `Line` was a generic Python name. `Magistrale` is the term used in
the UI, in AGENTS.md, and throughout the project.

```python
# Before (fetch_cfr_data.py):
@dataclass(frozen=True)
class Line:
    ref: str
    ...

# After (domain.py):
@dataclass(frozen=True)
class Magistrale:
    ref: str
    ...
```

Further renames with the same motivation:
- `_rewrite_datasources` → `rewrite_datasources` (now public + testable)
- `build_index` → `StationIndex.from_overpass` (object instead of free function)
- `resolve` → `StationIndex.resolve` (method, not global)
- `b64` → `embed_svg` (what the function does, not how)
- `map_tip` → `maptip_block` (conventional function name)
- `labeling` → `labeling_block`

---

## Pattern 4 – Thematic-Layer Pipeline (Strategy + Registry)

**Problem:** Three new atlas themes (mining, industry, natural features)
share identical machinery: ROI tiling, Overpass fetch + cache, German-name
enrichment (Wikipedia/Wikidata), GeoJSON construction, attribution sidecar.
Copy-pasting `fetch_natural.py` (628 lines) three times would create an
untestable mess.

**Solution in `themes/` + `thematic.py`:**

```python
# Declare what to fetch and how to classify it:
SPEC = ThemeSpec(
    name="mining",
    roi=KUK_ROI,
    node_filters=("man_made=mineshaft", "man_made=petroleum_well", ...),
    area_filters=("landuse=quarry",),
    layers=(MINERAL_LAYER,),
    extra_props=lambda el, tags, opts: {"commodity": _commodity(tags)},
)

# Generic runner does the rest:
thematic.run(SPEC, offline=False)
```

The runner (`thematic.py`) wires together:
- `tiles.fetch_tiled` — tiled Overpass fetch + dedup + JSON cache
- `enrich.german_names` — de.wikipedia titles + Wikidata labels (shared additive caches)
- `_build_features` — element classification via `OutputLayer.accepts`
- `repository.write_json` — GeoJSON + attribution sidecar

**Pattern:** Strategy (each ThemeSpec declares its own query selectors,
classification logic, and property extraction) + Registry (a dict from name
→ ThemeSpec, populated at import time). The runner is the Template Method:
fixed sequence of steps, with variable plugs.

**New shared infrastructure:**

| Module | Extracted from | Content |
|--------|---------------|---------|
| `geo.py` | `fetch_natural.py` | `way_to_linestring`, `node_to_point`, `centroid_of`, `parse_ele`, `parse_population` |
| `enrich.py` | `fetch_natural.py` | `resolve_name_de`, `german_names` |
| `tiles.py` | `fetch_natural.py` | `BBox`, `tile_grid`, `fetch_tiled` |

**Also added (v0.3, June 2026):**
- `raster.py` — thin GDAL subprocess wrappers (`hillshade`, `contours`, `warp_clip`, …)
- `fetch_terrain.py` — Copernicus GLO-30 DEM → hillshade + contours
- `fetch_landcover.py` — CORINE Land Cover → reclassified GeoJSON

See `docs/data-and-layers/thematic-layers.md` and
`docs/data-and-layers/terrain-landcover.md`.

---

## Template extraction (`build_site.py` → `web.py` + `template.html`)

The HTML/CSS/JS template string (330 lines) was embedded in `build_site.py`,
burying the actual Python logic (70 lines).

Now:
- `template.html` — pure template, recognised as HTML by editors
- `web.py` — Python logic (`collect()`, `render()`, `build()`)

Loading:
```python
HERE = Path(__file__).resolve().parent
template = (HERE / "template.html").read_text(encoding="utf-8")
html = template.format(bg=BG_COLOR, legend=..., data_js=...)
```

The `{{`-escapes in the HTML (for CSS/JS braces) are intentional — that is the
`.format()` convention. A `{bg}` in the template is substituted; a `{{` becomes
a literal `{` in the output.

---

## QML builder: `Marker` dataclass + `qml_document()` wrapper

In `build_marker_styles.py` the POI icon table was a `dict` of tuples:

```python
# Before:
icons = {
    "0": ("dracula_city", "Dracula-Stadt", b64("poi_dracula.svg"), 7.5),
    ...
}
```

Now a `Marker` dataclass with expressive fields:
```python
markers = [
    Marker("0", "dracula_city", "Dracula-Stadt", "poi_dracula.svg", 7.5),
    ...
]
```

The shared `qml_document()` wrapper eliminates the duplicated DOCTYPE/header
structure from `build_poi()` and `build_stations()`.

**Important:** The **output is byte-identical** to the previous version —
that was the acceptance criterion. Verified via `git diff qgis/styles/*.qml`
after running the script: no diff.

---

## Acceptance criteria (all met)

```bash
# 131 tests green:
uv run --group dev pytest

# No data diffs after offline rebuild:
uv run reiseplan-fetch --offline
git diff --stat data/processed/   # → empty

# No QML diffs after style rebuild:
python qgis/styles/build_marker_styles.py
git diff --stat qgis/styles/*.qml  # → empty

# CLI works:
uv run reiseplan-cli list-routes
uv run reiseplan-cli timetable --json | python3 -m json.tool

# Website builds:
uv run reiseplan-site --out /tmp/site
```
