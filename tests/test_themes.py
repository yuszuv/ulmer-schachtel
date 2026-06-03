"""Tests for the thematic-layer pipeline — ThemeSpec registry and classification.

No network, no filesystem writes.  All tests use small in-memory element fixtures.
"""

from __future__ import annotations

from reiseplan.themes import REGISTRY, OutputLayer, ThemeSpec, KUK_ROI
# Importing thematic populates the REGISTRY via side-effectful imports.
import reiseplan.thematic  # noqa: F401


# ---------------------------------------------------------------------------
# REGISTRY completeness
# ---------------------------------------------------------------------------

_EXPECTED_THEMES = {"natural", "mining", "industry"}


def test_all_expected_themes_registered():
    assert _EXPECTED_THEMES <= set(REGISTRY)


def test_registry_specs_have_layers():
    for name, spec in REGISTRY.items():
        assert len(spec.layers) > 0, f"{name} has no layers"


def test_registry_specs_have_roi():
    for name, spec in REGISTRY.items():
        assert spec.roi.south < spec.roi.north
        assert spec.roi.west  < spec.roi.east


# ---------------------------------------------------------------------------
# OutputLayer.accepts — natural theme
# ---------------------------------------------------------------------------

def test_natural_ridges_accepts_way():
    from reiseplan.themes.natural import RIDGES_LAYER
    el = {"type": "way", "tags": {"natural": "ridge"}}
    assert RIDGES_LAYER.accepts(el) is True


def test_natural_ridges_rejects_node():
    from reiseplan.themes.natural import RIDGES_LAYER
    el = {"type": "node", "tags": {"natural": "ridge"}}
    assert RIDGES_LAYER.accepts(el) is False


def test_natural_peaks_accepts_peak_node():
    from reiseplan.themes.natural import PEAKS_LAYER
    el = {"type": "node", "tags": {"natural": "peak"}}
    assert PEAKS_LAYER.accepts(el) is True


def test_natural_peaks_rejects_valley_node():
    from reiseplan.themes.natural import PEAKS_LAYER
    el = {"type": "node", "tags": {"natural": "valley"}}
    assert PEAKS_LAYER.accepts(el) is False


def test_natural_landscape_accepts_mountain_range():
    from reiseplan.themes.natural import LANDSCAPE_LAYER
    el = {"type": "node", "tags": {"natural": "mountain_range"}}
    assert LANDSCAPE_LAYER.accepts(el) is True


def test_natural_landscape_accepts_valley():
    from reiseplan.themes.natural import LANDSCAPE_LAYER
    el = {"type": "node", "tags": {"natural": "valley"}}
    assert LANDSCAPE_LAYER.accepts(el) is True


# ---------------------------------------------------------------------------
# extra_props — natural theme
# ---------------------------------------------------------------------------

def test_natural_extra_props_adds_ele():
    from reiseplan.themes.natural import SPEC
    el = {"type": "node", "id": 1, "tags": {"natural": "peak", "ele": "2500"}}
    tags = el["tags"]
    props = SPEC.extra_props(el, tags, {"min_ele": 1500})
    assert props is not None
    assert props["ele"] == 2500


def test_natural_extra_props_filters_low_peak():
    from reiseplan.themes.natural import SPEC
    el = {"type": "node", "id": 2, "tags": {"natural": "peak", "ele": "500"}}
    tags = el["tags"]
    result = SPEC.extra_props(el, tags, {"min_ele": 1500})
    assert result is None


def test_natural_extra_props_landscape_no_ele():
    from reiseplan.themes.natural import SPEC
    el = {"type": "node", "id": 3, "tags": {"natural": "mountain_range"}}
    tags = el["tags"]
    props = SPEC.extra_props(el, tags, {"min_ele": 1500})
    assert props is not None
    assert "ele" not in props
    assert props["natural"] == "mountain_range"


# ---------------------------------------------------------------------------
# extra_props — mining theme
# ---------------------------------------------------------------------------

def test_mining_extra_props_coal_mine():
    from reiseplan.themes.mining import SPEC
    el = {"type": "node", "id": 10, "tags": {"man_made": "mineshaft", "resource": "coal"}}
    tags = el["tags"]
    props = SPEC.extra_props(el, tags, {})
    assert props is not None
    assert props["commodity"] == "coal"
    assert props["mining_type"] == "mineshaft"


