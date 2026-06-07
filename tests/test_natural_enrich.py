"""Tests for German-name enrichment — pure functions, no network.

After the thematic-pipeline refactor, the enrichment helpers live in
``reiseplan.enrich`` (resolve_name_de, _qids_needing_labels) and the
natural-theme-specific prop builder lives in ``reiseplan.themes.natural``.

Coverage:
  enrich.resolve_name_de        priority chain + suppress-when-equal + source
  enrich._qids_needing_labels   which elements need a Wikidata lookup
  themes/natural extra_props    provenance fields and ele parsing wired through
"""

from __future__ import annotations

from reiseplan.enrich import resolve_name_de, _qids_needing_labels
from reiseplan.wikidata import WikidataNames
from reiseplan.themes.natural import SPEC as _NATURAL_SPEC


def _names(label=None, wikipedia=None, wikivoyage=None) -> WikidataNames:
    """Concise WikidataNames factory for the resolve_name_de tests."""
    return WikidataNames(label_de=label, wikipedia_de=wikipedia, wikivoyage_de=wikivoyage)


# ---------------------------------------------------------------------------
# resolve_name_de — priority, suppression, provenance
# ---------------------------------------------------------------------------

def test_osm_name_de_wins_over_everything():
    tags = {"name": "Carpați", "name:de": "Karpaten", "wikidata": "Q99"}
    entity = _names(label="Label-Karpaten", wikipedia="Wiki-Karpaten")
    name_de, src = resolve_name_de("Carpați", tags, {"Q99": entity})
    assert (name_de, src) == ("Karpaten", "osm")


def test_wikipedia_beats_wikidata_label():
    # de.wikipedia title is the authoritative exonym; the bare label is fallback.
    tags = {"name": "Cluj-Napoca", "wikidata": "Q99"}
    entity = _names(label="Cluj-Napoca", wikipedia="Klausenburg")
    name_de, src = resolve_name_de("Cluj-Napoca", tags, {"Q99": entity})
    assert (name_de, src) == ("Klausenburg", "wikipedia")


def test_wikidata_label_when_no_wikipedia_article():
    tags = {"name": "Carpați", "wikidata": "Q99"}
    name_de, src = resolve_name_de("Carpați", tags, {"Q99": _names(label="Karpaten")})
    assert (name_de, src) == ("Karpaten", "wikidata")


def test_wikipedia_disambiguator_stripped():
    tags = {"name": "Bistrița-local", "wikidata": "Q99"}
    entity = _names(wikipedia="Bistrița (Stadt)")
    name_de, src = resolve_name_de("Bistrița-local", tags, {"Q99": entity})
    assert (name_de, src) == ("Bistrița", "wikipedia")


def test_german_name_suppressed_when_equal_to_name():
    # Austrian feature: German label equals the local name → adds nothing.
    tags = {"name": "Fluchthorn", "wikidata": "Q668551"}
    name_de, src = resolve_name_de("Fluchthorn", tags, {"Q668551": _names(label="Fluchthorn")})
    assert (name_de, src) == (None, None)


def test_osm_name_de_suppressed_when_equal_to_name():
    tags = {"name": "Donau", "name:de": "Donau"}
    name_de, src = resolve_name_de("Donau", tags, {})
    assert (name_de, src) == (None, None)


def test_no_german_source_returns_none():
    tags = {"name": "Polovnik", "wikidata": "Q1"}
    name_de, src = resolve_name_de("Polovnik", tags, {})  # QID not in map
    assert (name_de, src) == (None, None)


# ---------------------------------------------------------------------------
# natural theme extra_props — provenance fields + ele parsing
# ---------------------------------------------------------------------------

def _build_natural_props(el: dict, wikidata_de: dict, **opts) -> dict | None:
    """Build the props dict the same way thematic._build_features does."""
    tags = el.get("tags", {})
    name = tags.get("name")
    name_de, name_de_src = resolve_name_de(name, tags, wikidata_de)
    extra = _NATURAL_SPEC.extra_props(el, tags, {"min_ele": opts.get("min_ele", 1500)})
    if extra is None:
        return None
    return {
        "osm_id":      el.get("id"),
        "osm_type":    el.get("type"),
        "name":        name,
        "name_de":     name_de,
        "name_de_src": name_de_src,
        "wikidata":    tags.get("wikidata"),
        **extra,
    }


def test_props_carries_provenance_fields():
    el = {
        "type": "node", "id": 7,
        "tags": {"name": "Carpați", "wikidata": "Q99", "natural": "mountain_range"},
    }
    props = _build_natural_props(el, {"Q99": _names(wikipedia="Karpaten")})
    assert props is not None
    assert props["name"] == "Carpați"
    assert props["name_de"] == "Karpaten"
    assert props["name_de_src"] == "wikipedia"
    assert props["wikidata"] == "Q99"
    assert props["natural"] == "mountain_range"


def test_props_without_wikidata_has_none_fields():
    el = {
        "type": "way",
        "id": 3,
        "tags": {"name": "Some Ridge", "natural": "ridge"},
        "geometry": [{"lon": 25.0, "lat": 45.0}, {"lon": 25.01, "lat": 45.0}],
    }
    props = _build_natural_props(el, {})
    assert props is not None
    assert props["name_de"] is None
    assert props["name_de_src"] is None
    assert props["wikidata"] is None


def test_peak_below_min_ele_returns_none():
    """extra_props returns None to skip a peak below the min_ele threshold."""
    el = {
        "type": "node", "id": 1,
        "tags": {"name": "Small Hill", "natural": "peak", "ele": "800"},
    }
    result = _build_natural_props(el, {}, min_ele=1500)
    assert result is None


def test_peak_above_min_ele_included():
    el = {
        "type": "node", "id": 2,
        "tags": {"name": "High Peak", "natural": "peak", "ele": "2500"},
    }
    props = _build_natural_props(el, {}, min_ele=1500)
    assert props is not None
    assert props["ele"] == 2500


# ---------------------------------------------------------------------------
# _qids_needing_labels — only named, name:de-less, wikidata-bearing elements
# ---------------------------------------------------------------------------

def test_qids_needing_labels_filters_and_dedups():
    elements = [
        {"tags": {"name": "A", "wikidata": "Q1"}},               # needs lookup
        {"tags": {"name": "B", "wikidata": "Q2", "name:de": "B-de"}},  # has name:de → skip
        {"tags": {"name": "C"}},                                  # no QID → skip
        {"tags": {"wikidata": "Q3"}},                             # no name → skip
        {"tags": {"name": "D", "wikidata": "Q1"}},               # dup QID → unique
        {"tags": {"name": "E", "wikidata": "Q4"}},               # needs lookup
    ]
    assert _qids_needing_labels(elements) == ["Q1", "Q4"]
