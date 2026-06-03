# 11 — Terrain & Land Cover

## Overview

Two raster-based atlas layers complete the thematic data integration:

| Layer | Source | Output |
|-------|--------|--------|
| **Terrain** | Copernicus DEM GLO-30 | `data/raster/terrain_dem.tif`<br>`data/raster/terrain_hillshade.tif`<br>`data/processed/contours.geojson` |
| **Land cover** | CORINE Land Cover 2018 | `data/processed/landcover.geojson` |

Both use GDAL (3.13+) via thin subprocess wrappers in `tools/reiseplan/raster.py`.

---

## Terrain — Copernicus DEM GLO-30

### Data source

**Copernicus DEM GLO-30** — publicly accessible via AWS HTTPS, no login required.

```
Tile URL pattern:
  https://copernicus-dem-30m.s3.amazonaws.com/
      Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM/
      Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM.tif
```

Tiles are downloaded automatically and cached in `data/raw/dem/`.

**Attribution required:**
> © ESA/Copernicus. Contains modified Copernicus DEM data.

License: Copernicus Data and Information Policy (open access).

### Usage

```bash
# Download DEM tiles + generate hillshade + 100 m contours
uv run reiseplan-cli fetch-terrain

# Offline rebuild (no download — uses cached tiles)
uv run reiseplan-cli fetch-terrain --offline

# Custom contour interval
uv run reiseplan-cli fetch-terrain --interval 200

# Only DEM + hillshade, skip contours
uv run reiseplan-cli fetch-terrain --no-contours

# Only DEM, skip both
uv run reiseplan-cli fetch-terrain --no-hillshade --no-contours
```

### Pipeline

```
data/raw/dem/*.tif     (1°×1° GLO-30 tiles, auto-downloaded)
        │
        ▼ gdalbuildvrt
data/raw/dem.vrt       (virtual mosaic)
        │
        ▼ gdalwarp -t_srs EPSG:3844 -te <ROI bbox>
data/raster/terrain_dem.tif
        │
        ├── gdaldem hillshade -z 2 -combined
        │         ▼
        │   data/raster/terrain_hillshade.tif
        │
        └── gdal_contour -i 100
                  ▼
            data/processed/contours.geojson  (EPSG:4326)
```

### QGIS styling

Run `tools/qgis_terrain.py` in the QGIS Python Console.  It loads three layers:

- **Hillshade** — raster, Multiply blend mode, 70 % opacity (background)
- **Höhenlinien** — thin brown contour lines + curved ele-labels
- **DEM** — hidden by default (for reference / colour-relief derivation)

---

## Land Cover — CORINE Land Cover 2018

### Data source

**CORINE Land Cover 2018, v2020_20u1** — European Environment Agency.

⚠ **Manual one-time download required** (free Copernicus account):

1. Go to: https://land.copernicus.eu/pan-european/corine-land-cover/clc2018
2. Click **"CLC 2018 — vector"** → download `U2018_CLC2018_V2020_20u1.gpkg`
3. Place it at: `data/raw/corine/U2018_CLC2018_V2020_20u1.gpkg`

**Attribution required:**
> © European Environment Agency (EEA) / Copernicus Land Monitoring Service.
> CORINE Land Cover, freely available under the Copernicus Data Policy.

### Usage

```bash
# Clip + reclassify (requires manual CORINE download)
uv run reiseplan-cli fetch-landcover

# Alternative: ESA WorldCover 2021 (no login — see below)
uv run reiseplan-cli fetch-landcover --source worldcover
```

### CORINE → Atlas category mapping

The 44 CLC classes are reclassified to 8 broad categories:

| Atlas category | CLC codes | Colour |
|----------------|-----------|--------|
| arable | 211–213, 241–244 | pale yellow `#e8d5a3` |
| vineyard | 221 | golden `#d4c070` |
| orchard | 222–223 | yellow-green `#c0cc6a` |
| pasture | 231 | light green `#d4e8b0` |
| forest | 311–313 | green `#8ab87a` |
| grassland | 321–324 | pale green `#c8e0a0` |
| barren | 331–335 | grey `#d8cdb8` |
| wetland | 411–423 | blue-grey `#a8c8d8` |
| water | 511–523 | blue `#88b4d0` |
| urban | 111–142 | warm grey `#c8b4a8` |

### ESA WorldCover 2021 (no-login alternative)

WorldCover 2021 (10 m resolution) is available on AWS as Cloud-Optimised
GeoTIFFs, no login required.  The `--source worldcover` path is not yet
automated (requires tile download + reclassification of the 11 ESA classes).
Until then, use CORINE for the authoritative result.

### QGIS styling

Run `tools/qgis_landcover.py` in the QGIS Python Console.  The layer renders
as categorised polygons with flat, semi-transparent atlas-palette fills.

---

## GDAL wrapper API (`raster.py`)

```python
from reiseplan.raster import buildvrt, warp_clip, hillshade, contours, translate

buildvrt(inputs, out)          # gdalbuildvrt
warp_clip(src, dst, **kwargs)  # gdalwarp (clip + reproject)
hillshade(dem, out, **kwargs)  # gdaldem hillshade
contours(dem, out, **kwargs)   # gdal_contour
translate(src, dst, **kwargs)  # gdal_translate
```

All functions call `shutil.which` first and exit with a helpful message if
the GDAL tool is not found (consistent with `packaging.GpkgBuilder`).
