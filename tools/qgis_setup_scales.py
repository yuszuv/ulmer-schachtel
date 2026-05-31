"""Wire up scale-dependent rendering for the Ulmer Schachtel reiseplan.

Run this from inside QGIS: **Plugins → Python Console → Show Editor →** open this
file and hit *Run*, or paste the contents into the console. It needs the running
QGIS application context (``qgis.core`` / ``iface``); it is not standalone.

What it does (idempotent — safe to re-run)
-------------------------------------------
1. **Reloads the QML styles** onto the vector layers via ``loadNamedStyle`` —
   loads *all* categories (Symbology + Labeling + MapTips) in one go, so it also
   sidesteps the manual "Load Style → All Categories" trap.
2. **Sets layer scale visibility** so markers vanish at continental zoom
   (Bahnhöfe from 1:1.5M, Info-Marker from 1:8M). POI is *not* gated here — its
   rule-based renderer (built by build_marker_styles.py) staggers per category;
   Bahn-Linien stays always-on (the backbone), only its labels are scale-gated
   inside the QML.
3. **Turns the basemap stack into scale bands** so the right map shows
   automatically per zoom, and switches off the opaque competitors that would
   otherwise obscure them:
       CARTO Positron   weit  … 1:4 000 000   (ruhige Kontinentalansicht)
       Arcanum 2.       1:4 000 000 … 1:25 000 (historischer Arbeitsbereich)
       ESRI World Imagery 1:25 000 … nah       (scharfer Hand-off bei Arcanum-zmax=14)

Afterwards: **save the project (Strg+S)** so the changes land in the .qgz (and
travel to QField). Nothing is written to disk by this script.

Scale semantics (QGIS, notoriously confusing)
----------------------------------------------
A layer is visible when ``maximumScale ≤ Kartennenner ≤ minimumScale``:
``minimumScale`` = am weitesten herausgezoomte Grenze (großer Nenner),
``maximumScale`` = am weitesten hereingezoomte Grenze (kleiner Nenner).
``0`` = unbegrenzt. Hier als ``(minimumScale, maximumScale)`` notiert.
"""

from pathlib import Path

from qgis.core import QgsProject

# layer name -> QML filename under qgis/styles/
LAYER_STYLES = {
    "POI": "poi_destinations.qml",
    "WikiVoyage Städte": "wikivoyage_cities.qml",
    "Bahnhöfe": "rail_stations.qml",
    "Bahn-Linien": "rail_lines.qml",
    "Info-Marker": "info_markers.qml",
}

# layer name -> (minimumScale, maximumScale); 0 = unbegrenzt.
# Nur Layer, deren *Geometrie* maßstabsabhängig aus-/eingeblendet werden soll.
LAYER_SCALE = {
    # Vektor-Marker: bei Weitzoom ausblenden (gegen Europa-Cluster)
    "Bahnhöfe":          (1_500_000, 0),  # ab 1:1,5 Mio nach innen sichtbar
    "Info-Marker":       (8_000_000, 0),  # ab 1:8 Mio nach innen sichtbar
    "WikiVoyage Städte": (2_000_000, 0),  # ab 1:2 Mio (wie sekundäre POIs)
    # Basemap-Bänder (genau eine Karte je Zoom-Stufe → kein Übereinanderliegen)
    "CARTO Positron (hell, dezent)":          (0, 4_000_000),
    "Arcanum 2. Militäraufnahme (1806–1869)": (4_000_000, 25_000),
    "ESRI World Imagery (Satellit)":          (25_000, 0),
}

# Basemaps, die für die Auto-Umschaltung eingeschaltet sein müssen …
BASEMAPS_ON = [
    "CARTO Positron (hell, dezent)",
    "Arcanum 2. Militäraufnahme (1806–1869)",
    "ESRI World Imagery (Satellit)",
]
# … und opake Konkurrenten, die sonst die Bänder verdecken würden (ausschalten).
# Transparente Overlays (Label-Layer, OpenRailwayMap) werden bewusst NICHT
# angefasst — die darf der Nutzer frei dazuschalten.
BASEMAPS_OFF = [
    "OSM Standard",
    "OSM Topografische Karte",
    "OSM ÖPNV",
    "Arcanum 1. Militäraufnahme (1763–1790)",
    "Arcanum 3. Militäraufnahme (1869–1887)",
]


def _layer(name, warn=True):
    hits = QgsProject.instance().mapLayersByName(name)
    if not hits:
        if warn:
            print(f"  ⚠ Layer nicht gefunden, übersprungen: {name!r}")
        return None
    return hits[0]


def _set_checked(root, layer, checked):
    """Layer-Checkbox setzen; bei Einschalten auch alle Eltern-Gruppen aktivieren."""
    node = root.findLayer(layer.id())
    if node is None:
        return
    node.setItemVisibilityChecked(checked)
    if checked:
        parent = node.parent()
        while parent is not None and parent is not root:
            parent.setItemVisibilityChecked(True)
            parent = parent.parent()


def setup_scales():
    project = QgsProject.instance()
    styles_dir = Path(project.fileName()).parent / "styles"
    root = project.layerTreeRoot()

    # 1) Styles (alle Kategorien) neu laden
    for name, qml in LAYER_STYLES.items():
        layer = _layer(name)
        if layer is None:
            continue
        path = styles_dir / qml
        if not path.exists():
            print(f"  ⚠ QML fehlt: {path}")
            continue
        layer.loadNamedStyle(str(path))
        layer.triggerRepaint()
        print(f"  Style geladen: {name}  ←  {qml}")

    # 2) Layer-Maßstabssichtbarkeit
    for name, (min_s, max_s) in LAYER_SCALE.items():
        layer = _layer(name)
        if layer is None:
            continue
        layer.setScaleBasedVisibility(True)
        layer.setMinimumScale(float(min_s))
        layer.setMaximumScale(float(max_s))
        layer.triggerRepaint()
        lo = "∞" if min_s == 0 else f"1:{min_s:,}"
        hi = "nah" if max_s == 0 else f"1:{max_s:,}"
        print(f"  Maßstab: {name}  sichtbar {hi} … {lo}")

    # 3) Basemap-Checkboxen für die Auto-Umschaltung
    for name in BASEMAPS_ON:
        layer = _layer(name)
        if layer:
            _set_checked(root, layer, True)
    for name in BASEMAPS_OFF:
        layer = _layer(name, warn=False)  # missing = normal (e.g. QuickMapServices layers)
        if layer:
            _set_checked(root, layer, False)

    print("\nFertig. Projekt speichern (Strg+S), damit alles in der .qgz landet.")


setup_scales()

try:  # Karte sofort neu zeichnen, falls iface verfügbar
    iface.mapCanvas().refreshAllLayers()  # noqa: F821
except NameError:
    pass
