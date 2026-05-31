"""Tests for the WikiVoyage ingest — pure functions only, no network.

Coverage:
  regions.COUNTY_TO_REGION       integrity of the county→region mapping
  wikivoyage.parse_places        dedup, coord fallback, population, name:de
  wikivoyage._trim_summary       whitespace collapse + length cap
  wikivoyage._requested_title_map redirect/normalisation back-mapping
  build_marker_styles._hex_to_rgba / build_wikivoyage  style generation
"""

from __future__ import annotations

from reiseplan import wikivoyage
from reiseplan.regions import COUNTY_TO_REGION, HISTORICAL_REGIONS


# ---------------------------------------------------------------------------
# regions
# ---------------------------------------------------------------------------

def test_every_county_mapped_exactly_once():
    """41 Județe + Bukarest = 42 Kreiscodes, kein Kreis doppelt zugeordnet."""
    flat = [code for codes in HISTORICAL_REGIONS.values() for code in codes]
    assert len(flat) == 42
    assert len(set(flat)) == 42           # keine Doppelung
    assert len(COUNTY_TO_REGION) == 42


def test_county_to_region_inverts_the_mapping():
    assert COUNTY_TO_REGION["RO-TM"] == "Banat"
    assert COUNTY_TO_REGION["RO-SB"] == "Siebenbürgen"
    assert COUNTY_TO_REGION["RO-SM"] == "Sathmar/Marmarosch"
    # all region values are valid keys of HISTORICAL_REGIONS
    assert set(COUNTY_TO_REGION.values()) == set(HISTORICAL_REGIONS)


# ---------------------------------------------------------------------------
# build_region_query
# ---------------------------------------------------------------------------

def test_build_region_query_unions_all_counties():
    q = wikivoyage.build_region_query(("RO-TM", "RO-CS"))
    assert '["ISO3166-2"="RO-TM"]' in q
    assert '["ISO3166-2"="RO-CS"]' in q
    assert 'place"~"^(city|town)$"' in q
    assert "out tags center;" in q


# ---------------------------------------------------------------------------
# parse_places
# ---------------------------------------------------------------------------

def test_parse_places_extracts_tags_and_handles_center_and_dedup():
    by_region = {
        "Banat": {"elements": [
            # node with direct lat/lon, full tags
            {"tags": {"name": "Timișoara", "name:de": "Temeswar",
                      "place": "city", "population": "319 279",
                      "wikidata": "Q83404"},
             "lat": 45.75, "lon": 21.23},
            # way/relation: only center → must still resolve
            {"tags": {"name": "Lugoj", "place": "town"},
             "center": {"lat": 45.69, "lon": 21.90}},
            # no name → skipped
            {"tags": {"place": "town"}, "lat": 1.0, "lon": 1.0},
            # no coords → skipped
            {"tags": {"name": "Geisterstadt", "place": "town"}},
        ]},
        "Siebenbürgen": {"elements": [
            # duplicate QID across regions → kept only once (first wins: Banat)
            {"tags": {"name": "Timișoara (dupe)", "wikidata": "Q83404"},
             "lat": 45.75, "lon": 21.23},
            {"tags": {"name": "Sibiu", "place": "city"}, "lat": 45.79, "lon": 24.15},
        ]},
    }
    places = wikivoyage.parse_places(by_region)
    by_name = {p["name"]: p for p in places}

    assert set(by_name) == {"Timișoara", "Lugoj", "Sibiu"}
    assert by_name["Timișoara"]["name_de"] == "Temeswar"
    assert by_name["Timișoara"]["population"] == 319_279   # spaces stripped
    assert by_name["Timișoara"]["region"] == "Banat"
    assert by_name["Lugoj"]["lon"] == 21.90               # center fallback
    assert by_name["Sibiu"]["population"] is None          # absent → None


def test_parse_places_keeps_zero_population_absent_not_zero():
    by_region = {"Moldau": {"elements": [
        {"tags": {"name": "X", "population": "nineteen"}, "lat": 1.0, "lon": 2.0},
    ]}}
    place = wikivoyage.parse_places(by_region)[0]
    assert place["population"] is None   # non-numeric ignored, not crashed


# ---------------------------------------------------------------------------
# _trim_summary
# ---------------------------------------------------------------------------

def test_trim_summary_collapses_whitespace():
    assert wikivoyage._trim_summary("Hallo\n\n  Welt  ") == "Hallo Welt"


def test_trim_summary_caps_length():
    long = "a " * 1000
    out = wikivoyage._trim_summary(long)
    assert len(out) <= wikivoyage._SUMMARY_MAXLEN + 2  # plus " …"
    assert out.endswith("…")


# ---------------------------------------------------------------------------
# _requested_title_map (normalisation + redirect chaining)
# ---------------------------------------------------------------------------

def test_requested_title_map_chains_normalisation_and_redirect():
    query = {
        "normalized": [{"from": "sibiu", "to": "Sibiu"}],
        "redirects": [{"from": "Sibiu", "to": "Hermannstadt"}],
    }
    mapping = wikivoyage._requested_title_map(query, ["sibiu", "Cluj"])
    # final article title maps back to what we originally asked for
    assert mapping["Hermannstadt"] == "sibiu"
    assert mapping["Cluj"] == "Cluj"


# ---------------------------------------------------------------------------
# Style generation
# ---------------------------------------------------------------------------

def test_hex_to_rgba():
    import importlib.util
    import sys

    from reiseplan.paths import QGIS_DIR

    spec = importlib.util.spec_from_file_location(
        "build_marker_styles", QGIS_DIR / "styles" / "build_marker_styles.py"
    )
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so the @dataclass in the module can resolve its own
    # __module__ in sys.modules (dataclasses looks it up at class-creation time).
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    assert mod._hex_to_rgba("#b5503c") == "181,80,60,255"

    qml = mod.build_wikivoyage()
    assert 'styleCategories="Symbology|Labeling|MapTips"' in qml
    # one rule per historical region
    assert qml.count("<rule ") == len(HISTORICAL_REGIONS)
    assert "&quot;region&quot; = 'Banat'" in qml
