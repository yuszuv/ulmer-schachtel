# Curved Labels via a Manual Label-Line Layer

## Goal

Place flowing, curved names (e.g. empire names like *Österreich-Ungarn*) across
polygon areas. QGIS only supports the **Curved** placement mode on **line**
geometries — not on polygons or points. The cleanest, most controllable result
(cartographer standard for historical maps) is a dedicated, invisible
**label-line layer**: one hand-drawn line per name, styled invisible, labelled
with curved placement.

> For *single* labels per merged area (one empire = one label, straight text),
> see `historische_reiche.geojson` and the "Label Largest Part Only" multipart
> option instead. This guide is specifically about the **curved** look.

## Steps (QGIS 4.0, English UI)

### 1. Create a new line layer

**Layer ▸ Create Layer ▸ New GeoPackage Layer…**

- **File name:** e.g. `data/label_lines.gpkg`
- **Geometry type:** `LineString`
- **CRS:** same as the other source layers — usually `EPSG:4326`
- Add a field: **Name** `label`, **Type** Text (String) → **Add to Fields List**
- **OK**

### 2. Draw the guide lines

1. Select the layer → **Toggle Editing** (pencil, `Ctrl+E`).
2. **Add Line Feature**.
3. Draw a gentle line through each area, **left to right** in reading direction,
   where the name should run (a slight arc looks best).
4. **Right-click** to finish → enter `label` = `Österreich-Ungarn` (etc.).
5. Repeat per area.

> Use few vertices with a soft curve — many small vertices make the text wavy.

### 3. Make the line invisible

Layer Styling ▸ **Symbology** ▸ Simple Line → **Stroke color** alpha 0, or
**Pen style: No Pen**. The line is only a carrier for the text.

### 4. Enable curved labelling

Layer Styling ▸ **Labels** ▸ **Single labels**:

- **Value:** `label`
- Tab **Placement** → **Mode: Curved**
  - **Allow upside-down labels:** *never*
  - **Maximum angle between curved characters:** reduce inner/outer (~20°/20°)
    so the text does not break at kinks
  - Placement **On line**, **Distance 0** for centred text
- Tab **Text:** choose font/size; increase **Letter spacing** for the historical
  look.

### 5. Save

- **Toggle Editing** off → confirm **Save** (writes into the GeoPackage).
- Optional GeoJSON for the project: right-click the layer →
  **Export ▸ Save Features As… ▸ GeoJSON** into `data/`.

## Alternatives (not used here)

- **Auto centreline** via a Geometry Generator label geometry — fast, no manual
  drawing, but the path is often crooked and hard to control.
- **Along the polygon border** — *Processing ▸ Polygons to lines*, then curved
  labelling on the line layer. Use when the name should trace the border rather
  than fill the area.
