"""Tests for the pure functions of CFR ingest, overpass, and timetable.

Coverage: StationIndex (rank resolution, coordinate fallback, alias matching),
Connection value object, and TimetableRepository loading.
Intentionally no network or file-write side effects.
"""

from __future__ import annotations

from reiseplan.domain import Connection, Coordinate, Stop
from reiseplan.overpass import StationIndex
from reiseplan.repository import TimetableRepository
from reiseplan.result import Nothing, Some
from reiseplan.routing import RailNetwork


# ---------------------------------------------------------------------------
# StationIndex.from_overpass
# ---------------------------------------------------------------------------

def test_station_beats_halt_and_skips_unusable():
    data = {
        "elements": [
            # Same name: "station" (rank 0) must beat "halt" (rank 1).
            {"tags": {"name": "Sibiu", "railway": "halt"}, "lat": 45.0, "lon": 24.0},
            {"tags": {"name": "Sibiu", "railway": "station"}, "lat": 45.8, "lon": 24.1},
            # No name → skip.
            {"tags": {"railway": "station"}, "lat": 1.0, "lon": 1.0},
            # No coordinates → skip.
            {"tags": {"name": "Geistbahnhof", "railway": "station"}},
        ]
    }
    index = StationIndex.from_overpass(data)

    coord = index.resolve(Stop("Sibiu", "Sibiu"))
    assert coord.is_some
    assert coord.unwrap().lon == 24.1   # station wins
    assert coord.unwrap().lat == 45.8

    ghost = index.resolve(Stop("Geistbahnhof", "?"))
    assert not ghost.is_some


def test_station_index_uses_center_and_keeps_zero_coords():
    data = {
        "elements": [
            # way/relation: only center, no lat/lon.
            {"tags": {"name": "Wegbahnhof", "railway": "station"},
             "center": {"lat": 46.0, "lon": 25.0}},
            # lat/lon == 0.0 is valid and must not be treated as missing.
            {"tags": {"name": "Nullinsel", "railway": "halt"}, "lat": 0.0, "lon": 0.0},
        ]
    }
    index = StationIndex.from_overpass(data)

    weg = index.resolve(Stop("Wegbahnhof", "X"))
    assert weg.is_some
    assert weg.unwrap().lon == 25.0

    null = index.resolve(Stop("Nullinsel", "Y"))
    assert null.is_some
    assert null.unwrap().lon == 0.0
    assert null.unwrap().lat == 0.0


# ---------------------------------------------------------------------------
# StationIndex.resolve — alias matching
# ---------------------------------------------------------------------------

def test_resolve_matches_canonical_and_alias():
    data = {
        "elements": [
            {"tags": {"name": "Gara de Nord", "railway": "station"},
             "lat": 44.45, "lon": 26.07},
        ]
    }
    index = StationIndex.from_overpass(data)

    stop_with_alias = Stop("București Nord", "București", ("Gara de Nord",))
    result = index.resolve(stop_with_alias)
    assert isinstance(result, Some)
    assert result.unwrap().lon == 26.07    # found via alias

    no_match = index.resolve(Stop("Unbekannt", "X"))
    assert result is not Nothing
    assert no_match is Nothing


# ---------------------------------------------------------------------------
# Connection value object
# ---------------------------------------------------------------------------

def test_connection_from_row_parses_approx():
    row = {
        "route_id": "M200", "from_city": "Brașov", "to_city": "Arad",
        "days": "täglich", "dep_time": "07:54", "arr_time": "15:30",
        "duration": "7h36", "via": "Sibiu", "train": "IR", "approx": "dep,arr",
        "notes": "",
    }
    conn = Connection.from_row(row)
    assert conn.dep_time == "07:54"
    assert conn.approximate == frozenset({"dep", "arr"})


def test_connection_approx_accepts_semicolons():
    conn = Connection.from_row({"approx": "dep; arr", "route_id": "",
                                "from_city": "", "to_city": "", "days": "",
                                "dep_time": "", "arr_time": "", "duration": "",
                                "via": "", "train": "", "notes": ""})
    assert conn.approximate == frozenset({"dep", "arr"})


def test_connection_empty_approx():
    conn = Connection.from_row({"approx": "", "route_id": "",
                                "from_city": "", "to_city": "", "days": "",
                                "dep_time": "", "arr_time": "", "duration": "",
                                "via": "", "train": "", "notes": ""})
    assert conn.approximate == frozenset()


