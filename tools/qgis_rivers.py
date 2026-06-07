"""Load and style the river layers for the Ulmer Schachtel project.

Run from QGIS Python Console:
  **Plugins → Python Console → Show Editor → open this file → Run**
  (or paste the whole file into the console).

Needs the running QGIS application context (``qgis.core`` / ``iface``);
not a standalone script.  Open + save the project first so relative paths
can be resolved.

What it does (idempotent — safe to re-run)
------------------------------------------
1. Creates a **"Gewässer"** layer group directly above "Hintergrundkarten".
2. Loads up to four GeoJSON layers from ``data/processed/`` (missing files
   are skipped gracefully — fetch what you need first):

   Natural Earth resolution pyramid (overview → detail):
   - **Flüsse 110m**  rivers_major_110m.geojson  (LineString, coarse overview)
   - **Flüsse 50m**   rivers_major_50m.geojson   (LineString, medium scales)
   - **Flüsse 10m**   rivers_major_10m.geojson   (LineString, close zoom)

   OSM delta detail:
   - **Donaudelta-Gewässer**  rivers_delta.geojson  (LineString, fine detail)

3. Each layer is styled and assigned an exclusive scale band so QGIS switches
   cleanly between resolutions rather than drawing all at once:

     Band            Scale range               Visibility
     ─────────────────────────────────────────────────────
     110m overview   1:8 000 000 and beyond    minimumScale 0,  maximumScale 8M
     50m medium      1:2 000 000 – 1:8 000 000 minimumScale 8M, maximumScale 2M
     10m detail      1:600 000 – 1:2 000 000   minimumScale 2M, maximumScale 600k
     Delta OSM       1:600 000 and closer       minimumScale 600k, maximumScale 0

   Within each NE layer, ``scalerank`` drives rule-based line widths and label
   visibility (the finest detail per-layer), so the pyramid gives both
   correct generalisation *and* progressive detail within each band.

Colours (from zimmermann.gpl)
------------------------------
  Wasser Blaugrün (Hauptfluss)  #7bbccc  → QColor(123, 188, 204)
  Wasser Nebenfluss             #9ecfdb  → QColor(158, 207, 219)
  Flussname Text                #3a7a8c  → QColor(58,  122, 140)
"""

from pathlib import Path

from qgis.core import (
    Qgis,
    QgsProject,
    QgsRuleBasedRenderer,
    QgsSingleSymbolRenderer,
    QgsVectorLayer,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling,
    QgsLineSymbol,
)
from qgis.PyQt.QtGui import QColor, QFont

# ---------------------------------------------------------------------------
# Colour constants (Zimmermann-Karten palette)
# ---------------------------------------------------------------------------

WATER_MAJOR   = QColor(123, 188, 204, 220)  # Wasser Blaugrün (Hauptfluss) #7bbccc
WATER_MINOR   = QColor(158, 207, 219, 200)  # Wasser Nebenfluss #9ecfdb
WATER_TEXT    = QColor(58,  122, 140, 255)  # Flussname Text #3a7a8c
WHITE_200     = QColor(255, 255, 255, 200)  # halo buffer

# ---------------------------------------------------------------------------
# Exclusive scale bands per resolution layer
#
# QGIS semantics:
#   minimumScale = outer limit (denominator); 0 = no limit (always show farther out)
#   maximumScale = inner limit (denominator); 0 = no limit (always show closer in)
#   A layer is HIDDEN when scale denominator > minimumScale OR < maximumScale.
# ---------------------------------------------------------------------------

# (display_name, filename, min_scale, max_scale)
_NE_LAYERS = [
    ("Flüsse 110m", "rivers_major_110m.geojson",        0,  8_000_000),
    ("Flüsse 50m",  "rivers_major_50m.geojson",  8_000_000,  2_000_000),
    ("Flüsse 10m",  "rivers_major_10m.geojson",  2_000_000,    600_000),
]

_DELTA_LAYER = ("Donaudelta-Gewässer", "rivers_delta.geojson", 600_000, 0)

# Group name and position
GROUP_NAME    = "Gewässer"
INSERT_BEFORE = "Hintergrundkarten"  # rivers go directly above basemaps


# ---------------------------------------------------------------------------
# Text format helpers
# ---------------------------------------------------------------------------

def _text_fmt(
    family: str,
    size_pt: float,
    italic: bool = False,
    color: QColor = WATER_TEXT,
) -> QgsTextFormat:
    fmt = QgsTextFormat()
    f = QFont(family)
    f.setPointSizeF(size_pt)
    f.setItalic(italic)
    fmt.setFont(f)
    fmt.setSize(size_pt)
    fmt.setSizeUnit(Qgis.RenderUnit.Points)
    fmt.setColor(color)
    return fmt


