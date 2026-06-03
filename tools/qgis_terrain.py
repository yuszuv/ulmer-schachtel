"""Load and style terrain layers for the Ulmer Schachtel project.

Run from QGIS Python Console:
  **Plugins → Python Console → Show Editor → open this file → Run**

What it does (idempotent — safe to re-run)
------------------------------------------
1. Creates a **"Terrain"** layer group at the bottom of the layer tree
   (below all other groups so raster layers render underneath vectors).
2. Loads three layers from the project data directory:

   - **Höhenlinien**   contours.geojson    (LineString, ele attribute)
   - **Hillshade**     terrain_hillshade.tif  (raster, rendered under vectors)
   - **DEM**           terrain_dem.tif        (raster, hidden by default)

3. Applies atlas-style symbology:

   - Hillshade:    multiply blend mode, 70 % opacity, no labels
   - Höhenlinien:  thin brown lines + italic ele-label at 100 m major / 500 m index
   - DEM:          hidden by default (single-band pseudo-colour for reference)

4. Sets scale visibility for Höhenlinien: 1:250 000 … 1:3 000 000.

Prerequisites:  run ``uv run reiseplan-cli fetch-terrain`` first.
"""

from pathlib import Path

from qgis.core import (
    Qgis,
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling,
    QgsLineSymbol,
)
from qgis.PyQt.QtGui import QColor, QFont

BROWN      = QColor(107, 79, 42, 180)
WHITE_180  = QColor(255, 255, 255, 180)

GROUP_NAME   = "Terrain"
SCALE_CONTOURS = (3_000_000, 250_000)


def _text_fmt(family: str, size_pt: float, italic: bool = False) -> QgsTextFormat:
    fmt = QgsTextFormat()
    f = QFont(family)
    f.setPointSizeF(size_pt)
    f.setItalic(italic)
    fmt.setFont(f)
    fmt.setSize(size_pt)
    fmt.setSizeUnit(Qgis.RenderUnit.Points)
    fmt.setColor(BROWN)
    return fmt


def _with_buffer(fmt: QgsTextFormat, size_mm: float = 0.4) -> QgsTextFormat:
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setColor(WHITE_180)
    buf.setSize(size_mm)
    buf.setSizeUnit(Qgis.RenderUnit.Millimeters)
    fmt.setBuffer(buf)
    return fmt


def _style_contours(layer: QgsVectorLayer) -> None:
    """Thin brown contour lines + italic ele-label."""
    sym = QgsLineSymbol.createSimple({
        "line_color": "107,79,42,140",
        "line_width": "0.15",
        "line_style": "solid",
    })
    layer.renderer().setSymbol(sym)

    pal = QgsPalLayerSettings()
    pal.fieldName = (
        'CASE WHEN "ele" % 500 = 0 THEN to_string("ele") || \' m\''
        ' WHEN "ele" % 100 = 0 THEN to_string("ele")'
        ' ELSE \'\' END'
    )
    pal.isExpression  = True
    pal.placement     = 3   # Curved
    pal.repeatDistance     = 60.0
    pal.repeatDistanceUnit = Qgis.RenderUnit.Points
    pal.setFormat(_with_buffer(_text_fmt("Sans Serif", 5.0, italic=True)))
    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)


def add_terrain_layers() -> None:
    project = QgsProject.instance()
    if not project.fileName():
        print("  ⚠ Projekt nicht gespeichert — erst speichern, dann erneut ausführen.")
        return

    qgis_dir  = Path(project.fileName()).parent
    repo_dir  = qgis_dir.parent
    proc_dir  = repo_dir / "data" / "processed"
    raster_dir = repo_dir / "data" / "raster"
    root      = project.layerTreeRoot()

    old = root.findGroup(GROUP_NAME)
    if old:
        root.removeChildNode(old)
    # Insert at the bottom so rasters render below all vector groups.
    group = root.insertGroup(len(root.children()), GROUP_NAME)

    loaded = []

    # --- Höhenlinien (vector contours) ---
    contours_path = proc_dir / "contours.geojson"
    if contours_path.exists():
        for dup in project.mapLayersByName("Höhenlinien"):
            project.removeMapLayer(dup.id())
        clayer = QgsVectorLayer(str(contours_path), "Höhenlinien", "ogr")
        if clayer.isValid():
            _style_contours(clayer)
            clayer.setScaleBasedVisibility(True)
            clayer.setMinimumScale(float(SCALE_CONTOURS[0]))
            clayer.setMaximumScale(float(SCALE_CONTOURS[1]))
            project.addMapLayer(clayer, False)
            group.addLayer(clayer)
            loaded.append("Höhenlinien")
    else:
        print(f"  ⚠ Höhenlinien fehlen: {contours_path}")

    # --- Hillshade (raster) ---
    hs_path = raster_dir / "terrain_hillshade.tif"
    if hs_path.exists():
        for dup in project.mapLayersByName("Hillshade"):
            project.removeMapLayer(dup.id())
        rl = QgsRasterLayer(str(hs_path), "Hillshade")
        if rl.isValid():
            # Multiply blend so it darkens underlying colours.
            rl.setBlendMode(13)  # 13 = Multiply in Qt blend mode enum
            rl.setOpacity(0.7)
            project.addMapLayer(rl, False)
            node = group.addLayer(rl)
            # Move hillshade to bottom of group so it renders first.
            group.setItemVisibilityChecked(False)  # tmp
            group.setItemVisibilityChecked(True)
            loaded.append("Hillshade")
    else:
        print(f"  ⚠ Hillshade fehlt: {hs_path}")

    # --- DEM (raster, hidden by default) ---
    dem_path = raster_dir / "terrain_dem.tif"
    if dem_path.exists():
        for dup in project.mapLayersByName("DEM"):
            project.removeMapLayer(dup.id())
        dem = QgsRasterLayer(str(dem_path), "DEM")
        if dem.isValid():
            project.addMapLayer(dem, False)
            dem_node = group.addLayer(dem)
            # Hide DEM by default (reference only)
            dem_node.setItemVisibilityChecked(False)
            loaded.append("DEM (versteckt)")
    else:
        print(f"  ⚠ DEM fehlt: {dem_path}")

    if loaded:
        print(f"'{GROUP_NAME}' mit {len(loaded)} Layern eingerichtet: "
              + ", ".join(loaded))
        print("→ Strg+S um das Projekt zu speichern.")
    else:
        print("  ⚠ Keine Terrain-Layer geladen.")
        print("    Erst ausführen: uv run reiseplan-cli fetch-terrain")


add_terrain_layers()

try:
    iface.mapCanvas().refreshAllLayers()  # noqa: F821
except NameError:
    pass
