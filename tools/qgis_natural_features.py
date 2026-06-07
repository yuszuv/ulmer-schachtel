"""Load and style the natural-feature layers for the Ulmer Schachtel project.

Run from QGIS Python Console:
  **Plugins → Python Console → Show Editor → open this file → Run**
  (or paste the whole file into the console).

Needs the running QGIS application context (``qgis.core`` / ``iface``);
not a standalone script.  Open + save the project first so relative paths
can be resolved.

What it does (idempotent — safe to re-run)
------------------------------------------
1. Creates a **"Relief / Landschaft"** layer group below "Historisch".
2. Loads three GeoJSON layers from ``data/processed/``:

   - **Gebirgs-Kämme**       natural_ridges.geojson   (LineString)
   - **Berggipfel**           mountain_peaks.geojson   (Point)
   - **Gebirgsbezeichnungen** landscape_labels.geojson (Point)

3. Applies atlas-style symbology and labels:

   - Kämme:           invisible carrier + *curved* brown labels (placement=3)
   - Gipfel:          small brown ▲ marker + name / elevation label
   - Bezeichnungen:   invisible point + ALL-CAPS spaced brown labels

4. Sets scale visibility: all three layers show only at 1:500 000 … 1:6 000 000.

Fonts
-----
Ideal atlas font for landscape labels: **Garamontio Italic** (in fonts/).
Install the OTF files from ``fonts/`` and set ``_FONT_LANDSCAPE`` below.
Fallback is "Gelasio" (already in use by the Historische Reiche layer).
Ridges and peaks use "Sans Serif" (always available).
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
    QgsMarkerSymbol,
    QgsLineSymbol,
)
from qgis.PyQt.QtGui import QColor, QFont

# ---------------------------------------------------------------------------
# Colour + typography constants
# ---------------------------------------------------------------------------

BROWN      = QColor(107, 79, 42, 255)   # atlas brown — matches all other label layers
WHITE_220  = QColor(255, 255, 255, 220) # halo buffer, semi-transparent
BG_BUFF    = QColor(243, 236, 213, 160) # canvas background colour, lighter halo

# Font for ridge + peak labels (simple, matches existing rail-line labels)
_FONT_RIDGE = "Sans Serif"
_FONT_PEAK  = "Sans Serif"
# Font for large landscape labels — Garamontio Italic gives the best atlas look;
# replace with "Garamontio" once fonts/ is installed, or keep "Gelasio" as fallback.
_FONT_LANDSCAPE = "Gelasio"

# ---------------------------------------------------------------------------
# Scale visibility: show relief detail only at useful zoom levels
# ---------------------------------------------------------------------------

# (minimumScale, maximumScale) in QGIS semantics:
#   minimumScale = farthest-out limit (largest denominator, e.g. 1:6 000 000)
#   maximumScale = closest-in limit  (smallest denominator, e.g. 1:500 000)
#   0 = no limit
SCALE_RIDGES  = (6_000_000, 0)        # ridges: visible at all scales closer than 1:6M
SCALE_PEAKS   = (3_000_000, 0)        # peaks: only when zoomed in enough to read them
SCALE_LANDSC  = (10_000_000, 800_000) # landscape names: medium overview window

# Group name and position relative to "Historisch"
GROUP_NAME  = "Relief / Landschaft"
INSERT_AFTER = "Historisch"           # group goes directly below this one


# ---------------------------------------------------------------------------
# Text format helpers
# ---------------------------------------------------------------------------

def _text_fmt(
    family: str,
    size_pt: float,
    italic: bool = False,
    bold: bool = False,
    letter_spacing: float = 0.0,
    color: QColor = BROWN,
) -> QgsTextFormat:
    """Return a QgsTextFormat with the given properties (no buffer)."""
    fmt = QgsTextFormat()
    f = QFont(family)
    f.setPointSizeF(size_pt)
    f.setItalic(italic)
    f.setBold(bold)
    if letter_spacing:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, letter_spacing)
    fmt.setFont(f)
    fmt.setSize(size_pt)
    fmt.setSizeUnit(Qgis.RenderUnit.Points)
    fmt.setColor(color)
    return fmt


def _with_buffer(
    fmt: QgsTextFormat,
    color: QColor = WHITE_220,
    size_mm: float = 0.6,
) -> QgsTextFormat:
    """Add a halo buffer to an existing QgsTextFormat and return it."""
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setColor(color)
    buf.setSize(size_mm)
    buf.setSizeUnit(Qgis.RenderUnit.Millimeters)
    fmt.setBuffer(buf)
    return fmt


# ---------------------------------------------------------------------------
# Per-layer stylers
# ---------------------------------------------------------------------------

def _style_ridges(layer: QgsVectorLayer) -> None:
    """Invisible line carrier + curved atlas-brown labels.

    placement=3 is 'Curved' in QGIS (see reiseplan.qgs:2186 for the same
    setting on the Bahn-Linien layer).  maxCurvedCharAngleIn/Out control how
    tightly the letters may follow the curve.
    """
    # --- symbology: fully invisible carrier line ---
    sym = QgsLineSymbol.createSimple({"line_style": "no"})
    layer.renderer().setSymbol(sym)

    # --- labels ---
    pal = QgsPalLayerSettings()
    pal.fieldName = (
        "CASE "
        "  WHEN \"importance\" = 1 OR "
        "       (@map_scale <= 1500000 AND \"importance\" = 2) OR "
        "       (@map_scale <= 750000 AND \"importance\" = 3) "
        "  THEN coalesce(\"name_de\", \"name\") "
        "  ELSE NULL "
        "END"
    )
    pal.isExpression = True

    # placement=3 → Curved (line layers only)
    pal.placement            = Qgis.LabelPlacement.Curved
    pal.maxCurvedCharAngleIn  = 25.0
    pal.maxCurvedCharAngleOut = -25.0
    # repeat the label every 40 points along long ridges
    pal.repeatDistance     = 40.0
    pal.repeatDistanceUnit = Qgis.RenderUnit.Points

    fmt = _with_buffer(_text_fmt(_FONT_RIDGE, 6.5, letter_spacing=0.5))
    pal.setFormat(fmt)

    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)


def _style_peaks(layer: QgsVectorLayer) -> None:
    """Small brown ▲ marker using rule-based rendering based on importance and scale, plus scale-dependent labels."""
    # --- symbology: rule-based renderer ---
    from qgis.core import QgsRuleBasedRenderer
    
    base_sym = QgsMarkerSymbol.createSimple({
        "name":          "triangle",
        "color":         "107,79,42,180",
        "outline_style": "no",
        "size":          "1.6",
        "size_unit":     "MM",
    })
    
    root_rule = QgsRuleBasedRenderer.Rule(None)
    rules_cfg = [
        ("Major Peaks (Imp 1)", '"importance" = 1', 3_000_000, 0),
        ("Significant Peaks (Imp 2)", '"importance" = 2', 1_500_000, 0),
        ("Minor Peaks (Imp 3)", '"importance" = 3', 750_000, 0),
        ("Local Peaks (Imp 4)", '"importance" = 4', 300_000, 0),
    ]
    
    for label, expr, min_s, max_s in rules_cfg:
        rule = QgsRuleBasedRenderer.Rule(base_sym.clone(), int(min_s), int(max_s), expr, label)
        root_rule.appendChild(rule)
        
    renderer = QgsRuleBasedRenderer(root_rule)
    layer.setRenderer(renderer)

    # --- labels: name + elevation below, scale-dependent ---
    pal = QgsPalLayerSettings()
    pal.fieldName = (
        "CASE "
        "  WHEN \"importance\" = 1 OR "
        "       (@map_scale <= 1500000 AND \"importance\" = 2) OR "
        "       (@map_scale <= 750000 AND \"importance\" = 3) OR "
        "       (@map_scale <= 300000 AND \"importance\" = 4) "
        "  THEN coalesce(\"name_de\", \"name\") || "
        "       CASE WHEN \"ele\" IS NOT NULL THEN '\\n' || to_string(\"ele\") || ' m' ELSE '' END "
        "  ELSE NULL "
        "END"
    )
    pal.isExpression = True

    # placement=0 → OverPoint
    pal.placement = Qgis.LabelPlacement.AroundPoint

    fmt = _with_buffer(_text_fmt(_FONT_PEAK, 5.5))
    pal.setFormat(fmt)

    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)


def _style_landscape(layer: QgsVectorLayer) -> None:
    """Invisible point + ALL-CAPS strongly-spaced italic labels.

    Follows the style guide §2 (Territorien & Regionen): italic, all-caps,
    heavy letter-spacing ("Sperrung"), brown.  For the full atlas look switch
    _FONT_LANDSCAPE to "Garamontio" once fonts/ is installed.
    """
    # --- symbology: invisible point ---
    sym = QgsMarkerSymbol.createSimple({
        "name":          "circle",
        "color":         "0,0,0,0",
        "outline_style": "no",
        "size":          "0.1",
        "size_unit":     "MM",
    })
    layer.renderer().setSymbol(sym)

    # --- labels: upper-cased, strongly spaced, scale-dependent ---
    pal = QgsPalLayerSettings()
    pal.fieldName = (
        "CASE "
        "  WHEN \"importance\" = 1 OR "
        "       (@map_scale <= 3000000 AND \"importance\" = 2) "
        "  THEN upper(coalesce(\"name_de\", \"name\")) "
        "  ELSE NULL "
        "END"
    )
    pal.isExpression = True

    # placement=2 → Free (best for diffuse area labels)
    pal.placement = Qgis.LabelPlacement.Free

    fmt = _with_buffer(
        _text_fmt(_FONT_LANDSCAPE, 9.0, italic=True, letter_spacing=2.5),
        color=BG_BUFF,
        size_mm=1.0,
    )
    pal.setFormat(fmt)

    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def add_natural_features() -> None:
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
        project, GROUP_NAME, insert_after=INSERT_AFTER
    )

    # Layers in draw order: ridges bottom, peaks middle, landscape names on top.
    # In QGIS legend the topmost entry draws last (= on top).
    layers_cfg = [
        # (filename, display name, style function, (min_scale, max_scale))
        ("landscape_labels.geojson", "Gebirgsbezeichnungen", _style_landscape, SCALE_LANDSC),
        ("mountain_peaks.geojson",   "Berggipfel",           _style_peaks,     SCALE_PEAKS),
        ("natural_ridges.geojson",   "Gebirgs-Kämme",        _style_ridges,    SCALE_RIDGES),
    ]

    loaded = []
    for fname, name, style_fn, (s_min, s_max) in layers_cfg:
        qgis_helpers.remove_layers_by_name(project, name)

        path = data_dir / fname
        if not path.exists():
            print(f"  ⚠ Datenquelle fehlt: {path}")
            continue

        layer = QgsVectorLayer(str(path), name, "ogr")
        if not layer.isValid():
            print(f"  ⚠ Layer ungültig: {name}")
            continue

        style_fn(layer)

        layer.setScaleBasedVisibility(True)
        layer.setMinimumScale(float(s_min))
        layer.setMaximumScale(float(s_max))

        project.addMapLayer(layer, False)
        group.addLayer(layer)
        loaded.append(name)
        print(f"  + {name}  ←  {fname}")

    if loaded:
        print(f"\n'{GROUP_NAME}' mit {len(loaded)} Layern eingerichtet.")
        print("→ Strg+S um das Projekt zu speichern.")
        print()
        print("Hinweis: Für den vollen Atlas-Look die Fonts aus fonts/ installieren")
        print(f"  und _FONT_LANDSCAPE auf 'Garamontio' setzen (aktuell: '{_FONT_LANDSCAPE}').")
    else:
        print("  ⚠ Keine Layer geladen — Daten prüfen.")


add_natural_features()

try:
    iface.mapCanvas().refreshAllLayers()  # noqa: F821  (only in QGIS context)
except NameError:
    pass
