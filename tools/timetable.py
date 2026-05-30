#!/usr/bin/env python3
"""Gemeinsames Schema + Laden der handgepflegten CFR-Timetable.

Single source of truth für ``data/processed/timetable.csv`` – genutzt sowohl
vom Ingest (``fetch_cfr_data.py``: Scaffold + Merge in ``rail_lines.geojson``)
als auch von der Anzeige (``reiseplan_cli.py`` ``timetable``).
"""

from __future__ import annotations

import csv
from pathlib import Path

from _paths import PROCESSED

TIMETABLE_PATH = PROCESSED / "timetable.csv"

# Spaltenschema der timetable.csv. ``route_id`` ist der Schlüssel zu den
# Magistralen; from_city/to_city/via werden beim Scaffold vorbefüllt, die
# übrigen Felder vom Menschen.
#
# ``approx`` listet *explizit* (kommasepariert), welche Zeitfelder nur
# Richtwerte sind – Teilmenge von {dep, arr}. Leer = beide Zeiten verbindlich.
# Das ersetzt die frühere Freitext-Heuristik ("ca." in notes), die u. a. die
# Abfahrt mit-markierte, wenn nur die Ankunft unsicher war.
TIMETABLE_COLUMNS: tuple[str, ...] = (
    "route_id", "from_city", "to_city", "days",
    "dep_time", "arr_time", "duration", "via", "train", "approx", "notes",
)

# Felder, die aus der Timetable in jedes ``rail_lines``-Feature gemergt werden.
TIMETABLE_FIELDS: tuple[str, ...] = (
    "days", "dep_time", "arr_time", "duration", "via", "train", "approx",
)


def load_timetable(path: Path = TIMETABLE_PATH) -> dict[str, dict]:
    """``route_id`` → Timetable-Zeile. Leeres Dict, wenn die Datei fehlt."""
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return {row["route_id"]: row for row in csv.DictReader(f)}


def approx_fields(row: dict) -> frozenset[str]:
    """Welche Zeitfelder dieser Zeile sind Richtwerte? Teilmenge von {dep, arr}."""
    raw = (row.get("approx") or "").replace(";", ",")
    return frozenset(token.strip() for token in raw.split(",") if token.strip())
