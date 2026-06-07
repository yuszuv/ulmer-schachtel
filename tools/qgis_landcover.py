"""Load and style the land-cover layer for the Ulmer Schachtel project.

Run from QGIS Python Console:
  **Plugins → Python Console → Show Editor → open this file → Run**

What it does (idempotent — safe to re-run)
------------------------------------------
1. Creates a **"Landbedeckung"** layer group above "Terrain".
2. Loads ``data/processed/landcover.geojson`` (CORINE or WorldCover).
3. Applies flat atlas-palette categorised symbology keyed on
   ``landuse_class`` (8 categories: arable/vineyard/orchard/pasture/forest/
   grassland/barren/wetland/water/urban) with subtle 60 % opacity fills.
4. Sets scale visibility: 1:500 000 … 1:8 000 000.

Prerequisites:  run ``uv run reiseplan-cli fetch-landcover`` first.
Attribution: EEA/Copernicus CORINE Land Cover or ESA WorldCover.
"""

from pathlib import Path

from qgis.core import (
    Qgis,
    QgsProject,
    QgsVectorLayer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsFillSymbol,
)
from qgis.PyQt.QtGui import QColor

GROUP_NAME   = "Landbedeckung"
INSERT_BEFORE = "Terrain"
LAYER_NAME   = "Landbedeckung"

# Atlas palette for land-cover categories (fill + outline).
# Muted, semi-transparent fills so vector layers show through.
_CATEGORY_COLOURS: dict[str, tuple[str, str]] = {
    "arable":    ("#e8d5a3", "#c8b580"),
    "vineyard":  ("#d4c070", "#b4a050"),
    "orchard":   ("#c0cc6a", "#a0ac4a"),
    "pasture":   ("#d4e8b0", "#b4c890"),
    "forest":    ("#8ab87a", "#6a9860"),
    "grassland": ("#c8e0a0", "#a8c080"),
    "barren":    ("#d8cdb8", "#b8ad98"),
    "wetland":   ("#a8c8d8", "#88a8b8"),
    "water":     ("#88b4d0", "#6894b0"),
    "urban":     ("#c8b4a8", "#a89488"),
}

SCALE_LANDCOVER = (8_000_000, 500_000)
_OPACITY = 0.60


def _make_fill(fill_hex: str, outline_hex: str) -> QgsFillSymbol:
    sym = QgsFillSymbol.createSimple({
        "color":         fill_hex,
        "outline_color": outline_hex,
        "outline_width": "0.1",
    })
    sym.setOpacity(_OPACITY)
    return sym


def _style_landcover(layer: QgsVectorLayer) -> None:
    """Categorised renderer: one fill per landuse_class."""
    categories = []
    for cls, (fill, outline) in _CATEGORY_COLOURS.items():
        cat = QgsRendererCategory(
            cls,
            _make_fill(fill, outline),
            cls,  # label
        )
        categories.append(cat)

    # Catch-all
    categories.append(QgsRendererCategory(
        None,
        _make_fill("#cccccc", "#aaaaaa"),
        "(sonstige)",
    ))

    renderer = QgsCategorizedSymbolRenderer("landuse_class", categories)
    layer.setRenderer(renderer)
    layer.setLabelsEnabled(False)


def add_landcover_layer() -> None:
    project = QgsProject.instance()

    # Bootstrap sys.path to import qgis_helpers
    import sys
    _pf = Path(project.fileName()) if project.fileName() else None
    _rd = next((p for p in [_pf.parent] + list(_pf.parents) if (p / "data" / "processed").is_dir()), None) if _pf else None
    if _rd and str(_rd / "tools") not in sys.path:
        sys.path.append(str(_rd / "tools"))

    import qgis_helpers

    repo_dir, data_dir, raster_dir, styles_dir = qgis_helpers.get_repo_paths(project)

    group = qgis_helpers.get_or_create_group(
        project, GROUP_NAME, insert_before=INSERT_BEFORE
    )

    fname = "landcover.geojson"
    path  = data_dir / fname
    if not path.exists():
        print(f"  ⚠ Datei fehlt: {path}")
        print("    Erst ausführen: uv run reiseplan-cli fetch-landcover")
        return

    qgis_helpers.remove_layers_by_name(project, LAYER_NAME)

    layer = QgsVectorLayer(str(path), LAYER_NAME, "ogr")
    if not layer.isValid():
        print(f"  ⚠ Layer ungültig: {LAYER_NAME}")
        return

    _style_landcover(layer)
    layer.setScaleBasedVisibility(True)
    layer.setMinimumScale(float(SCALE_LANDCOVER[0]))
    layer.setMaximumScale(float(SCALE_LANDCOVER[1]))

    project.addMapLayer(layer, False)
    group.addLayer(layer)
    print(f"  + {LAYER_NAME}  ←  {fname}")
    print(f"\n'{GROUP_NAME}' eingerichtet.")
    print("→ Strg+S um das Projekt zu speichern.")


add_landcover_layer()

try:
    iface.mapCanvas().refreshAllLayers()  # noqa: F821
except NameError:
    pass
