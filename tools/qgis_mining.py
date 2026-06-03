"""Load and style the mineral-resources layer for the Ulmer Schachtel project.

Run from QGIS Python Console:
  **Plugins → Python Console → Show Editor → open this file → Run**
  (or paste the whole file into the console).

Needs the running QGIS application context (``qgis.core`` / ``iface``);
not a standalone script.  Open + save the project first so relative paths
can be resolved.

What it does (idempotent — safe to re-run)
------------------------------------------
1. Creates a **"Bodenschätze"** layer group below "Relief / Landschaft".
2. Loads ``data/processed/mineral_resources.geojson``.
3. Applies rule-based piktogram symbology keyed on the ``commodity`` field:
   coal → black square, iron_ore → rust-red circle, salt → white octagon,
   gold → yellow star, oil/gas → black circle (petroleum), stone/gravel/clay
   → grey triangle, other → brown diamond.
4. Labels named features with a small brown italic name label.
5. Sets scale visibility: 1:500 000 … 1:6 000 000.

Attribution: OSM © ODbL 1.0.  Wikidata German names CC0.
"""

from pathlib import Path

from qgis.core import (
    Qgis,
    QgsProject,
    QgsVectorLayer,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling,
    QgsRuleBasedRenderer,
    QgsMarkerSymbol,
)
from qgis.PyQt.QtGui import QColor, QFont

# ---------------------------------------------------------------------------
# Colour + typography constants (shared with qgis_natural_features.py)
# ---------------------------------------------------------------------------

BROWN      = QColor(107, 79, 42, 255)
WHITE_200  = QColor(255, 255, 255, 200)

GROUP_NAME   = "Bodenschätze"
INSERT_AFTER = "Relief / Landschaft"
LAYER_NAME   = "Mineralvorkommen"

# commodity → (shape, fill colour hex, size mm)
_COMMODITY_SYMBOLS: dict[str, tuple[str, str, float]] = {
    "coal":     ("square",     "#1a1a1a", 2.4),
    "iron_ore": ("circle",     "#8b3a1a", 2.4),
    "salt":     ("octagon",    "#e8e8e8", 2.4),
    "gold":     ("star",       "#d4a017", 2.8),
    "silver":   ("star",       "#c0c0c0", 2.6),
    "oil":      ("circle",     "#333333", 2.2),
    "gas":      ("circle",     "#666666", 2.2),
    "copper":   ("diamond",    "#b87333", 2.4),
    "lead":     ("diamond",    "#708090", 2.2),
    "zinc":     ("diamond",    "#9fa8a3", 2.2),
    "manganese":("pentagon",   "#4a4a6a", 2.2),
    "bauxite":  ("triangle",   "#c0804a", 2.2),
    "chromite": ("triangle",   "#3a5a3a", 2.2),
    "uranium":  ("circle",     "#00aa00", 2.2),
    "stone":    ("triangle",   "#9a9080", 2.0),
    "gravel":   ("triangle",   "#b8a880", 2.0),
    "clay":     ("triangle",   "#c0a890", 2.0),
}
_DEFAULT_SYMBOL = ("diamond", "#8b7355", 1.8)  # "other" / unknown

SCALE_MINING = (6_000_000, 0)


# ---------------------------------------------------------------------------
# Text format helpers (minimal — mirrors qgis_natural_features.py)
# ---------------------------------------------------------------------------

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


def _with_buffer(fmt: QgsTextFormat, size_mm: float = 0.5) -> QgsTextFormat:
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setColor(WHITE_200)
    buf.setSize(size_mm)
    buf.setSizeUnit(Qgis.RenderUnit.Millimeters)
    fmt.setBuffer(buf)
    return fmt


# ---------------------------------------------------------------------------
# Symbology
# ---------------------------------------------------------------------------

def _make_symbol(shape: str, colour_hex: str, size_mm: float) -> QgsMarkerSymbol:
    return QgsMarkerSymbol.createSimple({
        "name":          shape,
        "color":         colour_hex,
        "outline_style": "no",
        "size":          str(size_mm),
        "size_unit":     "MM",
    })


def _style_mining(layer: QgsVectorLayer) -> None:
    """Rule-based renderer: one rule per commodity class + catch-all rule."""
    root = QgsRuleBasedRenderer.Rule(None)

    for commodity, (shape, colour, size) in _COMMODITY_SYMBOLS.items():
        rule = QgsRuleBasedRenderer.Rule(_make_symbol(shape, colour, size))
        rule.setLabel(commodity)
        rule.setFilterExpression(f'"commodity" = \'{commodity}\'')
        root.appendChild(rule)

    # Catch-all for unknown / empty commodity
    default_shape, default_colour, default_size = _DEFAULT_SYMBOL
    default_rule = QgsRuleBasedRenderer.Rule(
        _make_symbol(default_shape, default_colour, default_size)
    )
    default_rule.setLabel("other")
    default_rule.setIsElse(True)
    root.appendChild(default_rule)

    layer.setRenderer(QgsRuleBasedRenderer(root))

    # Labels: name when available
    pal = QgsPalLayerSettings()
    pal.fieldName = 'coalesce("name_de", "name")'
    pal.isExpression = True
    pal.placement = 0  # OverPoint
    pal.setFormat(_with_buffer(_text_fmt("Sans Serif", 5.0, italic=True)))
    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def add_mining_layer() -> None:
    project = QgsProject.instance()
    if not project.fileName():
        print("  ⚠ Projekt nicht gespeichert — erst speichern, dann erneut ausführen.")
        return

    qgis_dir = Path(project.fileName()).parent
    data_dir  = qgis_dir.parent / "data" / "processed"
    root      = project.layerTreeRoot()

    anchor    = root.findGroup(INSERT_AFTER)
    insert_idx = (root.children().index(anchor) + 1) if anchor else 0

    old = root.findGroup(GROUP_NAME)
    if old:
        root.removeChildNode(old)
    group = root.insertGroup(insert_idx, GROUP_NAME)

    fname = "mineral_resources.geojson"
    path  = data_dir / fname
    if not path.exists():
        print(f"  ⚠ Datei fehlt: {path}")
        print("    Erst ausführen: uv run reiseplan-cli fetch-mining")
        return

    for dup in project.mapLayersByName(LAYER_NAME):
        project.removeMapLayer(dup.id())

    layer = QgsVectorLayer(str(path), LAYER_NAME, "ogr")
    if not layer.isValid():
        print(f"  ⚠ Layer ungültig: {LAYER_NAME}")
        return

    _style_mining(layer)
    layer.setScaleBasedVisibility(True)
    layer.setMinimumScale(float(SCALE_MINING[0]))
    layer.setMaximumScale(float(SCALE_MINING[1]))

    project.addMapLayer(layer, False)
    group.addLayer(layer)
    print(f"  + {LAYER_NAME}  ←  {fname}")
    print(f"\n'{GROUP_NAME}' eingerichtet.")
    print("→ Strg+S um das Projekt zu speichern.")


add_mining_layer()

try:
    iface.mapCanvas().refreshAllLayers()  # noqa: F821  (only in QGIS context)
except NameError:
    pass
