"""Slope-based terrain overlay for the Ulmer Schachtel atlas.

Run from QGIS Python Console:
  **Plugins → Python Console → Show Editor → open this file → Run**

Prerequisite: terrain_dem.tif must exist under data/raster/.
Run first if missing:
  uv run reiseplan-cli fetch-terrain

What it does (idempotent — safe to re-run)
------------------------------------------
1. Generates data/raster/terrain_slope.tif from terrain_dem.tif (GDAL slope,
   degrees, Z-factor 1.0 — EPSG:3844 is metric so no correction needed).
2. Adds a "Slope-Overlay" raster layer with a Zimmermann-palette classified
   colour ramp:
     0–8°   → transparent           (Câmpia Română, Donauebene)
     8–22°  → #e8d8a8 semi-opaque   (Hügelland / Subkarpaten)
     22°+   → #d4c080 semi-opaque   (Karpaten-Hauptkamm / Hochgebirge)
3. Sets Multiply blending mode so the hillshade beneath stays plastically
   visible — slope tinting accentuates relief, not drowns it.
4. Inserts the layer into the "Terrain" group (created if absent), directly
   above the existing Hillshade layer.

Layer stack (top → bottom, within Terrain group)
  Höhenlinien    (contours.geojson, vector — already in project)
  Slope-Overlay  ← this script
  Hillshade      (terrain_hillshade.tif, Multiply)
  DEM            (terrain_dem.tif, hidden)

Threshold guidance for atlas scale 1:500 000 – 1:2 000 000
  Adjust _SLOPE_HILL and _SLOPE_MOUNTAIN below to taste.
  Current defaults: 8° / 22°.
"""

from pathlib import Path

from qgis import processing
from qgis.core import (
    Qgis,
    QgsColorRampShader,
    QgsLayerTreeLayer,
    QgsProject,
    QgsRasterLayer,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor

# ---------------------------------------------------------------------------
# Tunable thresholds (degrees)
# ---------------------------------------------------------------------------

_SLOPE_HILL     =  8.0   # below = Flachland (transparent)
_SLOPE_MOUNTAIN = 22.0   # above = Hochgebirge / Karpaten-Kamm

# Zimmermann palette (from zimmermann.gpl)
_COLOR_HILL     = QColor(232, 216, 168, 140)   # Mittelgebirge #e8d8a8, semi-opaque
_COLOR_MOUNTAIN = QColor(212, 192, 128, 165)   # Hochgebirge   #d4c080, semi-opaque

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

project = QgsProject.instance()

# Bootstrap sys.path to import qgis_helpers
import sys
_pf = Path(project.fileName()) if project.fileName() else None
_rd = next((p for p in [_pf.parent] + list(_pf.parents) if (p / "data" / "processed").is_dir()), None) if _pf else None
if _rd and str(_rd / "tools") not in sys.path:
    sys.path.append(str(_rd / "tools"))
import qgis_helpers

repo_dir, data_dir, raster_dir, styles_dir = qgis_helpers.get_repo_paths(project)

dem_path   = raster_dir / "terrain_dem.tif"
slope_path = raster_dir / "terrain_slope.tif"

if not dem_path.exists():
    print(f"  ⚠ DEM nicht gefunden: {dem_path}")
    print("    Zuerst ausführen: uv run reiseplan-cli fetch-terrain")
    raise SystemExit

# ---------------------------------------------------------------------------
# Step 1: Generate slope raster (skipped if already present)
# ---------------------------------------------------------------------------

if slope_path.exists():
    print(f"[cache]   Slope-Raster vorhanden: {slope_path.name}")
else:
    print("Berechne Hangneigung via GDAL …")
    processing.run("gdal:slope", {
        "INPUT":         str(dem_path),
        "BAND":          1,
        "SCALE":         1.0,    # EPSG:3844: Meter/Meter
        "AS_PERCENT":    False,
        "COMPUTE_EDGES": True,
        "ZEVENBERGEN":   False,
        "OUTPUT":        str(slope_path),
    })
    print(f"  → {slope_path.relative_to(repo_dir)}")

# ---------------------------------------------------------------------------
# Step 2: Load slope layer and apply classified colour ramp
# ---------------------------------------------------------------------------

qgis_helpers.remove_layers_by_name(project, "Slope-Overlay")

slope_layer = QgsRasterLayer(str(slope_path), "Slope-Overlay")
if not slope_layer.isValid():
    raise RuntimeError(f"Slope-Layer ungültig: {slope_path}")

shader_items = [
    # flat → transparent
    QgsColorRampShader.ColorRampItem(0.0,                 QColor(0, 0, 0, 0), "Flachland"),
    QgsColorRampShader.ColorRampItem(_SLOPE_HILL,         QColor(0, 0, 0, 0), f"< {_SLOPE_HILL}°"),
    # hills
    QgsColorRampShader.ColorRampItem(_SLOPE_HILL + 0.01,  _COLOR_HILL,        f"{_SLOPE_HILL}–{_SLOPE_MOUNTAIN}° Hügelland"),
    # mountains
    QgsColorRampShader.ColorRampItem(_SLOPE_MOUNTAIN,     _COLOR_MOUNTAIN,    f"> {_SLOPE_MOUNTAIN}° Hochgebirge"),
    QgsColorRampShader.ColorRampItem(90.0,                _COLOR_MOUNTAIN,    "Steilwand"),
]

ramp_shader = QgsColorRampShader()
ramp_shader.setColorRampType(QgsColorRampShader.Type.Discrete)
ramp_shader.setColorRampItemList(shader_items)

raster_shader = QgsRasterShader()
raster_shader.setRasterShaderFunction(ramp_shader)

slope_layer.setRenderer(
    QgsSingleBandPseudoColorRenderer(slope_layer.dataProvider(), 1, raster_shader)
)

# Multiply blend + 60% opacity — hillshade stays plastically visible beneath
qgis_helpers.set_multiply_blend_mode(slope_layer)
slope_layer.setOpacity(0.6)

# ---------------------------------------------------------------------------
# Step 3: Insert into "Terrain" group, above Hillshade
# ---------------------------------------------------------------------------

project.addMapLayer(slope_layer, False)

root  = project.layerTreeRoot()
group = root.findGroup("Terrain")
if group is None:
    group = root.insertGroup(len(root.children()), "Terrain")
    print("  Gruppe 'Terrain' neu erstellt.")

hs_node = next(
    (n for n in group.children() if n.name() == "Hillshade"),
    None,
)
insert_idx = group.children().index(hs_node) if hs_node else 0
group.insertChildNode(insert_idx, QgsLayerTreeLayer(slope_layer))

print(f"\nSlope-Overlay eingebunden ({_SLOPE_HILL}° / {_SLOPE_MOUNTAIN}° Schwellen).")
print("Layer-Reihenfolge: Höhenlinien > Slope-Overlay > Hillshade > DEM")
print("→ Schwellen anpassen: _SLOPE_HILL und _SLOPE_MOUNTAIN oben im Skript.")
print("→ Strg+S um das Projekt zu speichern.")

try:
    iface.mapCanvas().refreshAllLayers()  # noqa: F821
except NameError:
    pass
