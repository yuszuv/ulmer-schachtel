"""Load and style the industry-sites layer for the Ulmer Schachtel project.

Run from QGIS Python Console:
  **Plugins → Python Console → Show Editor → open this file → Run**

What it does (idempotent — safe to re-run)
------------------------------------------
1. Creates an **"Industrie"** layer group below "Bodenschätze".
2. Loads ``data/processed/industry_sites.geojson``.
3. Applies rule-based symbology keyed on the ``branch`` field:
   power_hydro → blue circle, power_thermal → dark-grey circle,
   power_nuclear → orange circle, power_wind → blue arrow,
   steel/iron → rust triangle, chemical → green diamond,
   textile → purple square, food → warm-brown circle, etc.
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

BROWN      = QColor(107, 79, 42, 255)
WHITE_200  = QColor(255, 255, 255, 200)

GROUP_NAME   = "Industrie"
INSERT_AFTER = "Bodenschätze"
LAYER_NAME   = "Industriestandorte"

# branch → (shape, fill colour hex, size mm)
_BRANCH_SYMBOLS: dict[str, tuple[str, str, float]] = {
    "power_hydro":    ("circle",   "#4a7ab8", 2.6),
    "power_thermal":  ("circle",   "#404040", 2.6),
    "power_nuclear":  ("circle",   "#e08020", 2.6),
    "power_wind":     ("arrow",    "#6090c0", 2.4),
    "power_solar":    ("circle",   "#d4c020", 2.4),
    "power_other":    ("circle",   "#888888", 2.4),
    "steel":          ("triangle", "#8b3a1a", 2.6),
    "chemical":       ("diamond",  "#3a8a3a", 2.4),
    "textile":        ("square",   "#7a4a9a", 2.2),
    "paper":          ("square",   "#9a9070", 2.2),
    "food":           ("circle",   "#c07840", 2.2),
    "glass":          ("circle",   "#80c0d0", 2.2),
    "ceramics":       ("circle",   "#c09060", 2.2),
    "cement":         ("triangle", "#b0a890", 2.2),
    "wood":           ("triangle", "#7a5a30", 2.2),
    "works_other":    ("diamond",  "#7a6a5a", 2.0),
    "industrial":     ("square",   "#9a8a7a", 1.8),
}
_DEFAULT_SYMBOL = ("circle", "#888080", 1.8)

SCALE_INDUSTRY = (6_000_000, 0)


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


def _make_symbol(shape: str, colour_hex: str, size_mm: float) -> QgsMarkerSymbol:
    return QgsMarkerSymbol.createSimple({
        "name":          shape,
        "color":         colour_hex,
        "outline_style": "no",
        "size":          str(size_mm),
        "size_unit":     "MM",
    })


def _style_industry(layer: QgsVectorLayer) -> None:
    """Nested rule-based renderer: Top-level rules for importance scale gating, child rules for branch symbols."""
    # 1. Create root rule
    root = QgsRuleBasedRenderer.Rule(None)

    # 2. Define top-level importance rules
    # (importance_level, label, filter_expr, min_scale, max_scale)
    imp_rules_cfg = [
        (1, "Major Industry (Imp 1)", '"importance" = 1', 6_000_000, 0),
        (2, "Significant Industry (Imp 2)", '"importance" = 2', 2_000_000, 0),
        (3, "Minor Industry (Imp 3)", '"importance" = 3', 750_000, 0),
    ]

    for imp_val, label, expr, min_s, max_s in imp_rules_cfg:
        # Parent rule has no symbol itself, just filter and scale gate
        parent_rule = QgsRuleBasedRenderer.Rule(None, int(min_s), int(max_s), expr, label)
        
        # Add child rules for each branch matching this importance
        for branch, (shape, colour, size) in _BRANCH_SYMBOLS.items():
            child_rule = QgsRuleBasedRenderer.Rule(_make_symbol(shape, colour, size))
            child_rule.setLabel(branch)
            child_rule.setFilterExpression(f'"branch" = \'{branch}\'')
            parent_rule.appendChild(child_rule)
            
        # Catch-all child rule for "other"
        default_shape, default_colour, default_size = _DEFAULT_SYMBOL
        default_rule = QgsRuleBasedRenderer.Rule(_make_symbol(default_shape, default_colour, default_size))
        default_rule.setLabel("other")
        default_rule.setIsElse(True)
        parent_rule.appendChild(default_rule)
        
        root.appendChild(parent_rule)

    layer.setRenderer(QgsRuleBasedRenderer(root))

    # Labels: name when available, scale-dependent
    pal = QgsPalLayerSettings()
    pal.fieldName = (
        "CASE "
        "  WHEN \"importance\" = 1 OR "
        "       (@map_scale <= 2000000 AND \"importance\" = 2) OR "
        "       (@map_scale <= 750000 AND \"importance\" = 3) "
        "  THEN coalesce(\"name_de\", \"name\") "
        "  ELSE NULL "
        "END"
    )
    pal.isExpression = True
    pal.placement = Qgis.LabelPlacement.AroundPoint
    pal.setFormat(_with_buffer(_text_fmt("Sans Serif", 5.0, italic=True)))
    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)


def add_industry_layer() -> None:
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

    fname = "industry_sites.geojson"
    path  = data_dir / fname
    if not path.exists():
        print(f"  ⚠ Datei fehlt: {path}")
        print("    Erst ausführen: uv run reiseplan-cli fetch-industry")
        return

    for dup in project.mapLayersByName(LAYER_NAME):
        project.removeMapLayer(dup.id())

    layer = QgsVectorLayer(str(path), LAYER_NAME, "ogr")
    if not layer.isValid():
        print(f"  ⚠ Layer ungültig: {LAYER_NAME}")
        return

    _style_industry(layer)
    layer.setScaleBasedVisibility(True)
    layer.setMinimumScale(float(SCALE_INDUSTRY[0]))
    layer.setMaximumScale(float(SCALE_INDUSTRY[1]))

    project.addMapLayer(layer, False)
    group.addLayer(layer)
    print(f"  + {LAYER_NAME}  ←  {fname}")
    print(f"\n'{GROUP_NAME}' eingerichtet.")
    print("→ Strg+S um das Projekt zu speichern.")


add_industry_layer()

try:
    iface.mapCanvas().refreshAllLayers()  # noqa: F821
except NameError:
    pass
