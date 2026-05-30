# AGENTS.md – Ulmer Schachtel (Romania Travel Planner)

Guide for AI agents working in this repo. Keep it concise and aligned with existing conventions.

## What this is

A lightly historical-flavoured map application for planning a **rail trip through Romania**
(Dracula towns, Timișoara, Bucharest, Danube Delta). Main tool: **QGIS**, export target:
**QField**. A small **uv CLI** supports data work. Code language: **English**.

Maturity: **Basic v1**. Full vintage styling (historical raster base map, cartouche,
typography, day-by-day itinerary planning) is intentionally deferred to a later "Fancy"
stage — documented in `docs/STYLE_TODO_FANCY.md`.

## Data flow (important)

```
data/processed/*.geojson   ── versioned source of truth (EPSG:4326)
        │  uv run reiseplan-cli build-gpkg  (uses ogr2ogr → EPSG:3844)
        ▼
data/processed/reiseplan.gpkg   ── generated, GITIGNORED, single-file bundle
        ▼
QGIS project (qgis/projects/*.qgz)   ── styles + labels embedded
        ▼
QField (copy .qgz + .gpkg to device)
```

- **GeoJSON are the source**; the GPKG is a reproducible build artefact.
  Always make content changes in GeoJSON, then `build-gpkg`.
- `*.gpkg` is in `.gitignore` — **do not commit**.
- **Note:** The desktop project `qgis/reiseplan.qgz` loads GeoJSON **directly**
  via relative paths (`../data/processed/*.geojson`), **not** the GPKG. If you
  rename a GeoJSON file, update the path in the `.qgz` too (it is a ZIP containing
  `reiseplan.qgs`). The GPKG is only the bundle for QField export.
- **Connection times:** `data/processed/timetable.csv` is a **hand-maintained**
  source (one row per magistrală, real dep/arr/days/via). `fetch_cfr_data.py`
  creates it only as a scaffold template (if missing) and merges its fields into
  `rail_lines.geojson` as attributes (key: `route_id`). Entered times are never
  overwritten.

## Conventions

- **CRS:** Data is stored in `EPSG:4326` (GeoJSON standard). Project/GPKG CRS is
  `EPSG:3844` (Stereo70, Romanian national projection). Do not mix them up. See the
  CRS rationale block in `tools/fetch_cfr_data.py` for the reason GeoJSON stays 4326.
- **Encoding:** real UTF-8 diacritics (Brașov, Timișoara, București) — no ASCII
  transliteration (`Rumaenien`).
- **QGIS paths:** save projects with **relative** paths so `.qgz` + `.gpkg` can be
  copied together to a QField device.
- **Styles:** `qgis/styles/*.qml` carry symbology, **labelling** (POIs 8pt bold
  sepia, stations 6.5pt grey) **and Map Tips** (HTML card on tap, style category
  `MapTips`). When loading a style in QGIS use *Load Style → All Categories*,
  otherwise Map Tips are missing. Saving the `.qgz` embeds the styles — separate
  `.qml` files do not need to be copied to QField.
- **Colour palette (muted sepia):** background `#f3ecd5`, routes `#6b4f2a` dashed,
  stations `#4c4c4c`. POI categories: `dracula_city` dark red/circle,
  `city` sepia/square, `danube_delta` teal/triangle.

## CLI (`tools/reiseplan_cli.py`)

- Dependencies: **rich** (tables/colours) + **Python standard library**
  (argparse/csv/json + subprocess for `ogr2ogr`). No new deps in `pyproject.toml`
  without good reason.
- Run via **uv**: `uv run reiseplan-cli <cmd>` (entrypoint in `pyproject.toml`)
  or `uv run python tools/reiseplan_cli.py <cmd>`.
- Data directory is located by `find_repo_root()` (walks up from CWD) — run from
  the repo root.
- Commands: `list-routes`, `list-categories`, `list-destinations [--category]`,
  `show-route <id>`, `overview`, `timetable`, `build-gpkg`.
  All data commands accept `--json` for machine-readable output.
- `build-gpkg` requires **GDAL/ogr2ogr** in PATH (Arch: `pacman -S gdal`).

## Verification

```bash
uv run reiseplan-cli overview          # magistrale + stop sequences
uv run reiseplan-cli timetable         # connections (dep/arr/via) per magistrală
uv run reiseplan-cli list-routes       # M200–M900
uv run python -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('data/processed/*.geojson')]"
uv run --group dev pytest              # unit tests
```

QGIS/QField steps are manual and cannot be automated. Procedure in
`docs/01_qgis_setup.md` (setup) and `docs/02_qfield_export.md` (export).

## Directory layout

- `data/processed/` – GeoJSON (source) + `route_stops.csv` (generated stop sequences)
  + `timetable.csv` (hand-maintained connections with real times).
  `info_markers.geojson` is the in-app documentation (ℹ "About this map", legend).
- `data/raw/` – placeholder for GTFS / OSM raw data
- `data/reference/historical/` – historical map material (Fancy stage)
- `qgis/styles/` – `.qml` (symbology + labels + Map Tips)
- `qgis/projects/` – `.qgz` files (maintained directly in QGIS)
- `qgis/xyz_connections.xml` – XYZ base maps ready to import (OSM, CARTO,
  OpenRailwayMap, relief, satellite, Arcanum historical)
- `docs/` – `01_qgis_setup`, `02_qfield_export`, `03_cli_reference`,
  `04_web_pages`, `05_overpass_101`, `06_cfr_data_fetch`, `STYLE_TODO_FANCY`

## Git

- Conventional commits (`feat:` / `fix:` / `chore:`), imperative mood, optional issue key.
- **Never push automatically** — only on explicit request.
- Generated artefacts (`*.gpkg`, `qfield/`, `__pycache__/`, `.venv/`) stay untracked
  (see `.gitignore`).

## Data and travel assumptions

- Start/end city are deliberately open → multiple route options (M200–M900) rather
  than one fixed itinerary.
- **The Danube Delta is not reachable by rail:** the line ends at Tulcea; onward
  travel is by boat. Do not "optimise away" this note in data or docs.
- `timetable.csv` contains **real**, hand-maintained connections (one per magistrală);
  not-yet-entered times are left empty. Authoritative/current times:
  <https://mersultrenurilor.infofer.ro>. `route_stops.csv` carries **no** times.
