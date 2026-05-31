# Ulmer Schachtel – QGIS Setup (Basic v1)

## Goal

A simple QGIS project containing:

- POIs (key destinations)
- Rail stations
- Broad route corridors
- Muted historical-style symbology (parchment + sepia)

## Steps

1. Start QGIS and create a new project.
2. Set the project CRS to `EPSG:3844 (Stereo70)` — the official Romanian national
   projection, eliminates the distortion present in 4326. GeoJSON data stays in
   4326; QGIS reprojects on-the-fly.
3. Load data directly from the GeoJSON sources (EPSG:4326, versioned source of truth):
   - `data/processed/poi_destinations.geojson`
   - `data/processed/rail_stations.geojson`
   - `data/processed/rail_lines.geojson`
   - `data/processed/info_markers.geojson` (ℹ "About this map" – usage/legend help)

   > **Why GeoJSON, not GPKG?** The desktop project reads GeoJSON directly so
   > that any change to the data (re-running `uv run reiseplan-fetch`) is immediately
   > visible in QGIS without a `build-gpkg` step. The GPKG is a generated bundle
   > *only* for QField export — see [02_qfield_export.md](02_qfield_export.md).

4. Layer order (top to bottom):
   - `info_markers`
   - `poi_destinations`
   - `rail_stations`
   - `rail_lines`
5. Apply styles (*Layer Properties → Style → Load Style…*):
   - `poi_destinations` → `qgis/styles/poi_destinations.qml`
   - `rail_lines` → `qgis/styles/rail_lines.qml`
   - `rail_stations` → `qgis/styles/rail_stations.qml`
   - `info_markers` → `qgis/styles/info_markers.qml`
   > **Use "All Categories"** when loading: the `.qml` files carry **Symbology**,
   > **Labeling**, *and* **Map Tips** (HTML card on tap). Loading only "Symbology"
   > silently drops the other two categories.
   >
   > For `info_markers` additionally set the display field to `title`
   > (*Layer Properties → Display*).
   >
   > **Connection data on `rail_lines`:** The lines carry the fields from
   > `data/processed/timetable.csv` (`from_city`, `to_city`, `days`, `dep_time`,
   > `arr_time`, `duration`, `via`, `train`) as attributes — visible in the
   > attribute table and via *Identify Features*. They appear once times have been
   > entered and the data rebuilt (`uv run reiseplan-fetch --offline`, then
   > `build-gpkg`).