def test_mining_extra_props_quarry():
    from reiseplan.themes.mining import SPEC
    el = {"type": "way", "id": 20, "tags": {"landuse": "quarry", "resource": "limestone"}}
    tags = el["tags"]
    props = SPEC.extra_props(el, tags, {})
    assert props is not None
    assert props["mining_type"] == "quarry"
    assert props["commodity"] == "stone"


def test_mining_extra_props_unknown_resource():
    from reiseplan.themes.mining import SPEC
    el = {"type": "node", "id": 30, "tags": {"man_made": "mineshaft"}}
    tags = el["tags"]
    props = SPEC.extra_props(el, tags, {})
    assert props is not None
    assert props["commodity"] == ""


# ---------------------------------------------------------------------------
# extra_props — industry theme
# ---------------------------------------------------------------------------

def test_industry_extra_props_hydro_plant():
    from reiseplan.themes.industry import SPEC
    el = {"type": "node", "id": 40,
          "tags": {"power": "plant", "plant:source": "hydro"}}
    tags = el["tags"]
    props = SPEC.extra_props(el, tags, {})
    assert props is not None
    assert props["branch"] == "power_hydro"


def test_industry_extra_props_thermal_plant():
    from reiseplan.themes.industry import SPEC
    el = {"type": "node", "id": 41,
          "tags": {"power": "plant", "plant:source": "coal"}}
    tags = el["tags"]
    props = SPEC.extra_props(el, tags, {})
    assert props["branch"] == "power_thermal"


def test_industry_extra_props_steel_works():
    from reiseplan.themes.industry import SPEC
    el = {"type": "node", "id": 50,
          "tags": {"man_made": "works", "product": "steel"}}
    tags = el["tags"]
    props = SPEC.extra_props(el, tags, {})
    assert props["branch"] == "steel"


def test_industry_extra_props_generic_industrial():
    from reiseplan.themes.industry import SPEC
    el = {"type": "way", "id": 60,
          "tags": {"landuse": "industrial"}}
    tags = el["tags"]
    props = SPEC.extra_props(el, tags, {})
    assert props is not None
    assert props["branch"] == "industrial"


# ---------------------------------------------------------------------------
# thematic._build_features — integration
# ---------------------------------------------------------------------------

def test_build_features_natural_ridge(tmp_path):
    """Ridge way produces a LineString in the ridges layer."""
    from reiseplan.thematic import _build_features
    from reiseplan.themes.natural import SPEC

    el = {
        "type": "way", "id": 100,
        "tags": {"name": "Testgrat", "natural": "ridge"},
        "geometry": [{"lat": 46.0, "lon": 12.0}, {"lat": 46.1, "lon": 12.1}],
    }
    out = _build_features([el], SPEC, {}, {"min_ele": 1500})
    ridges = out.get("natural_ridges", [])
    assert len(ridges) == 1
    assert ridges[0]["geometry"]["type"] == "LineString"
    assert ridges[0]["properties"]["name"] == "Testgrat"


def test_build_features_mining_node(tmp_path):
    """Mine node produces a Point in the mineral_resources layer."""
    from reiseplan.thematic import _build_features
    from reiseplan.themes.mining import SPEC

    el = {
        "type": "node", "id": 200,
        "lat": 47.0, "lon": 15.0,
        "tags": {"man_made": "mineshaft", "resource": "salt"},
    }
    out = _build_features([el], SPEC, {}, {})
    points = out.get("mineral_resources", [])
    assert len(points) == 1
    assert points[0]["geometry"]["type"] == "Point"
    assert points[0]["properties"]["commodity"] == "salt"


def test_build_features_skips_unnamed_when_required():
    """require_name=True: elements without a name tag are skipped."""
    from reiseplan.thematic import _build_features
    from reiseplan.themes.natural import SPEC

    el = {
        "type": "node", "id": 300,
        "lat": 47.0, "lon": 15.0,
        "tags": {"natural": "peak", "ele": "2000"},  # no "name"
    }
    out = _build_features([el], SPEC, {}, {"min_ele": 1500})
    assert len(out["mountain_peaks"]) == 0


def test_build_features_includes_unnamed_when_not_required():
    """require_name=False: elements without a name are included."""
    from reiseplan.thematic import _build_features
    from reiseplan.themes.mining import SPEC

    el = {
        "type": "node", "id": 400,
        "lat": 48.0, "lon": 16.0,
        "tags": {"man_made": "mineshaft"},  # no "name"
    }
    out = _build_features([el], SPEC, {}, {})
    assert len(out["mineral_resources"]) == 1
