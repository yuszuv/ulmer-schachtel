"""Seed project spatial bookmarks for the Ulmer Schachtel reiseplan.

Run this from inside QGIS: **Plugins → Python Console → Show Editor →**
open this file and hit *Run*, or paste the contents into the console.
It needs the running QGIS application context (``qgis.core``); it is not a
standalone script.

What it does
------------
Adds 10 *project* bookmarks (stored in the .qgz, so they are versioned and
travel with the project) via :class:`QgsBookmarkManager`:

* **Übersicht** group: whole-Romania extent + Siebenbürgen (Transylvania) core.
* **Magistralen** group: one bookmark per CFR main line M200–M900, framed to
  that line's own bounding box — handy for QC (both endpoints visible) and for
  jumping between routes.

Re-running is safe: bookmarks whose names already exist are removed first, so
the set stays idempotent instead of piling up duplicates.

Extents
-------
Bounding boxes were computed from ``data/processed/rail_lines.geojson`` (the
real geometries, EPSG:4326). They are stored here as literals so the script has
no file dependency. Each box gets an 8 % margin per axis. Bookmark extents carry
their own CRS (4326); QGIS reprojects them to the project CRS on use.
"""

from qgis.core import (
    QgsBookmark,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsRectangle,
    QgsReferencedRectangle,
)

CRS = QgsCoordinateReferenceSystem("EPSG:4326")
MARGIN = 0.08  # fraction of each axis span added on every side

# name, group, (xmin, ymin, xmax, ymax) in EPSG:4326
BOOKMARKS = [
    ("Übersicht Rumänien", "Übersicht", (21.2072, 43.8221, 28.6316, 47.7952)),
    ("Siebenbürgen-Fokus", "Übersicht", (22.5000, 45.4000, 26.2000, 47.5000)),
    ("M200 · Brașov–Curtici",      "Magistralen", (21.2979, 45.6612, 25.6136, 46.3409)),
    ("M300 · București–Oradea",    "Magistralen", (21.9362, 44.4467, 26.0738, 47.0701)),
    ("M400 · Brașov–Satu Mare",    "Magistralen", (22.8931, 45.6612, 25.6136, 47.7952)),
    ("M500 · București–Suceava",   "Magistralen", (25.9946, 44.4467, 27.1693, 47.6704)),
    ("M600 · Făurei–Iași",         "Magistralen", (27.2748, 45.0827, 27.7271, 47.1654)),
    ("M700 · București–Galați",    "Magistralen", (26.0738, 44.4467, 28.0610, 45.4449)),
    ("M800 · București–Mangalia",  "Magistralen", (26.0738, 43.8221, 28.6316, 44.4467)),
    ("M900 · București–Timișoara", "Magistralen", (21.2072, 44.3288, 26.0738, 45.7511)),
]


def _padded(xmin, ymin, xmax, ymax):
    dx = (xmax - xmin) * MARGIN or 0.05
    dy = (ymax - ymin) * MARGIN or 0.05
    return QgsRectangle(xmin - dx, ymin - dy, xmax + dx, ymax + dy)


def seed_bookmarks():
    mgr = QgsProject.instance().bookmarkManager()
    wanted = {name for name, _, _ in BOOKMARKS}

    # idempotent: drop any existing bookmark we are about to (re)create
    for existing in list(mgr.bookmarks()):
        if existing.name() in wanted:
            mgr.removeBookmark(existing.id())

    for name, group, box in BOOKMARKS:
        b = QgsBookmark()
        b.setName(name)
        b.setGroup(group)
        b.setExtent(QgsReferencedRectangle(_padded(*box), CRS))
        mgr.addBookmark(b)

    print(f"{len(BOOKMARKS)} Bookmarks gesetzt. Projekt speichern (Strg+S), "
          "damit sie in der .qgz landen.")


seed_bookmarks()
