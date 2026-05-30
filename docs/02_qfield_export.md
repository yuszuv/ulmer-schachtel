# QField Export (Basic v1)

Two ways to get the project onto the device:

- **Option A – copy GPKG directly:** For primarily **read-only** use (viewing
  markers and routes). No plugin needed, just copy two files.
- **Option B – full QFieldSync workflow:** The plugin handles the complete export
  including a self-rendered **offline base map**. Required for offline maps without
  manual tile preparation and for **editing + syncing back** from the field.

If you only need to read the map and don't need an offline base map, use Option A.

## Option A (recommended): copy GPKG directly

QField opens `.qgz` projects natively — no packaging step, no nesting, just two
files.

### Prerequisites

- Data bundle built: `uv run reiseplan-cli build-gpkg`
  → `data/processed/reiseplan.gpkg` (all four layers in one file).
- Project built in QGIS from this GPKG and saved as `.qgz`
  (see [01_qgis_setup.md](01_qgis_setup.md)).
- **Relative paths** used when saving
  (*Project → Properties → General* → Paths "relative").
  Styles (symbology + labels) are automatically embedded in the `.qgz` —
  you **do not** need to copy the separate `.qml` files.

### Procedure

1. Transfer these two files to the device (same folder, so the relative path
   resolves), e.g. via USB/MTP, Syncthing, or cloud:
   - `qgis/projects/v1.qgz`
   - `data/processed/reiseplan.gpkg`
2. Open the folder in QField and tap the `.qgz`.
3. Toggle layers visible, check labels, tap markers
   (`name`, `category`, `notes`).
4. Optionally enable GNSS to see your own position relative to the routes.

> Base map: Basic v1 starts without raster tiles (saves storage). Optionally
> generate MBTiles offline later and copy them alongside.

## Documentation in QField (Map Tips & info markers)

Documentation travels **inside the project** — no separate files, no internet
needed.

- **Map Tips:** Tap a marker or route line → QField shows a formatted HTML card
  on identify (POI: name, category, priority, notes; station: name + city; route:
  name, from → to, tags). The HTML lives in `qgis/styles/*.qml` (category
  *Map Tips*) and is embedded at `.qgz` save time — requires that styles were
  loaded **with all categories** (see [01_qgis_setup.md](01_qgis_setup.md), step 5).
- **"About this map" marker:** the ℹ point (`info_markers`) near the centre of
  Romania is the usage/legend help — tap it for symbol explanation, navigation
  hints, and the Danube Delta / rail note.

> On the device, tap one POI, one station, one route, and the ℹ marker and
> verify that the HTML card appears. If not: reload styles in QGIS with *All
> Categories*, re-save the `.qgz`, and re-transfer.

## Option B: full QFieldSync plugin workflow

The QFieldSync plugin handles the **complete** path to the device: it bundles
the project + data, optionally renders an **offline base map**, and produces a
self-contained package. Use this when you:

- want the base map **offline** (the plugin generates MBTiles itself — no manual
  tile fetching),
- want to **edit and sync back** from the field, or
- only want to take a sub-area of interest.

> ⚠️ **Choose a target folder outside the project folder** (e.g.
> `~/qfield_export/v1`). QFieldSync copies everything project-relevant into the
> target folder on each run — if the target is *inside* the project tree, each
> run nests inside the previous one (`qfield/qfield/qfield/…`).

### Step 1: install the plugin

*Plugins → Manage and Install Plugins → "QFieldSync" → Install.*

### Step 2: configure the project

1. **Save** the project first (otherwise `AssertionError` — QFieldSync needs a
   `.qgz`/`.qgs` filename).
2. `Plugins → QFieldSync → Configure Current Project`.
3. Set layer action:
   - `poi_destinations`: `Offline editing` if you plan to edit in the field,
     otherwise `Copy`
   - `rail_stations` / `rail_lines` / `info_markers`: `Copy`
     (read-only is sufficient)
   - XYZ / online base map: `Keep existing` (stays online) — or replace with
     an offline base map (step 3).

### Step 3 (optional): generate an offline base map

This way you don't need to source MBTiles manually — QFieldSync renders them
during packaging:

1. In the same configuration dialog open the **Base map** section.
2. Enable **Create base map**.
3. Select the **map theme** or layer of the desired base map as the source (e.g.
   the XYZ OSM or CARTO map from [01_qgis_setup.md](01_qgis_setup.md)).
4. Set the level of detail:
   - **Map units per pixel**: smaller = sharper, but larger file.
   - **Tile size**: the default (usually 1024 px) is sufficient.
5. Limit the extent to the travel area to keep the package small.

> **Internet required at export time:** QFieldSync downloads the tiles from the
> online source during packaging. On the device the map is then available offline.

### Step 4: package and transfer

1. `Plugins → QFieldSync → Package for QField`, target folder **outside** the
   repo (e.g. `~/qfield_export/v1`).
2. Let the package build — it contains the project, all layers, and optionally
   the offline base map.
3. Transfer the **entire target folder** to the device (USB/MTP, Syncthing,
   cloud) and open it in QField.
4. If `Offline editing` was enabled: sync changes back later via
   `Plugins → QFieldSync → Synchronize`.

## Common pitfalls

- Missing symbols:
  - Apply styles in the project and re-save the `.qgz` — they travel with it.
- Layers not visible:
  - Check scale-dependent visibility in Layer Properties.
- Diacritics / special characters:
  - Keep file encoding UTF-8.
- `AssertionError` during QFieldSync export:
  - Project was not saved → save as `.qgz` first (see Option B, step 2).
