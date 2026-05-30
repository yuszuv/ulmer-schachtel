# CLI Reference

The CLI is a secondary tool alongside QGIS:

- quick data inspection without the QGIS UI
- filtering by category or route
- compact stop sequence per magistrală (`overview`)
- connection overview with dep/arr/via (`timetable`)
- building the GeoJSON → GPKG bundle (`build-gpkg`)
- building the QField export package (`build-qfield`)

For map editing, QGIS remains the primary tool.

## Tool

- Script: `tools/reiseplan_cli.py`
- External dependency: **rich** (tables, colours) — already in `pyproject.toml`
- Run via **uv** (`pyproject.toml` defines the entrypoint `reiseplan-cli`)

## Examples

```bash
uv run reiseplan-cli list-categories
uv run reiseplan-cli list-destinations --category dracula_city
uv run reiseplan-cli list-routes
uv run reiseplan-cli overview               # stop sequence per magistrală
uv run reiseplan-cli timetable              # connections (dep/arr/via) per magistrală
uv run reiseplan-cli show-route M300        # stop sequence for a single magistrală
```

All data commands accept `--json` for machine-readable output (pipe-friendly):

```bash
uv run reiseplan-cli timetable --json | jq '.[].route_id'
uv run reiseplan-cli show-route M300 --json
```

## Build commands

```bash
# Step 1: bundle GeoJSON sources into a GPKG (required before build-qfield)
uv run reiseplan-cli build-gpkg

# Step 2: create the QField package (2 files in qfield/current/)
uv run reiseplan-cli build-qfield

# Custom output folder:
uv run reiseplan-cli build-qfield --out ~/some/folder
```

`build-gpkg` requires **GDAL/ogr2ogr** in PATH (Arch: `pacman -S gdal`).

`build-qfield` opens `qgis/reiseplan.qgz` (a ZIP), rewrites the GeoJSON
datasource paths to point to the GPKG, and writes two files to
`qfield/current/`: `reiseplan.qgz` + `reiseplan.gpkg`. The original project
is never modified. See [02_qfield_export.md](02_qfield_export.md) for details.

Without installing the entrypoint:

```bash
uv run python tools/reiseplan_cli.py overview
```

> The CLI locates `data/processed` by walking up from the current directory —
> run from the repo root for simplest usage.

## Possible extensions (later)

- Import real GTFS timetables into `data/raw`
- Validate that all POIs have a nearby rail station
- Export a "daily suggestion" list for QField forms
