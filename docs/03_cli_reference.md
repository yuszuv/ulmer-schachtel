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

- Package: `tools/reiseplan/cli.py` (entry point `reiseplan-cli`, defined in `pyproject.toml`)
- External dependency: **rich** (tables, colours) — already in `pyproject.toml`
- Run via **uv**: `uv run reiseplan-cli <cmd>`

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
# One-shot canonical export (builds GPKG + packs everything):
uv run tools/export_qfield.py

# Custom output folder:
uv run tools/export_qfield.py --out ~/some/folder

# Or two-step via CLI:
uv run reiseplan-cli build-gpkg       # Step 1: bundle all vector layers into GPKG
uv run reiseplan-cli build-qfield     # Step 2: pack 3-file QField package
uv run reiseplan-cli build-qfield --out ~/some/folder
```

`build-gpkg` requires **GDAL/ogr2ogr** in PATH (Arch: `pacman -S gdal`).

`build-qfield` reads `qgis/reiseplan.qgs` + `qgis/reiseplan_attachments.zip`,
rewrites all datasource paths to local bundle references, and writes three files
to `qfield/current/`: `reiseplan.qgz` + `reiseplan.gpkg` + `arcanum2_ro_clip.tif`.
The original project is never modified. See [02_qfield_export.md](02_qfield_export.md) for details.

> The CLI locates `data/processed` by walking up from the current directory —
> run from the repo root for simplest usage.

## Possible extensions (later)

- Import real GTFS timetables into `data/raw`
- Validate that all POIs have a nearby rail station
- Export a "daily suggestion" list for QField forms