def test_connection_geojson_fields_includes_approx():
    """Regression: approx must be present in the GeoJSON feature merge."""
    from reiseplan.domain import TIMETABLE_FIELDS
    conn = Connection.from_row({"approx": "dep", "route_id": "M300",
                                "from_city": "A", "to_city": "B", "days": "",
                                "dep_time": "08:00", "arr_time": "", "duration": "",
                                "via": "", "train": "", "notes": ""})
    gf = conn.geojson_fields()
    assert set(gf.keys()) == set(TIMETABLE_FIELDS)
    assert gf["approx"] == "dep"


# ---------------------------------------------------------------------------
# TimetableRepository
# ---------------------------------------------------------------------------

def test_timetable_repository_roundtrip(tmp_path):
    csv_path = tmp_path / "timetable.csv"
    csv_path.write_text(
        'route_id,dep_time,approx\nM200,07:54,"dep,arr"\n', encoding="utf-8"
    )
    timetable = TimetableRepository(csv_path).load()

    conn = timetable.get("M200")
    assert conn is not None
    assert conn.dep_time == "07:54"
    assert conn.approximate == frozenset({"dep", "arr"})


def test_timetable_repository_missing_file(tmp_path):
    timetable = TimetableRepository(tmp_path / "fehlt.csv").load()
    assert not timetable


# ---------------------------------------------------------------------------
# RailNetwork (graph routing) — synthetic Overpass `out geom` ways, no network
# ---------------------------------------------------------------------------

def _way(coords: list[tuple[float, float]]) -> dict:
    """Build a fake Overpass way element from (lon, lat) vertices."""
    return {"type": "way",
            "geometry": [{"lon": lon, "lat": lat} for lon, lat in coords]}


def test_railnetwork_joins_ways_at_shared_node_and_routes():
    # Horizontal way and vertical way share the junction (1, 0).
    data = {"elements": [
        _way([(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]),
        _way([(1.0, -1.0), (1.0, 0.0), (1.0, 1.0)]),
    ]}
    net = RailNetwork.from_overpass(data)

    routed = net.route(Coordinate(0.0, 0.0), Coordinate(1.0, 1.0))
    assert routed.is_some
    path = routed.unwrap()
    assert path[0] == Coordinate(0.0, 0.0)
    assert path[-1] == Coordinate(1.0, 1.0)
    assert Coordinate(1.0, 0.0) in path          # crosses the shared junction


def test_railnetwork_unreachable_is_nothing():
    # Two disconnected components → no path between them.
    data = {"elements": [
        _way([(0.0, 0.0), (1.0, 0.0)]),
        _way([(10.0, 10.0), (11.0, 10.0)]),
    ]}
    net = RailNetwork.from_overpass(data)
    assert not net.route(Coordinate(0.0, 0.0), Coordinate(10.0, 10.0)).is_some


def test_railnetwork_empty_is_nothing():
    net = RailNetwork.from_overpass({"elements": []})
    assert not net.route(Coordinate(0.0, 0.0), Coordinate(1.0, 1.0)).is_some


def test_route_stops_concatenates_and_dedups_shared_vertices():
    data = {"elements": [_way([(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)])]}
    net = RailNetwork.from_overpass(data)

    coords, gaps = net.route_stops(
        [Coordinate(0.0, 0.0), Coordinate(1.0, 0.0), Coordinate(2.0, 0.0)]
    )
    assert gaps == []                             # fully routed
    # Shared endpoint (1,0) between the two legs appears exactly once.
    assert coords == [Coordinate(0.0, 0.0), Coordinate(1.0, 0.0), Coordinate(2.0, 0.0)]


def test_route_stops_falls_back_to_straight_on_gap():
    # Disconnected pieces → the leg between them falls back to a straight line.
    data = {"elements": [
        _way([(0.0, 0.0), (1.0, 0.0)]),
        _way([(5.0, 0.0), (6.0, 0.0)]),
    ]}
    net = RailNetwork.from_overpass(data)

    coords, gaps = net.route_stops([Coordinate(0.0, 0.0), Coordinate(6.0, 0.0)])
    assert len(gaps) == 1                         # one gap flagged
    assert gaps[0] == (Coordinate(0.0, 0.0), Coordinate(6.0, 0.0))
    assert coords[0] == Coordinate(0.0, 0.0)
    assert coords[-1] == Coordinate(6.0, 0.0)
