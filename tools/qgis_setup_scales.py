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
   automatically per zoom, switching off the opaque competitors that would
   otherwise obscure them. A single handoff at 1:8 000 000:
       Stadia Alidade Smooth  wide … 1:8 000 000  (subtle grayscale overview)
       CARTO Voyager          1:8 000 000 … near  (detailed map)
   The overview map is desaturated to a subtle "s/w" grayscale via a raster
   colour filter (step 4 below). Arcanum surveys, ESRI imagery and OpenTopoMap
   stay available as manual layers (switched off here).

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
    "POI":               "poi_destinations.qml",
    "WikiVoyage Städte": "wikivoyage_cities.qml",
    "Bahnhöfe":          "rail_stations.qml",
    "Bahn-Linien":       "rail_lines.qml",
    "Bahn-Lücken":       "rail_gaps.qml",
    "Info-Marker":       "info_markers.qml",
    "Grenzen 1800":         "grenzen.qml",
    "Historische Reiche":   "historische_reiche.qml",
    "Historische Regionen": "historische_regionen.qml",
    "Historische Städte":   "historische_staedte.qml",
}

# layer name -> (minimumScale, maximumScale); 0 = unbegrenzt.
# Nur Layer, deren *Geometrie* maßstabsabhängig aus-/eingeblendet werden soll.
LAYER_SCALE = {
    # Vektor-Marker: bei Weitzoom ausblenden (gegen Europa-Cluster)
    "Bahnhöfe":          (1_500_000, 0),  # ab 1:1,5 Mio nach innen sichtbar
    "Info-Marker":       (8_000_000, 0),  # ab 1:8 Mio nach innen sichtbar
    "WikiVoyage Städte": (2_000_000, 0),  # ab 1:2 Mio (wie sekundäre POIs)
    # Historische Grenzen: Orientierungsrahmen bei Weitzoom, Lärm bei Nahzoom.
    "Grenzen 1800":         (20_000_000, 800_000),  # sichtbar 1:800k … 1:20 Mio
    # Historische Reiche: reine Label-Ebene (Reich einmal beschriftet), mittlerer Zoom.
    "Historische Reiche":   (5_000_000,  1_000_000),  # sichtbar 1:1 Mio … 1:5 Mio
    # Historische Regionen: Binnenstruktur — erst beim Hineinzoomen unter die Staatsebene.
    "Historische Regionen": (3_000_000,  200_000),  # sichtbar 1:200k … 1:3 Mio
    # Historische Städte: Punkte, analog zu Bahnhöfen.
    "Historische Städte":   (1_500_000,  0),         # ab 1:1,5 Mio nach innen
    # Zugeschnittene Arcanum-Karte: nur im Detail-Band 1:100k … 1:4 Mio sichtbar.
    # Nicht bei Weitzooms: die Arcanum-Tiles enden an der Habsburg-Grenze; Dobruja
    # und das rumänische Regat waren Ottoman/autonom → keine Survey-Daten → schwarze
    # Pixel im geclippten Raster. Bei Weitzooms überdecken diese Flächen zu viel.
    # Erzeugt via tools/fetch_arcanum_clip.py.
    "Arcanum 2 (RO, zugeschnitten)": (4_000_000, 100_000),  # sichtbar 1:100k … 1:4 Mio
    # Basemap bands: subtle grayscale overview → detailed map, one handoff at 1:8M.
    "Stadia Alidade Smooth (matt, Sepia-tauglich)": (0, 8_000_000),  # wide … 1:8M (overview)
    "CARTO Voyager (hell, mehr Detail)":            (8_000_000, 0),  # 1:8M … near (detail)
}

# Basemaps that must be switched ON for the scale-band auto-handoff.
BASEMAPS_ON = [
    "Stadia Alidade Smooth (matt, Sepia-tauglich)",
    "CARTO Voyager (hell, mehr Detail)",
]
# Opaque competitors switched OFF so they don't obscure the bands; they remain
# available as manual layers. Transparent overlays (label layers, OpenRailwayMap)
# are deliberately left untouched — the user can toggle those freely.
BASEMAPS_OFF = [
    "CARTO Positron (hell, dezent)",
    "Arcanum 1. Militäraufnahme (1763–1790)",
    "Arcanum 2. Militäraufnahme (1806–1869)",
    "Arcanum 3. Militäraufnahme (1869–1887)",
    "ESRI World Imagery (Satellit)",
    "OpenTopoMap (Höhenlinien + Relief)",
    "ESRI World Hillshade (reines Relief)",
    "OSM Standard",
    "OSM Topografische Karte",
    "OSM ÖPNV",
]

# Subtle grayscale ("s/w") tuning for the overview basemap, applied as a raster
# colour filter (persists in the .qgz on save). Values are -100..100 each; this
# matches the recipe documented in xyz_connections.xml. For a stronger, true
# black-and-white look, add hueSaturationFilter().setGrayscaleMode(1) below.
BASEMAP_COLOR = {
    "Stadia Alidade Smooth (matt, Sepia-tauglich)":
        {"saturation": -70, "brightness": 15, "contrast": -15},
}


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

    # 4) Desaturate the overview basemap to a subtle grayscale ("s/w" look).
    for name, cfg in BASEMAP_COLOR.items():
        layer = _layer(name)
        if layer is None:
            continue
        layer.hueSaturationFilter().setSaturation(cfg["saturation"])
        layer.brightnessFilter().setBrightness(cfg["brightness"])
        layer.brightnessFilter().setContrast(cfg["contrast"])
        layer.triggerRepaint()
        print(f"  Entsättigt: {name}  (Sättigung {cfg['saturation']}, "
              f"Helligkeit {cfg['brightness']:+}, Kontrast {cfg['contrast']:+})")

    print("\nFertig. Projekt speichern (Strg+S), damit alles in der .qgz landet.")


setup_scales()

try:  # Karte sofort neu zeichnen, falls iface verfügbar
    iface.mapCanvas().refreshAllLayers()  # noqa: F821
except NameError:
    pass