6. Load a base map via the **QuickMapServices** plugin:
   - Install: *Plugins → Manage and Install Plugins → "QuickMapServices"*
   - Load: *Web → QuickMapServices → OSM → OSM Standard* (or Stamen Toner for
     a more historical look)
   - QGIS reprojects the tiles (EPSG:3857) to Stereo70 automatically.
   - *Project → Properties → General* → background colour `#f3ecd5` (applies when
     no tile layer is active).
   > Labels (POI names 8pt bold sepia, station names 6.5pt grey) are already
   > embedded in the QML files — no manual step required.
   > Additional useful base maps (rail overlay, relief, satellite, historical) as
   > one-click imports: see [Additional base maps](#additional-base-maps).
7. Save the project:
   - `qgis/reiseplan.qgs` (source format; XML, git-diffable)
   - Ensure **relative paths** are used when saving
     (*Project → Properties → General* → Paths "relative").
   - Styles are embedded at save time. For QField you do **not** need to copy
     the `.qml` files — use `uv run tools/export_qfield.py` instead
     (see [02_qfield_export.md](02_qfield_export.md)).

## Additional base maps

Beyond OSM Standard, other base maps are useful depending on purpose. All are
prepared as XYZ connections in `qgis/xyz_connections.xml`.

**One-click import:** Browser panel → right-click *XYZ Tiles* →
*Load Connections…* → select `qgis/xyz_connections.xml`. All maps then appear
under *XYZ Tiles* and can be loaded as layers by double-clicking (place them
below your own vector layers).

| Map | Purpose |
|---|---|
| **CARTO Positron / Voyager** | Light, clean everyday base map — quieter than OSM Standard, lets the sepia markers stand out. |
| **OpenRailwayMap** | Rail overlay (lines, electrification, stations) — layer semi-transparently over your own routes to check corridors against real infrastructure. |
| **OpenTopoMap / ESRI World Hillshade** | Terrain/relief — explains the alignment through the Carpathians (Brașov, Sighișoara). |
| **ESRI World Imagery** | Satellite — useful for the Danube Delta, where the water channels (Sulina, Sf. Gheorghe, Letea) are the main feature. |
| **Arcanum 2nd Military Survey** | Historical base map for the Fancy stage (1806–1869). Requires a Referer header (configured in the XML). Details: [STYLE_TODO_FANCY.md](STYLE_TODO_FANCY.md). |

> **Offline / QField:** All services require an internet connection. For use in
> the field you will need to cache the chosen base map tiles as MBTiles/GeoPackage
> raster — otherwise they will be empty offline.

> **Tip:** instead of toggling base maps by hand, `tools/qgis_setup_scales.py`
> wires three of them (CARTO / Arcanum / ESRI) into automatic scale bands — see
> [Helper scripts](#helper-scripts-python-console) below.

## Helper scripts (Python Console)

Four PyQGIS scripts under `tools/` automate the otherwise click-heavy setup. Run
them from *Plugins → Python Console* (open the editor, load the file, **Run** — or
paste the contents). All are **idempotent** (safe to re-run) and look layers up by
name, skipping any they can't find. Afterwards **save the project (Ctrl+S)** so the
changes land in the `.qgs`.

**Recommended order to build the project from scratch** (open an empty project,
*Save As* `qgis/reiseplan.qgs` first):

1. `qgis_bootstrap.py` — CRS, vector layers, styles, canvas, paths
2. `qgis_basemaps.py` — load the XYZ base maps
3. `qgis_setup_scales.py` — scale bands + scale visibility
4. `qgis_bookmarks.py` — spatial bookmarks

### `tools/qgis_bootstrap.py` — project skeleton from source files

Reproduces the manual setup (steps 2–7 above) so the `.qgs` is buildable from code:

- sets the project **CRS** to `EPSG:3844` (avoids the 4326 trap),
- loads the **four vector layers** from `data/processed/*.geojson` with the German
  display names the rest of the toolchain expects (Info-Marker, POI, Bahnhöfe,
  Bahn-Linien), grouped Guide / Bahn and ordered top→bottom,
- applies the **QML styles** (`loadNamedStyle`, all categories),
- sets the **info_markers display field** to `title`,
- sets the **canvas background** `#f3ecd5` and **relative paths**.

It deliberately does *not* load base maps or set scales/bookmarks — that's the
next three scripts (it prints the order on completion).

### `tools/qgis_basemaps.py` — load the XYZ base maps

Reads `qgis/xyz_connections.xml` and turns every entry into a raster layer in a
group **"Hintergrundkarten"** at the bottom of the tree (behind your own data),
all **unchecked**. Layer names match the XML exactly, which is what
`qgis_setup_scales.py` looks up for the scale bands. Replaces the manual
*Browser → XYZ Tiles → Load Connections… → double-click each* dance.

> The Arcanum surveys need a Referer header (passed as `http-header:referer`). If
> Arcanum tiles return 403, verify that parameter against your QGIS version.

### `tools/qgis_bookmarks.py` — spatial bookmarks

Adds 10 **project** bookmarks (stored in the `.qgs`, so they are versioned and
travel with the project):

- **Übersicht** group: whole-Romania extent + Siebenbürgen (Transylvania) core.
- **Magistralen** group: one bookmark per CFR main line M200–M900, framed to that
  line's bounding box — for quick QC and jumping between routes.

Extents are computed from `data/processed/rail_lines.geojson` (stored as literals
in the script, +8 % margin per axis). View them via *View → Show Spatial Bookmarks*.

### `tools/qgis_setup_scales.py` — scale-dependent rendering

Turns the flat "everything visible at every zoom" map into a layered one. It
(1) reloads the QML styles onto the four vector layers (`loadNamedStyle`, all
categories — also sidesteps the "All Categories" trap), (2) sets layer scale
visibility so markers vanish at continental zoom, and (3) turns the basemap stack
into scale bands, switching off the opaque competitors, so the right map shows
automatically per zoom.

Resulting visibility hierarchy (scale `1:X`, appears as you zoom *in*):

| Layer / base map | visible from | to | mechanism |
|---|---|---|---|
| CARTO Positron (calm, wide) | ∞ | 1:4 000 000 | layer band |
| Arcanum 2nd Survey (historical working range) | 1:4 000 000 | 1:25 000 | layer band |
| ESRI World Imagery (sharp, close) | 1:25 000 | close | layer band (Arcanum hand-off) |
| Bahn-Linien (backbone) | always | – | — |
| rail_lines `M…` labels | 1:6 000 000 | – | QML `scaleVisibility` |
| POI `dracula_city` + `city` | 1:6 000 000 | – | rule-based renderer |
| POI `danube_delta` | 1:3 000 000 | – | rule-based renderer |
| POI labels | 1:3 000 000 | – | QML `scaleVisibility` |
| info_markers (ℹ) | 1:8 000 000 | – | QML + layer band |
| Bahnhöfe (markers + labels) | 1:1 500 000 | – | layer band + QML |

Why this fixes the three symptoms it was built for:

- **Continental clutter** (7 POI + 36 stations + all labels piling up at Europe
  zoom): markers and labels are scale-gated, so a wide view shows only CARTO +
  rail lines.
- **Arcanum blur** past its native tiles (`zmax=14` ≈ 1:34 000): the band hands
  off to sharp ESRI imagery below 1:25 000.
- **Manual base-map toggling**: the three bands switch automatically; the other
  base maps stay available (just unchecked) as a manual fallback.

**Tuning:** thresholds live in `LAYER_SCALE` (this script) and in
`build_marker_styles.py` (POI `scale_max` per category, label `scale_max`). Change a
value, re-run `build_marker_styles.py` if a QML is affected, then re-run this script.

## Colour palette (muted sepia, already in the QML files)

- Map canvas background: warm off-white `#f3ecd5`
- Route lines: sepia brown `#6b4f2a`, label along line
- Station markers: dark grey `#4c4c4c`, small circles
- POI categories:
  - `dracula_city`: dark red (circle)
  - `city`: sepia brown (square)
  - `danube_delta`: muted teal (triangle)

> The full historical look (raster base map, cartouche, serif typography) follows
> in the Fancy stage — see [STYLE_TODO_FANCY.md](STYLE_TODO_FANCY.md).
