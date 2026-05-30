"""Tests for rewrite_datasources (build-qfield core logic).

Verifies:
- all layer paths are correctly rewritten
- other XML content is left unchanged
- a missing datasource raises SystemExit with a clear message
"""

from __future__ import annotations

import pytest

from reiseplan.packaging import GPKG_LAYERS, rewrite_datasources


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mini_qgs(*layers: tuple[str, str]) -> str:
    """Minimal .qgs XML snippet with real <datasource> tags."""
    tags = "\n".join(
        f"  <datasource>../data/processed/{geojson}</datasource>"
        for _, geojson in layers
    )
    return f"<maplayer>\n{tags}\n</maplayer>"


# ---------------------------------------------------------------------------
# Positive tests
# ---------------------------------------------------------------------------

def test_rewrite_ersetzt_alle_layer():
    """All four GPKG_LAYERS paths are correctly rewritten."""
    snippet = _mini_qgs(*GPKG_LAYERS)
    result = rewrite_datasources(snippet, "reiseplan.gpkg")

    for layer_name, geojson_name in GPKG_LAYERS:
        assert f"../data/processed/{geojson_name}" not in result
        assert f"./reiseplan.gpkg|layername={layer_name}" in result


def test_rewrite_laesst_anderen_inhalt_unveraendert():
    """XML content outside the datasources is not touched."""
    snippet = _mini_qgs(*GPKG_LAYERS)
    snippet += "\n<anderes>unveraenderter Inhalt</anderes>"
    result = rewrite_datasources(snippet, "reiseplan.gpkg")
    assert "<anderes>unveraenderter Inhalt</anderes>" in result


def test_rewrite_gpkg_dateiname_konfigurierbar():
    """The GPKG filename can be chosen freely."""
    snippet = _mini_qgs(*GPKG_LAYERS)
    result = rewrite_datasources(snippet, "custom_bundle.gpkg")
    for layer_name, _ in GPKG_LAYERS:
        assert f"./custom_bundle.gpkg|layername={layer_name}" in result


# ---------------------------------------------------------------------------
# Error tests
# ---------------------------------------------------------------------------

def test_rewrite_fehler_bei_fehlender_quelle():
    """SystemExit with clear message when a datasource is not found."""
    snippet = "<maplayer></maplayer>"
    with pytest.raises(SystemExit, match="Erwartete Datenquelle nicht im .qgs gefunden"):
        rewrite_datasources(snippet, "reiseplan.gpkg")


def test_rewrite_fehler_nennt_fehlenden_pfad():
    """The error message contains the concrete missing path."""
    snippet = "<maplayer></maplayer>"
    first_layer_name, first_geojson = GPKG_LAYERS[0]
    try:
        rewrite_datasources(snippet, "reiseplan.gpkg")
    except SystemExit as exc:
        assert first_geojson in str(exc)
    else:
        pytest.fail("SystemExit erwartet")
