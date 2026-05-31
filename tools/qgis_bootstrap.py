"""Build the Ulmer Schachtel QGIS project from scratch, from the source files.

Run this from inside QGIS: **Plugins → Python Console → Show Editor →** open this
file and hit *Run*, or paste the contents. It needs the running QGIS application
context (``qgis.core`` / ``iface``); it is not standalone. Open (or create+save) a
project at ``qgis/reiseplan.qgz`` first, so paths can be resolved relative to it.

What it does (idempotent — safe to re-run)
-------------------------------------------
Reproduces the manual setup from docs/01_qgis_setup.md so ``reiseplan.qgz`` is
buildable from code:

1. **Project CRS** → ``EPSG:3844 (Stereo70)`` (avoids the EPSG:4326 trap: the data
   stays 4326 and is reprojected on the fly).
2. **Loads the four vector layers** from ``data/processed/*.geojson`` with the
   German display names the rest of the toolchain expects, grouped Guide / Bahn and
   ordered top→bottom (Info-Marker, POI, Bahnhöfe, Bahn-Linien).
3. **Applies the QML styles** (``loadNamedStyle`` = all categories: Symbology +
   Labeling + MapTips).
4. **info_markers display field** → ``title``.
5. **Canvas background** → ``#f3ecd5`` (warm off-white) and **relative paths**.

It does *not* load base maps or set scale bands / bookmarks — those are the
companion scripts (printed at the end). Run them after, then save.
"""

from pathlib import Path

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QColor

CRS = "EPSG:3844"
CANVAS_BG = QColor(243, 236, 213)  # #f3ecd5

# (GeoJSON-Datei, Anzeigename, Gruppe) — Reihenfolge = oben→unten in der Legende
VECTOR_LAYERS = [
    ("info_markers.geojson",     "Info-Marker", "Guide"),
    ("poi_destinations.geojson", "POI",         "Guide"),
    ("rail_stations.geojson",    "Bahnhöfe",    "Bahn"),
    ("rail_lines.geojson",       "Bahn-Linien", "Bahn"),
]
STYLE_FOR = {
    "Info-Marker": "info_markers.qml",
    "POI":         "poi_destinations.qml",
    "Bahnhöfe":    "rail_stations.qml",
    "Bahn-Linien": "rail_lines.qml",
}
GROUP_ORDER = ["Guide", "Bahn"]  # oben→unten


def bootstrap():
    project = QgsProject.instance()
    if not project.fileName():
        print("  ⚠ Projekt ist nicht gespeichert. Bitte erst unter "
              "qgis/reiseplan.qgz speichern, dann erneut ausführen.")
        return

    qgis_dir = Path(project.fileName()).parent
    data_dir = qgis_dir.parent / "data" / "processed"
    styles_dir = qgis_dir / "styles"
    root = project.layerTreeRoot()

    # 1) Projekt-CRS
    project.setCrs(QgsCoordinateReferenceSystem(CRS))
    print(f"  CRS → {CRS}")

    # Gruppen (idempotent) oben anlegen, in definierter Reihenfolge
    groups = {}
    for i, gname in enumerate(GROUP_ORDER):
        old = root.findGroup(gname)
        if old is not None:
            root.removeChildNode(old)
        groups[gname] = root.insertGroup(i, gname)

    # 2) + 3) Vektorlayer laden, stylen, einsortieren
    for fname, name, gname in VECTOR_LAYERS:
        for dup in project.mapLayersByName(name):
            project.removeMapLayer(dup.id())

        path = data_dir / fname
        if not path.exists():
            print(f"  ⚠ Datenquelle fehlt: {path}")
            continue
        layer = QgsVectorLayer(str(path), name, "ogr")
        if not layer.isValid():
            print(f"  ⚠ Layer ungültig: {name}")
            continue

        qml = styles_dir / STYLE_FOR[name]
        if qml.exists():
            layer.loadNamedStyle(str(qml))   # alle Kategorien
        else:
            print(f"  ⚠ Style fehlt: {qml}")

        # 4) info_markers: Anzeigefeld auf "title"
        if name == "Info-Marker":
            layer.setDisplayExpression('"title"')

        project.addMapLayer(layer, False)
        groups[gname].addLayer(layer)
        print(f"  + {name}  ←  {fname}"
              + (f"  [{STYLE_FOR[name]}]" if qml.exists() else ""))

    # 5) Canvas-Hintergrund + relative Pfade
    project.writeEntry("Gui", "/CanvasColorRedPart", CANVAS_BG.red())
    project.writeEntry("Gui", "/CanvasColorGreenPart", CANVAS_BG.green())
    project.writeEntry("Gui", "/CanvasColorBluePart", CANVAS_BG.blue())
    project.writeEntry("Paths", "/Absolute", False)
    try:
        iface.mapCanvas().setCanvasColor(CANVAS_BG)  # noqa: F821
    except NameError:
        pass
    print("  Canvas-Hintergrund #f3ecd5 · Pfade relativ")

    print("\nGrundgerüst steht. Jetzt der Reihe nach ausführen:")
    print("  1) tools/qgis_basemaps.py      (Hintergrundkarten laden)")
    print("  2) tools/qgis_setup_scales.py  (Maßstabsbänder + -sichtbarkeit)")
    print("  3) tools/qgis_bookmarks.py     (räumliche Lesezeichen)")
    print("  → danach Projekt speichern (Strg+S).")


bootstrap()

try:
    iface.mapCanvas().refreshAllLayers()  # noqa: F821
except NameError:
    pass
