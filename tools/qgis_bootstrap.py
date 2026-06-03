"""Build the Ulmer Schachtel QGIS project from scratch, from the source files.

Run this from inside QGIS: **Plugins → Python Console → Show Editor →** open this
file and hit *Run*, or paste the contents. It needs the running QGIS application
context (``qgis.core`` / ``iface``); it is not standalone. Open (or create+save) a
project at ``qgis/reiseplan.qgz`` first, so paths can be resolved relative to it.

What it does (idempotent — safe to re-run)
-------------------------------------------
Reproduces the manual setup from docs/getting-started/qgis-setup.md so ``reiseplan.qgz`` is
buildable from code:

1. **Project CRS** → ``EPSG:3844 (Stereo70)`` (avoids the EPSG:4326 trap: the data
   stays 4326 and is reprojected on the fly).
2. **Loads the vector layers** (mostly ``data/processed/*.geojson``; the historical
   ``staatsgrenzen.geojson`` from ``data/reference/historical/`` via ``BASE_DIR_FOR``)
   with the German display names the rest of the toolchain expects, grouped
   Guide / Bahn / Historisch and ordered top→bottom.
3. **Applies the QML styles** (``loadNamedStyle`` = all categories: Symbology +
   Labeling + MapTips) and any **subset filter** (``SUBSET_FOR``; e.g. trims the
   world borders to the empires relevant to the trip).
4. **info_markers display field** → ``title``.
5. **Canvas background** → ``#f3ecd5`` (warm off-white) and **relative paths**.

It does *not* load base maps or set scale bands / bookmarks — those are the
companion scripts (printed at the end). Run them after, then save.
"""

from pathlib import Path

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
)
from qgis.PyQt.QtGui import QColor

CRS = "EPSG:3844"
CANVAS_BG = QColor(243, 236, 213)  # #f3ecd5

# (GeoJSON-Datei, Anzeigename, Gruppe) — Reihenfolge = oben→unten in der Legende.
# Die meisten Layer liegen in data/processed/; Ausnahmen siehe BASE_DIR_FOR unten.
VECTOR_LAYERS = [
    ("info_markers.geojson",      "Info-Marker",       "Guide"),
    ("poi_destinations.geojson",  "POI",               "Guide"),
    ("wikivoyage_cities.geojson", "WikiVoyage Städte", "Guide"),
    ("rail_stations.geojson",     "Bahnhöfe",          "Bahn"),
    ("rail_lines.geojson",        "Bahn-Linien",       "Bahn"),
    ("rail_gaps.geojson",         "Bahn-Lücken",       "Bahn"),
    ("staatsgrenzen.geojson",       "Grenzen 1800",         "Historisch"),
    ("historische_reiche.geojson",  "Historische Reiche",    "Historisch"),
    ("historische_regionen.geojson","Historische Regionen",  "Historisch"),
    ("historische_staedte.geojson", "Historische Städte",    "Historisch"),
]
STYLE_FOR = {
    "Info-Marker":         "info_markers.qml",
    "POI":                 "poi_destinations.qml",
    "WikiVoyage Städte":   "wikivoyage_cities.qml",
    "Bahnhöfe":            "rail_stations.qml",
    "Bahn-Linien":         "rail_lines.qml",
    "Bahn-Lücken":         "rail_gaps.qml",
    "Grenzen 1800":        "grenzen.qml",
    "Historische Reiche":  "historische_reiche.qml",
    "Historische Regionen":"historische_regionen.qml",
    "Historische Städte":  "historische_staedte.qml",
}
# Layer, die NICHT in data/processed/ liegen → relativer Pfad ab Repo-Wurzel.
BASE_DIR_FOR = {
    "Grenzen 1800":         ("data", "reference", "historical"),
    "Historische Reiche":   ("data", "reference", "historical"),
    "Historische Regionen": ("data", "reference", "historical"),
    "Historische Städte":   ("data", "reference", "historical"),
}
# Subset-Strings (Layer-Filter): den weltweiten Grenzdatensatz auf die für die
# Reise relevanten Reiche/Nachbarn um 1900 eindampfen (236 → 10 Features).
SUBSET_FOR = {
    "Grenzen 1800": (
        "\"NAME\" IN ('Austria Hungary','Romania','Ottoman Empire',"
        "'Bulgaria','Serbia','Montenegro','Bosnia-Herzegovina',"
        "'Greece','Russian Empire')"
    ),
}
# Lokale Raster (Pfad ab Repo-Wurzel, Anzeigename, Gruppe). Werden NACH den Vektoren
# eingehängt, landen also unter „Grenzen 1800" in der Gruppe — die historische Karte
# ist der Hintergrund, die Grenz-Umrisse liegen darüber. Quelle: tools/fetch_arcanum_clip.py
# (lokales, auf Rumänien+Österreich-Ungarn zugeschnittenes GeoTIFF, außen transparent —
# QGIS kann ein Raster nicht auf der Leinwand clippen, daher vorab gebacken).
RASTER_LAYERS = [
    (("data", "raster", "arcanum2_ro_clip.tif"),
     "Arcanum 2 (RO, zugeschnitten)", "Historisch"),
]
# Grenzen unter „Bahn", damit die Gleise über den getönten Grenzflächen liegen.
GROUP_ORDER = ["Guide", "Bahn", "Historisch"]  # oben→unten