def _with_buffer(
    fmt: QgsTextFormat,
    color: QColor = WHITE_200,
    size_mm: float = 0.5,
) -> QgsTextFormat:
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setColor(color)
    buf.setSize(size_mm)
    buf.setSizeUnit(Qgis.RenderUnit.Millimeters)
    fmt.setBuffer(buf)
    return fmt


# ---------------------------------------------------------------------------
# Stylers
# ---------------------------------------------------------------------------

def _make_line_sym(color: QColor, width_mm: float) -> QgsLineSymbol:
    return QgsLineSymbol.createSimple({
        "line_color": color.name(QColor.NameFormat.HexArgb),
        "line_width": str(width_mm),
        "line_width_unit": "MM",
        "capstyle": "round",
        "joinstyle": "round",
    })


def _style_ne_rivers(layer: QgsVectorLayer) -> None:
    """Rule-based renderer keyed on NE ``scalerank`` + curved river-name labels.

    scalerank 0-1: major international rivers (Danube, large tributaries)
    scalerank 2-3: large national rivers
    scalerank 4-6: medium rivers
    scalerank 7+ : small tributaries

    The rules are the same across all three NE layers; within each layer
    scalerank naturally reflects the level of detail present in that dataset.
    """
    root_rule = QgsRuleBasedRenderer.Rule(None)
    rules_cfg = [
        # (label, filter_expr, color, width_mm)
        ("Hauptstrom (rank 0–1)",  '"scalerank" <= 1', WATER_MAJOR, 1.2),
        ("Großfluss (rank 2–3)",   '"scalerank" <= 3', WATER_MAJOR, 0.8),
        ("Mittelfluss (rank 4–6)", '"scalerank" <= 6', WATER_MINOR, 0.5),
        ("Nebenfluss (rank 7+)",   "ELSE",              WATER_MINOR, 0.25),
    ]
    for label, expr, color, width in rules_cfg:
        rule = QgsRuleBasedRenderer.Rule(
            _make_line_sym(color, width),
            0, 0,       # per-rule scale limits disabled; layer handles scale band
            expr, label,
        )
        root_rule.appendChild(rule)
    layer.setRenderer(QgsRuleBasedRenderer(root_rule))

    pal = QgsPalLayerSettings()
    pal.fieldName = (
        "CASE "
        "  WHEN \"scalerank\" <= 3 THEN \"name\" "
        "  WHEN (@map_scale <= 2000000 AND \"scalerank\" <= 5) THEN \"name\" "
        "  ELSE NULL "
        "END"
    )
    pal.isExpression = True
    pal.placement            = Qgis.LabelPlacement.Curved
    pal.maxCurvedCharAngleIn  = 20.0
    pal.maxCurvedCharAngleOut = -20.0
    pal.repeatDistance        = 60.0
    pal.repeatDistanceUnit    = Qgis.RenderUnit.Points
    pal.setFormat(_with_buffer(_text_fmt("Sans Serif", 5.5, italic=True)))

    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    layer.setLabelsEnabled(True)


def _style_delta(layer: QgsVectorLayer) -> None:
    """Uniform fine blue line for OSM delta waterways (no labels at this scale)."""
    layer.setRenderer(QgsSingleSymbolRenderer(_make_line_sym(WATER_MINOR, 0.3)))
    layer.setLabelsEnabled(False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def add_rivers() -> None:
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

    # Layer order in legend = draw order (topmost = renders last = visually on top).
    # Delta OSM is finest detail, goes on top; 110m overview at bottom.
    layers_cfg = [
        (_DELTA_LAYER[0], _DELTA_LAYER[1], _style_delta,     _DELTA_LAYER[2], _DELTA_LAYER[3]),
        *[
            (name, fname, _style_ne_rivers, s_min, s_max)
            for name, fname, s_min, s_max in _NE_LAYERS
        ],
    ]

    loaded = []
    for name, fname, style_fn, s_min, s_max in layers_cfg:
        qgis_helpers.remove_layers_by_name(project, name)

        path = data_dir / fname
        if not path.exists():
            print(f"  – {fname} fehlt (übersprungen) → uv run reiseplan-cli fetch-rivers")
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
        print("Maßstabbänder:")
        print("  Flüsse 110m   ← 1:8 000 000 und kleiner (Übersicht)")
        print("  Flüsse 50m    ← 1:2 000 000 – 1:8 000 000 (Mittel)")
        print("  Flüsse 10m    ← 1:600 000 – 1:2 000 000 (Detail)")
        print("  Donaudelta    ← 1:600 000 und größer (Feindetail)")
        print("→ Strg+S um das Projekt zu speichern.")
    else:
        print("  ⚠ Keine Layer geladen — zuerst: uv run reiseplan-cli fetch-rivers")


add_rivers()

try:
    iface.mapCanvas().refreshAllLayers()  # noqa: F821  (only in QGIS context)
except NameError:
    pass
