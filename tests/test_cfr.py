"""Tests für die reinen Funktionen der CFR-Ingestion + Timetable.

Abgedeckt: Halte-Index (Rang-Auflösung, Koordinaten-Fallback), Alias-Matching
und das Timetable-Schema/Laden. Bewusst ohne Netz/Datei-Schreibvorgänge.
"""

from __future__ import annotations

from fetch_cfr_data import Stop, build_index, resolve
from timetable import TIMETABLE_FIELDS, approx_fields, load_timetable


# --------------------------------------------------------------------------- #
# build_index                                                                 #
# --------------------------------------------------------------------------- #
def test_build_index_station_beats_halt_and_skips_unusable():
    data = {
        "elements": [
            # Gleicher Name, "station" (Rang 0) muss "halt" (Rang 1) schlagen.
            {"tags": {"name": "Sibiu", "railway": "halt"}, "lat": 45.0, "lon": 24.0},
            {"tags": {"name": "Sibiu", "railway": "station"}, "lat": 45.8, "lon": 24.1},
            # Ohne Name → ignorieren.
            {"tags": {"railway": "station"}, "lat": 1.0, "lon": 1.0},
            # Ohne Koordinaten → ignorieren.
            {"tags": {"name": "Geistbahnhof", "railway": "station"}},
        ]
    }
    index = build_index(data)

    assert index["Sibiu"] == (24.1, 45.8)   # (lon, lat), station gewinnt
    assert "Geistbahnhof" not in index
    assert len(index) == 1


def test_build_index_uses_center_and_keeps_zero_coords():
    data = {
        "elements": [
            # way/relation: nur center, kein lat/lon.
            {"tags": {"name": "Wegbahnhof", "railway": "station"},
             "center": {"lat": 46.0, "lon": 25.0}},
            # lat/lon == 0.0 ist gültig und darf nicht als "fehlend" gelten.
            {"tags": {"name": "Nullinsel", "railway": "halt"}, "lat": 0.0, "lon": 0.0},
        ]
    }
    index = build_index(data)

    assert index["Wegbahnhof"] == (25.0, 46.0)
    assert index["Nullinsel"] == (0.0, 0.0)


# --------------------------------------------------------------------------- #
# resolve (Alias-Matching)                                                    #
# --------------------------------------------------------------------------- #
def test_resolve_matches_canonical_and_alias():
    index = {"Gara de Nord": (26.07, 44.45)}
    stop = Stop("București Nord", "București", ("Gara de Nord",))

    assert resolve(stop, index) == (26.07, 44.45)        # über Alias
    assert resolve(Stop("Unbekannt", "X"), index) is None


# --------------------------------------------------------------------------- #
# Timetable-Schema + Laden                                                    #
# --------------------------------------------------------------------------- #
def test_approx_fields_parsing():
    assert approx_fields({"approx": "dep,arr"}) == {"dep", "arr"}
    assert approx_fields({"approx": "arr"}) == {"arr"}
    assert approx_fields({"approx": "dep; arr"}) == {"dep", "arr"}   # ; toleriert
    assert approx_fields({"approx": ""}) == set()
    assert approx_fields({}) == set()                                # Spalte fehlt


def test_load_timetable_roundtrip_and_missing(tmp_path):
    csv_path = tmp_path / "timetable.csv"
    csv_path.write_text(
        "route_id,dep_time,approx\nM200,07:54,\"dep,arr\"\n", encoding="utf-8"
    )
    loaded = load_timetable(csv_path)

    assert loaded["M200"]["dep_time"] == "07:54"
    assert approx_fields(loaded["M200"]) == {"dep", "arr"}
    assert load_timetable(tmp_path / "fehlt.csv") == {}


def test_approx_is_merged_into_rail_lines():
    # Regressionsschutz: approx muss in die GeoJSON-Features wandern.
    assert "approx" in TIMETABLE_FIELDS
