"""Data access layer — Repository pattern (Pattern 3).

All reads from and writes to the file system are centralised here.  Higher
layers (tables, web, ingest, cli) import named functions/classes from this
module instead of scattering open()/json.load() calls throughout the codebase.

Repositories:
  GeoJSON/CSV helpers   load_geojson, write_json, feature_collection
  Stop-sequence index   stops_for, load_route_stops  (cached in-process)
  Route properties      routes()
  TimetableRepository   load() → Timetable, scaffold(magistralen)

Path constants (POI_PATH etc.) are co-located here because they are
repository implementation details — callers reference them by name, not path.
"""

from __future__ import annotations

import csv
import functools
import json
from pathlib import Path

from .domain import (
    TIMETABLE_COLUMNS,
    TIMETABLE_FIELDS,
    Connection,
    Magistrale,
    Timetable,
)
from .paths import PROCESSED, ROOT

# ---------------------------------------------------------------------------
# Well-known data paths
# ---------------------------------------------------------------------------

POI_PATH = PROCESSED / "poi_destinations.geojson"
ROUTES_PATH = PROCESSED / "rail_lines.geojson"
STATIONS_PATH = PROCESSED / "rail_stations.geojson"
INFO_PATH = PROCESSED / "info_markers.geojson"
ROUTE_STOPS_PATH = PROCESSED / "route_stops.csv"
TIMETABLE_PATH = PROCESSED / "timetable.csv"
GPKG_PATH = PROCESSED / "reiseplan.gpkg"


# ---------------------------------------------------------------------------
# GeoJSON helpers
# ---------------------------------------------------------------------------

def load_geojson(path: Path) -> dict:
    """Load a GeoJSON file and return the parsed dict."""
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def feature_collection(name: str, features: list[dict]) -> dict:
    """Wrap a feature list in a GeoJSON FeatureCollection envelope."""
    return {
        "type": "FeatureCollection",
        "name": name,
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": features,
    }


def write_json(path: Path, obj: dict) -> None:
    """Write a dict as pretty-printed JSON (UTF-8, trailing newline)."""
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


# ---------------------------------------------------------------------------
# Stop-sequence index (cached for the lifetime of the process)
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _stops_index() -> dict[str, list[dict]]:
    """Load route_stops.csv and index by route_id (sorted by sequence)."""
    index: dict[str, list[dict]] = {}
    with ROUTE_STOPS_PATH.open("r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            index.setdefault(row["route_id"], []).append(row)
    for rows in index.values():
        rows.sort(key=lambda r: int(r["sequence"]))
    return index


def stops_for(route_id: str) -> list[dict]:
    """Return the stop sequence for one magistrală, or [] if unknown."""
    return _stops_index().get(route_id, [])


def load_route_stops() -> list[dict]:
    """Return all stop rows across all magistralen (flattened)."""
    return [row for rows in _stops_index().values() for row in rows]


# ---------------------------------------------------------------------------
# Route repository (thin wrapper over rail_lines.geojson)
# ---------------------------------------------------------------------------

def routes() -> list[dict]:
    """Return GeoJSON feature properties for all magistralen."""
    return [f["properties"] for f in load_geojson(ROUTES_PATH)["features"]]


# ---------------------------------------------------------------------------
# TimetableRepository — Pattern 3 applied to the hand-maintained CSV
# ---------------------------------------------------------------------------

class TimetableRepository:
    """Reads and scaffolds the hand-maintained ``timetable.csv``.

    Accepts a custom ``path`` so tests can point at temporary files without
    touching the real data directory:

        repo = TimetableRepository(tmp_path / "timetable.csv")
        timetable = repo.load()

    Design choice: ``load()`` returns a domain ``Timetable`` (not a raw dict)
    so callers work with ``Connection`` value objects and get typed access to
    ``approximate``, ``dep_time``, etc. instead of bare string dicts.
    """

    def __init__(self, path: Path = TIMETABLE_PATH) -> None:
        self.path = path

    def load(self) -> Timetable:
        """Return ``Timetable`` (route_id → Connection). Empty if file is missing."""
        if not self.path.is_file():
            return Timetable({})
        with self.path.open("r", encoding="utf-8") as fh:
            return Timetable(
                {row["route_id"]: Connection.from_row(row) for row in csv.DictReader(fh)}
            )

    def scaffold(self, magistralen: tuple[Magistrale, ...]) -> None:
        """Create a timetable.csv template — only if the file does not yet exist.

        Pre-fills route_id, from_city, to_city, via (city chain).  All time
        fields are left empty for hand-entry.  Existing files are **never**
        overwritten — this is intentional: real times are the authoritative data.
        """
        if self.path.is_file():
            return
        rows = []
        for mag in magistralen:
            cities = [s.city for s in mag.stops]
            rows.append({
                "route_id": mag.ref,
                "from_city": cities[0],
                "to_city": cities[-1],
                "days": "",
                "dep_time": "",
                "arr_time": "",
                "duration": "",
                "via": ", ".join(cities[1:-1]),
                "train": "",
                "approx": "",
                "notes": "",
            })
        with self.path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(TIMETABLE_COLUMNS))
            writer.writeheader()
            writer.writerows(rows)
        print(
            f"  → {self.path.relative_to(ROOT)} "
            f"(Vorlage, {len(rows)} Zeilen – Zeiten bitte ergänzen)"
        )
