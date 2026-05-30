# CLI Reference

The CLI is a secondary tool alongside QGIS:

- quick data inspection without the QGIS UI
- filtering by category or route
- compact stop sequence per magistrală (`overview`)
- connection overview with dep/arr/via (`timetable`)
- good entry point for future automation (import/validation)

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
