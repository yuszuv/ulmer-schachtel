# QField Export (Basic v1)

Two ways to get the project onto the device:

- **Option A – `build-qfield` (recommended):** Automated script builds a
  self-contained 2-file package from the desktop project. No plugin, no manual
  copying. Use for primarily **read-only** use (viewing markers and routes).
- **Option B – full QFieldSync workflow:** The plugin handles the complete export
  including a self-rendered **offline base map**. Required for offline maps without
  manual tile preparation and for **editing + syncing back** from the field.

If you only need to read the map and don't need an offline base map, use Option A.

## Option A (recommended): `build-qfield`

QField opens `.qgz` projects natively. The script builds a clean, reproducible
2-file package and places it in `qfield/current/` — which Syncthing syncs to the
device.

### Prerequisites

- GeoJSON data is current (re-run `uv run reiseplan-fetch` if routes changed).
- Data bundle is built:

  ```bash
  uv run reiseplan-cli build-gpkg
  ```

- The desktop project `qgis/reiseplan.qgz` is saved with **relative paths**
  (*Project → Properties → General* → Paths "relative").
- Styles are embedded in the project (loaded with *All Categories*, project saved).

### Procedure

```bash
uv run reiseplan-cli build-qfield
```

This creates two files in `qfield/current/`:
- `reiseplan.qgz` — project file with datasources rewritten to the GPKG
- `reiseplan.gpkg` — data bundle (all four layers in EPSG:3844)

Syncthing picks up the changes and syncs them to the device automatically.
Open `qfield/current/` in QField and tap `reiseplan.qgz`.

> **Custom output folder:** `uv run reiseplan-cli build-qfield --out ~/some/path`

> **How it works (good to know once):** `.qgz` is a ZIP file containing a
> `.qgs` project XML. The desktop project references GeoJSON via relative paths
> (`../data/processed/xxx.geojson`). `build-qfield` opens the ZIP, rewrites
> those paths to `./reiseplan.gpkg|layername=xxx`, and creates a new ZIP. The
> original `qgis/reiseplan.qgz` is never modified.

### Verify on device

Toggle layers visible, check labels, tap one marker of each type:
- one POI → HTML card with name / category / priority / notes
- one station → HTML card with name / city
- one route line → HTML card with timetable data
- the ℹ marker → legend / usage hints

If no HTML card appears: reload styles in QGIS with *All Categories*, re-save
`reiseplan.qgz`, run `build-qfield` again.

> Base map: Basic v1 starts without raster tiles (saves storage). Optionally
> generate MBTiles offline later and copy them alongside, or use Option B.

## Documentation in QField (Map Tips & info markers)

Documentation travels **inside the project** — no separate files, no internet
needed.

- **Map Tips:** All four layers (POIs, stations, route lines, info marker) carry
  an HTML card shown on identify (Identify tool / finger tap). The HTML is defined
  in `qgis/styles/*.qml` (category *Map Tips*) and embedded at `.qgz` save time —
  requires that styles were loaded **with all categories** (see
  [01_qgis_setup.md](01_qgis_setup.md), step 5).
- **"About this map" marker:** the ℹ point (`info_markers`) near the centre of
  Romania is the usage/legend help — tap it for symbol explanation, navigation
  hints, and the Danube Delta / rail note.

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
- Missing Map Tips (HTML card does not appear on tap):
  - Styles must be loaded with *All Categories* in QGIS, not just "Symbology".
- Layers not visible:
  - Check scale-dependent visibility in Layer Properties.
- Diacritics / special characters:
  - Keep file encoding UTF-8.
- `AssertionError` during QFieldSync export:
  - Project was not saved → save as `.qgz` first (see Option B, step 2).
