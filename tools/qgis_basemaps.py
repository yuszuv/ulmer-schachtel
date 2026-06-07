"""Load the XYZ base maps from xyz_connections.xml into the open project.

Run this from inside QGIS: **Plugins → Python Console → Show Editor →** open this
file and hit *Run*, or paste the contents. It needs the running QGIS application
context (``qgis.core`` / ``iface``); it is not standalone.

What it does (idempotent — safe to re-run)
-------------------------------------------
Reads ``qgis/xyz_connections.xml`` (next to the project) and turns every
``<xyztiles>`` entry into a raster layer in a group **"Hintergrundkarten"** at the
*bottom* of the layer tree (so it sits behind your own vector data). Layer names
match the XML exactly — that's what ``tools/qgis_setup_scales.py`` looks up when it
wires the scale bands.

All base maps are added **unchecked**. Then run ``tools/qgis_setup_scales.py``: it
switches the three banded maps (CARTO / Arcanum / ESRI) on and gives them their
scale ranges. The rest stay available as a manual fallback.

Replaces the manual "Browser → XYZ Tiles → Load Connections… → double-click each"
dance described in docs/getting-started/qgis-setup.md.

Referer note
------------
The Arcanum surveys need a Referer header; it is passed as ``http-header:referer``
(QGIS ≥ 3.x). If Arcanum tiles 403, check that param against your QGIS version.
"""

from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

from qgis.core import QgsProject, QgsRasterLayer

try:
    from qgis.PyQt.QtGui import QColor  # noqa: F401  (nur falls erweitert)
except Exception:  # pragma: no cover
    pass

GROUP_NAME = "Hintergrundkarten"


def _xyz_uri(url, zmin, zmax, referer, tile_pixel_ratio):
    """QGIS-Datenquellen-URI für einen XYZ-Tile-Layer bauen.

    Die URL wird vollständig prozent-kodiert (``safe=''``), damit ``&``, ``:`` und
    die ``{z}/{x}/{y}``-Platzhalter den URI-Parser nicht zerschießen — genau so
    speichert QGIS XYZ-Quellen selbst.
    """
    parts = ["type=xyz", f"url={quote(url, safe='')}", f"zmin={zmin}", f"zmax={zmax}"]
    if tile_pixel_ratio and int(tile_pixel_ratio) > 0:
        parts.append(f"tilePixelRatio={tile_pixel_ratio}")
    if referer:
        parts.append(f"http-header:referer={quote(referer, safe='')}")
    return "&".join(parts)


def load_basemaps():
    project = QgsProject.instance()

    # Bootstrap sys.path to import qgis_helpers
    import sys
    _pf = Path(project.fileName()) if project.fileName() else None
    _rd = next((p for p in [_pf.parent] + list(_pf.parents) if (p / "data" / "processed").is_dir()), None) if _pf else None
    if _rd and str(_rd / "tools") not in sys.path:
        sys.path.append(str(_rd / "tools"))

    import qgis_helpers

    repo_dir, data_dir, raster_dir, styles_dir = qgis_helpers.get_repo_paths(project)

    xml_path = repo_dir / "qgis" / "xyz_connections.xml"
    if not xml_path.exists():
        print(f"  ⚠ Nicht gefunden: {xml_path}")
        return

    entries = ET.parse(xml_path).getroot().findall("xyztiles")
    root = project.layerTreeRoot()

    # idempotent: vorhandene Gruppe + gleichnamige Layer entfernen
    group = qgis_helpers.get_or_create_group(project, GROUP_NAME)

    added = 0
    for e in entries:
        name = e.get("name")
        qgis_helpers.remove_layers_by_name(project, name)

        uri = _xyz_uri(
            e.get("url"), e.get("zmin", "0"), e.get("zmax", "19"),
            e.get("referer", ""), e.get("tilePixelRatio", "0"),
        )
        layer = QgsRasterLayer(uri, name, "wms")
        if not layer.isValid():
            print(f"  ⚠ ungültig, übersprungen: {name}")
            continue

        project.addMapLayer(layer, False)        # nicht automatisch ins Wurzel-Legendenende
        node = group.addLayer(layer)
        node.setItemVisibilityChecked(False)     # alle aus; setup_scales schaltet die Bänder an
        added += 1
        print(f"  + {name}")

    print(f"\n{added} Basemaps in Gruppe „{GROUP_NAME}“ geladen (alle aus).")
    print("Nächster Schritt: tools/qgis_setup_scales.py ausführen "
          "(schaltet CARTO/Arcanum/ESRI maßstabsgesteuert ein), dann speichern.")


load_basemaps()

try:
    iface.mapCanvas().refreshAllLayers()  # noqa: F821
except NameError:
    pass
