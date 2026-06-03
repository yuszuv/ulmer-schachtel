"""Tests for the cities pipeline — no network, no filesystem writes."""

from __future__ import annotations

import pytest

from reiseplan.cities import (
    _assign_importance,
    _in_ring,
    _place_key,
    _parse_element,
    CONTEXT_ROI,
    _OUTER_POP_THRESHOLD,
)
from reiseplan.themes import KUK_ROI


# ---------------------------------------------------------------------------
# Ray-casting point-in-polygon tests
# ---------------------------------------------------------------------------

# Simple unit square ring: (0,0)→(1,0)→(1,1)→(0,1)→(0,0)
_SQUARE = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def test_in_ring_centre_inside():
    assert _in_ring(0.5, 0.5, _SQUARE) is True


def test_in_ring_corner_point_edge():
    # Strictly outside corner
    assert _in_ring(1.5, 1.5, _SQUARE) is False


def test_in_ring_outside_right():
    assert _in_ring(2.0, 0.5, _SQUARE) is False


def test_in_ring_outside_below():
    assert _in_ring(0.5, -0.5, _SQUARE) is False


def test_in_ring_near_boundary_inside():
    # Just inside the ring
    assert _in_ring(0.01, 0.01, _SQUARE) is True


def test_in_ring_near_boundary_outside():
    assert _in_ring(1.01, 0.5, _SQUARE) is False


# ---------------------------------------------------------------------------
# Importance classification
# ---------------------------------------------------------------------------

def test_importance_city():
    assert _assign_importance("city", None) == 1


def test_importance_city_overrides_pop():
    # city always importance=1 regardless of population
    assert _assign_importance("city", 100) == 1


def test_importance_large_pop_no_tag():
    assert _assign_importance(None, 200_000) == 1


def test_importance_town():
    assert _assign_importance("town", None) == 2


def test_importance_town_with_mid_pop():
    assert _assign_importance("town", 5_000) == 2


def test_importance_medium_pop_no_tag():
    assert _assign_importance(None, 15_000) == 2


def test_importance_village():
    assert _assign_importance("village", None) == 3


def test_importance_small_pop():
    assert _assign_importance("village", 800) == 3


def test_importance_none_none():
    assert _assign_importance(None, None) == 3


def test_importance_boundary_100k():
    # Exactly at threshold → importance 1
    assert _assign_importance("town", 100_000) == 1


def test_importance_boundary_10k():
    # Exactly at threshold → importance 2
    assert _assign_importance("village", 10_000) == 2


# ---------------------------------------------------------------------------
# _parse_element
# ---------------------------------------------------------------------------

def _node(name, lat, lon, **extra_tags):
    tags = {"name": name, "place": "city", **extra_tags}
    return {"type": "node", "id": 1, "lat": lat, "lon": lon, "tags": tags}


def test_parse_element_basic():
    el = _node("Wien", 48.2, 16.37)
    rec = _parse_element(el)
    assert rec is not None
    assert rec["name"] == "Wien"
    assert rec["lat"] == pytest.approx(48.2)
    assert rec["lon"] == pytest.approx(16.37)
    assert rec["kind"] == "city"
    assert rec["population"] is None


def test_parse_element_with_population():
    el = _node("Budapest", 47.49, 19.04, population="1700000")
    rec = _parse_element(el)
    assert rec is not None
    assert rec["population"] == 1_700_000


def test_parse_element_missing_name():
    el = {"type": "node", "id": 2, "lat": 48.0, "lon": 16.0, "tags": {"place": "city"}}
    assert _parse_element(el) is None


def test_parse_element_missing_coords():
    el = {"type": "node", "id": 3, "tags": {"name": "X", "place": "city"}}
    assert _parse_element(el) is None


def test_parse_element_center_fallback():
    el = {
        "type": "way",
        "id": 4,
        "center": {"lat": 47.0, "lon": 28.0},
        "tags": {"name": "Chișinău", "place": "city"},
    }
    rec = _parse_element(el)
    assert rec is not None
    assert rec["lat"] == pytest.approx(47.0)
    assert rec["lon"] == pytest.approx(28.0)


# ---------------------------------------------------------------------------
# _place_key deduplication
# ---------------------------------------------------------------------------

def test_place_key_uses_wikidata():
    rec = {"wikidata": "Q1741", "lon": 48.2, "lat": 16.37, "_el": {}}
    assert _place_key(rec) == "Q1741"


def test_place_key_uses_coords_fallback():
    rec = {"wikidata": None, "lon": 48.20001, "lat": 16.37001, "_el": {}}
    key = _place_key(rec)
    assert key.startswith("48.2") or "," in key


def test_place_key_rounds_coords():
    rec1 = {"wikidata": None, "lon": 16.370001, "lat": 48.200001, "_el": {}}
    rec2 = {"wikidata": None, "lon": 16.370002, "lat": 48.200002, "_el": {}}
    # Differences at 6th decimal place collapse to the same key (rounded to 5).
    assert _place_key(rec1) == _place_key(rec2)


# ---------------------------------------------------------------------------
# Outer-tier filter constants sanity
# ---------------------------------------------------------------------------

def test_outer_pop_threshold_is_50k():
    assert _OUTER_POP_THRESHOLD == 50_000


def test_context_roi_contains_kuk_roi():
    """CONTEXT_ROI must fully enclose KUK_ROI."""
    assert CONTEXT_ROI.south <= KUK_ROI.south
    assert CONTEXT_ROI.west  <= KUK_ROI.west
    assert CONTEXT_ROI.north >= KUK_ROI.north
    assert CONTEXT_ROI.east  >= KUK_ROI.east


# ---------------------------------------------------------------------------
# CLI registration
# ---------------------------------------------------------------------------

def test_fetch_cities_registered_in_cli():
    from reiseplan import cli  # noqa: F401 — side-effect import populates REGISTRY
    names = {cmd.name for cmd in cli.REGISTRY}
    assert "fetch-cities" in names