def bootstrap():
    project = QgsProject.instance()
    if not project.fileName():
        print("  ⚠ Projekt ist nicht gespeichert. Bitte erst unter "
              "qgis/reiseplan.qgz speichern, dann erneut ausführen.")
        return

    qgis_dir = Path(project.fileName()).parent
    repo_dir = qgis_dir.parent
    data_dir = repo_dir / "data" / "processed"
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

        base_dir = data_dir
        if name in BASE_DIR_FOR:
            base_dir = repo_dir.joinpath(*BASE_DIR_FOR[name])
        path = base_dir / fname
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

        # Layer-Filter (Subset) — z.B. Welt-Grenzen auf die relevanten Reiche kürzen
        if name in SUBSET_FOR:
            layer.setSubsetString(SUBSET_FOR[name])

        project.addMapLayer(layer, False)
        groups[gname].addLayer(layer)
        print(f"  + {name}  ←  {fname}"
              + (f"  [{STYLE_FOR[name]}]" if qml.exists() else ""))

    # 2b) Lokale Raster (z.B. zugeschnittene Arcanum-Karte) — nach den Vektoren,
    #     damit sie in der Gruppe darunter (= Hintergrund) liegen.
    for parts, name, gname in RASTER_LAYERS:
        for dup in project.mapLayersByName(name):
            project.removeMapLayer(dup.id())
        path = repo_dir.joinpath(*parts)
        if not path.exists():
            print(f"  ⚠ Raster fehlt — erst `python tools/fetch_arcanum_clip.py` "
                  f"ausführen: {path}")
            continue
        layer = QgsRasterLayer(str(path), name, "gdal")
        if not layer.isValid():
            print(f"  ⚠ Raster ungültig: {name}")
            continue
        project.addMapLayer(layer, False)
        groups[gname].addLayer(layer)
        print(f"  + {name}  ←  {path.name}")

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
    print("  1) tools/qgis_basemaps.py         (Hintergrundkarten laden)")
    print("  2) tools/qgis_natural_features.py (Gebirge, Gipfel, Landschaftsnamen)")
    print("  3) tools/qgis_mining.py           (Bodenschätze)")
    print("  4) tools/qgis_industry.py         (Industriestandorte)")
    print("  5) tools/qgis_terrain.py          (Hillshade + Höhenlinien)")
    print("  6) tools/qgis_landcover.py        (Landbedeckung)")
    print("  7) tools/qgis_setup_scales.py     (Maßstabsbänder + -sichtbarkeit)")
    print("  8) tools/qgis_bookmarks.py        (räumliche Lesezeichen)")
    print("  → danach Projekt speichern (Strg+S).")


bootstrap()

try:
    iface.mapCanvas().refreshAllLayers()  # noqa: F821
except NameError:
    pass
