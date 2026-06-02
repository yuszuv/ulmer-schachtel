"""Tests for natural-feature German-name enrichment — pure functions, no network.

Coverage:
  fetch_natural._resolve_name_de    priority chain + suppress-when-equal + source
  fetch_natural._props              provenance fields wired through
  fetch_natural._qids_needing_labels which elements need a Wikidata lookup
"""

from __future__ import annotations

from reiseplan import fetch_natural as fn


# ---------------------------------------------------------------------------
# _resolve_name_de — priority, suppression, provenance
# ---------------------------------------------------------------------------

def test_osm_name_de_wins_over_wikidata():
    tags = {"name": "Carpați", "name:de": "Karpaten", "wikidata": "Q99"}
    name_de, src = fn._resolve_name_de("Carpați", tags, {"Q99": "Wikidata-Karpaten"})
    assert (name_de, src) == ("Karpaten", "osm")


def test_wikidata_fallback_when_no_osm_name_de():
    tags = {"name": "Carpați", "wikidata": "Q99"}
    name_de, src = fn._resolve_name_de("Carpați", tags, {"Q99": "Karpaten"})
    assert (name_de, src) == ("Karpaten", "wikidata")


def test_german_name_suppressed_when_equal_to_name():
    # Austrian feature: German label equals the local name → adds nothing.
    tags = {"name": "Fluchthorn", "wikidata": "Q668551"}
    name_de, src = fn._resolve_name_de("Fluchthorn", tags, {"Q668551": "Fluchthorn"})
    assert (name_de, src) == (None, None)


def test_osm_name_de_suppressed_when_equal_to_name():
    tags = {"name": "Donau", "name:de": "Donau"}
    name_de, src = fn._resolve_name_de("Donau", tags, {})
    assert (name_de, src) == (None, None)


def test_no_german_source_returns_none():
    tags = {"name": "Polovnik", "wikidata": "Q1"}
    name_de, src = fn._resolve_name_de("Polovnik", tags, {})  # QID not in map
    assert (name_de, src) == (None, None)


# ---------------------------------------------------------------------------
# _props — provenance fields present
# ---------------------------------------------------------------------------

def test_props_carries_provenance_fields():
    el = {
        "type": "node", "id": 7,
        "tags": {"name": "Carpați", "wikidata": "Q99", "natural": "mountain_range"},
    }
    props = fn._props(el, {"Q99": "Karpaten"})
    assert props["name"] == "Carpați"
    assert props["name_de"] == "Karpaten"
    assert props["name_de_src"] == "wikidata"
    assert props["wikidata"] == "Q99"


def test_props_without_wikidata_has_none_fields():
    el = {"type": "way", "id": 3, "tags": {"name": "Some Ridge", "natural": "ridge"}}
    props = fn._props(el, {})
    assert props["name_de"] is None
    assert props["name_de_src"] is None
    assert props["wikidata"] is None


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
    assert fn._qids_needing_labels(elements) == ["Q1", "Q4"]
