"""Tests for rewrite_datasources (build-qfield core logic).

Verifies:
- all vector layer paths are correctly rewritten to GPKG layer references
- the raster path is rewritten to a local filename reference
- both historische_reiche entries map to distinct GPKG layer names
- other XML content is left unchanged
- a missing datasource raises SystemExit with a clear message
"""

from __future__ import annotations

import pytest

from reiseplan.packaging import LAYERS, RASTER_FILENAME, RASTER_QGS_TOKEN, rewrite_datasources


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _full_qgs() -> str:
    """Minimal .qgs XML snippet containing all expected datasource tokens."""
    tags = "\n".join(
        f"  <datasource>{layer.qgs_token}</datasource>"
        for layer in LAYERS
    )
    tags += f"\n  <datasource>{RASTER_QGS_TOKEN}</datasource>"
    return f"<maplayer>\n{tags}\n</maplayer>"


# ---------------------------------------------------------------------------
# Positive tests
# ---------------------------------------------------------------------------

def test_rewrite_ersetzt_alle_vektorlayer():
    """All LAYERS token paths are rewritten to GPKG layer references."""
    snippet = _full_qgs()
    result = rewrite_datasources(snippet, "reiseplan.gpkg")

    for layer in LAYERS:
        assert layer.qgs_token not in result, f"Token not rewritten: {layer.qgs_token!r}"
        assert f"./reiseplan.gpkg|layername={layer.gpkg_name}" in result


def test_rewrite_ersetzt_raster():
    """The raster path is rewritten to a local filename."""
    snippet = _full_qgs()
    result = rewrite_datasources(snippet, "reiseplan.gpkg")

    assert RASTER_QGS_TOKEN not in result
    assert f"./{RASTER_FILENAME}" in result


def test_historische_reiche_verschiedene_layer_namen():
    """The two historische_reiche sources get distinct GPKG layer names."""
    snippet = _full_qgs()
    result = rewrite_datasources(snippet, "reiseplan.gpkg")

    assert "./reiseplan.gpkg|layername=historische_reiche" in result
    assert "./reiseplan.gpkg|layername=historische_reiche_merged" in result


def test_rewrite_laesst_anderen_inhalt_unveraendert():
    """XML content outside the datasources is not touched."""
    snippet = _full_qgs()
    snippet += "\n<anderes>unveraenderter Inhalt</anderes>"
    result = rewrite_datasources(snippet, "reiseplan.gpkg")
    assert "<anderes>unveraenderter Inhalt</anderes>" in result


def test_rewrite_gpkg_dateiname_konfigurierbar():
    """The GPKG filename can be chosen freely."""
    snippet = _full_qgs()
    result = rewrite_datasources(snippet, "custom_bundle.gpkg")
    for layer in LAYERS:
        assert f"./custom_bundle.gpkg|layername={layer.gpkg_name}" in result


def test_kein_relativer_datenpfad_verbleibt():
    """After rewriting, no ../data/ or ../historische_reiche references remain."""
    snippet = _full_qgs()
    result = rewrite_datasources(snippet, "reiseplan.gpkg")
    assert "../data/" not in result
    assert "../historische_reiche" not in result


# ---------------------------------------------------------------------------
# Error tests
# ---------------------------------------------------------------------------

def test_rewrite_fehler_bei_fehlendem_vektorlayer():
    """SystemExit with clear message when a vector datasource is not found."""
    snippet = "<maplayer></maplayer>"
    with pytest.raises(SystemExit, match="Erwartete Datenquelle nicht im .qgs gefunden"):
        rewrite_datasources(snippet, "reiseplan.gpkg")


def test_rewrite_fehler_bei_fehlendem_raster():
    """SystemExit with clear message when the raster datasource is not found."""
    # Include all vector tokens but omit the raster.
    tags = "\n".join(
        f"  <datasource>{layer.qgs_token}</datasource>"
        for layer in LAYERS
    )
    snippet = f"<maplayer>\n{tags}\n</maplayer>"
    with pytest.raises(SystemExit, match="Erwartete Raster-Quelle nicht im .qgs gefunden"):
        rewrite_datasources(snippet, "reiseplan.gpkg")


def test_rewrite_fehler_nennt_fehlenden_pfad():
    """The error message contains the concrete missing path."""
    snippet = "<maplayer></maplayer>"
    try:
        rewrite_datasources(snippet, "reiseplan.gpkg")
    except SystemExit as exc:
        # The first layer's token must appear in the error.
        assert LAYERS[0].qgs_token in str(exc)
    else:
        pytest.fail("SystemExit erwartet")
