"""Core domain model — pure value objects, no IO, no side effects.

Ubiquitous language used throughout the project:
  Magistrale  CFR main rail line (was called ``Line`` in the old ingest script)
  Stop        a station on a magistrală with its OSM name aliases
  Coordinate  a WGS84 lon/lat pair (EPSG:4326)
  Connection  timetable data for one magistrală (one row of timetable.csv)
  Timetable   route_id → Connection mapping (hand-maintained)

DDD note: all types here are frozen value objects — equality by value, no
identity, no mutation. IO and persistence live in repository.py.

Schema constants (TIMETABLE_COLUMNS / TIMETABLE_FIELDS) live here because
they are part of the domain contract between the hand-maintained CSV and the
GeoJSON feature properties; any code that reads or writes either side needs them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator


# ---------------------------------------------------------------------------
# Coordinate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Coordinate:
    """A WGS84 position in EPSG:4326 — lon first, per GeoJSON spec (RFC 7946)."""

    lon: float
    lat: float

    def as_list(self) -> list[float]:
        """[lon, lat] — ready to drop into a GeoJSON coordinates array."""
        return [self.lon, self.lat]


# ---------------------------------------------------------------------------
# Stop / Magistrale
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Stop:
    """A station on a magistrală.

    ``name`` is the canonical display name stored in processed GeoJSON.
    ``osm_names`` are alternative spellings used *only* during OSM ingest
    for fuzzy name matching — they are never written to any output file.
    """

    name: str
    city: str
    osm_names: tuple[str, ...] = field(default_factory=tuple)

    def lookup_names(self) -> tuple[str, ...]:
        """Return all names to try during OSM resolution, canonical first."""
        return (self.name, *self.osm_names)


@dataclass(frozen=True)
class Magistrale:
    """A CFR main line (magistrală), e.g. M300 București–Brașov–Cluj-Napoca.

    Renamed from ``Line`` (old script) to match the Romanian/project term used
    in the UI, docs, and AGENTS.md.
    """

    ref: str           # e.g. "M300"
    route_name: str    # display name (German)
    tags: str          # comma-separated topic tags
    length_km: int     # official route length (km, Wikipedia)
    stops: tuple[Stop, ...]

    @property
    def from_city(self) -> str:
        return self.stops[0].city

    @property
    def to_city(self) -> str:
        return self.stops[-1].city


# ---------------------------------------------------------------------------
# Timetable schema (shared contract between ingest and display)
# ---------------------------------------------------------------------------

# All columns in timetable.csv.  ``route_id`` is the join key; from/to/via
# are pre-filled by TimetableRepository.scaffold(); the rest are hand-entered.
TIMETABLE_COLUMNS: tuple[str, ...] = (
    "route_id", "from_city", "to_city", "days",
    "dep_time", "arr_time", "duration", "via", "train", "approx", "notes",
)

# Fields merged from the timetable into each rail_lines GeoJSON feature.
# ``approx`` explicitly names which time fields are estimates ({dep,arr} subset).
TIMETABLE_FIELDS: tuple[str, ...] = (
    "days", "dep_time", "arr_time", "duration", "via", "train", "approx",
)


# ---------------------------------------------------------------------------
# Connection / Timetable
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Connection:
    """Timetable data for one magistrală — a single hand-maintained CSV row.

    ``approximate`` replaces the old free-text heuristic: it is a frozenset
    naming which time fields are estimates — a subset of {'dep', 'arr'}.
    An empty set means both times are authoritative.

    Usage:
        conn = Connection.from_row(csv_dict)
        if "dep" in conn.approximate:
            label = f"~{conn.dep_time}"
    """

    route_id: str
    from_city: str
    to_city: str
    days: str
    dep_time: str
    arr_time: str
    duration: str
    via: str
    train: str
    approximate: frozenset[str]   # subset of {'dep', 'arr'}
    notes: str

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Connection":
        """Construct from a raw csv.DictReader row."""
        raw = (row.get("approx") or "").replace(";", ",")
        approx = frozenset(t.strip() for t in raw.split(",") if t.strip())
        return cls(
            route_id=row.get("route_id", ""),
            from_city=row.get("from_city", ""),
            to_city=row.get("to_city", ""),
            days=row.get("days", ""),
            dep_time=row.get("dep_time", ""),
            arr_time=row.get("arr_time", ""),
            duration=row.get("duration", ""),
            via=row.get("via", ""),
            train=row.get("train", ""),
            approximate=approx,
            notes=row.get("notes", ""),
        )

    def as_dict(self) -> dict[str, str]:
        """Flat string dict for CSV writing or GeoJSON property merging.

        ``approx`` is serialised with a fixed token order (dep before arr) so
        that round-tripping through Connection.from_row → as_dict is
        deterministic and matches the hand-maintained CSV convention.
        """
        # Fixed order: dep first, then arr — matches the hand-maintained CSV.
        approx_str = ",".join(f for f in ("dep", "arr") if f in self.approximate)
        return {
            "route_id": self.route_id,
            "from_city": self.from_city,
            "to_city": self.to_city,
            "days": self.days,
            "dep_time": self.dep_time,
            "arr_time": self.arr_time,
            "duration": self.duration,
            "via": self.via,
            "train": self.train,
            "approx": approx_str,
            "notes": self.notes,
        }

    def geojson_fields(self) -> dict[str, str]:
        """Subset of as_dict() containing only TIMETABLE_FIELDS — for GeoJSON merge."""
        d = self.as_dict()
        return {k: d[k] for k in TIMETABLE_FIELDS}


class Timetable:
    """Immutable route_id → Connection mapping (loaded from timetable.csv).

    Iterable over route_ids, supports bool coercion, and passes a custom path
    to TimetableRepository for easy testing.
    """

    def __init__(self, data: dict[str, "Connection"]) -> None:
        self._data: dict[str, Connection] = dict(data)  # defensive copy

    def get(self, route_id: str) -> "Connection | None":
        return self._data.get(route_id)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return bool(self._data)
