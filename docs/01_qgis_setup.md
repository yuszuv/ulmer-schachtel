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
   > that any change to the data (re-running `fetch_cfr_data.py`) is immediately
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
   > entered and the data rebuilt (`fetch_cfr_data.py --offline`, then
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
   - `qgis/reiseplan.qgz`
   - Ensure **relative paths** are used when saving
     (*Project → Properties → General* → Paths "relative").
   - Styles are embedded into the `.qgz` at save time. For QField you do **not**
     need to copy the `.qml` files — use `build-qfield` instead
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
