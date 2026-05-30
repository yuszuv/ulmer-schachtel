"""Tests für _rewrite_datasources (build-qfield Kern-Logik).

Prüft:
- alle Layer-Pfade werden korrekt umgeschrieben
- anderer XML-Inhalt bleibt unverändert
- fehlende Datenquelle führt zu SystemExit mit klarer Meldung
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from reiseplan_cli import GPKG_LAYERS, _rewrite_datasources


# --------------------------------------------------------------------------- #
# Hilfsfunktionen                                                              #
# --------------------------------------------------------------------------- #

def _mini_qgs(*layers: tuple[str, str]) -> str:
    """Minimales .qgs-XML-Snippet mit echten <datasource>-Tags erzeugen."""
    tags = "\n".join(
        f"  <datasource>../data/processed/{geojson}</datasource>"
        for _, geojson in layers
    )
    return f"<maplayer>\n{tags}\n</maplayer>"


# --------------------------------------------------------------------------- #
# Positiv-Tests                                                                #
# --------------------------------------------------------------------------- #

def test_rewrite_ersetzt_alle_layer():
    """Alle vier GPKG_LAYERS-Pfade werden korrekt umgeschrieben."""
    snippet = _mini_qgs(*GPKG_LAYERS)
    result = _rewrite_datasources(snippet, "reiseplan.gpkg")

    for layer_name, geojson_name in GPKG_LAYERS:
        # Original-Pfad muss weg sein
        assert f"../data/processed/{geojson_name}" not in result
        # GPKG-Verweis muss drin sein
        assert f"./reiseplan.gpkg|layername={layer_name}" in result


def test_rewrite_laesst_anderen_inhalt_unveraendert():
    """XML-Inhalt außerhalb der Datenquellen wird nicht angefasst."""
    snippet = _mini_qgs(*GPKG_LAYERS)
    snippet += "\n<anderes>unveraenderter Inhalt</anderes>"
    result = _rewrite_datasources(snippet, "reiseplan.gpkg")
    assert "<anderes>unveraenderter Inhalt</anderes>" in result


def test_rewrite_gpkg_dateiname_konfigurierbar():
    """Der GPKG-Dateiname kann beliebig gewählt werden."""
    snippet = _mini_qgs(*GPKG_LAYERS)
    result = _rewrite_datasources(snippet, "custom_bundle.gpkg")
    for layer_name, _ in GPKG_LAYERS:
        assert f"./custom_bundle.gpkg|layername={layer_name}" in result


# --------------------------------------------------------------------------- #
# Fehler-Tests                                                                 #
# --------------------------------------------------------------------------- #

def test_rewrite_fehler_bei_fehlender_quelle():
    """SystemExit mit klarer Meldung wenn eine Datenquelle nicht gefunden wird."""
    snippet = "<maplayer></maplayer>"   # keine datasource-Tags
    with pytest.raises(SystemExit, match="Erwartete Datenquelle nicht im .qgs gefunden"):
        _rewrite_datasources(snippet, "reiseplan.gpkg")


def test_rewrite_fehler_nennt_fehlenden_pfad():
    """Die Fehlermeldung enthält den konkreten Pfad, der nicht gefunden wurde."""
    snippet = "<maplayer></maplayer>"
    first_layer_name, first_geojson = GPKG_LAYERS[0]
    try:
        _rewrite_datasources(snippet, "reiseplan.gpkg")
    except SystemExit as exc:
        assert first_geojson in str(exc)
    else:
        pytest.fail("SystemExit erwartet")
