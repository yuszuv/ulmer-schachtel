#!/usr/bin/env python3
"""Shared schema and loader for the hand-maintained CFR timetable.

Single source of truth for ``data/processed/timetable.csv`` — used by both
the ingest script (``fetch_cfr_data.py``: scaffold + merge into
``rail_lines.geojson``) and the display CLI (``reiseplan_cli.py timetable``).
"""

from __future__ import annotations

import csv
from pathlib import Path

from _paths import PROCESSED

TIMETABLE_PATH = PROCESSED / "timetable.csv"

# Column schema for timetable.csv. ``route_id`` is the join key to the rail
# lines; from_city/to_city/via are pre-filled by the scaffold step, all other
# fields are maintained by hand.
#
# ``approx`` explicitly lists (comma-separated) which time fields are estimates
# — a subset of {dep, arr}. Empty means both times are authoritative.
# Replaces the earlier free-text heuristic ("ca." in notes) that incorrectly
# marked the departure as approximate when only the arrival was uncertain.
TIMETABLE_COLUMNS: tuple[str, ...] = (
    "route_id", "from_city", "to_city", "days",
    "dep_time", "arr_time", "duration", "via", "train", "approx", "notes",
)

# Fields merged from the timetable into each ``rail_lines`` GeoJSON feature.
TIMETABLE_FIELDS: tuple[str, ...] = (
    "days", "dep_time", "arr_time", "duration", "via", "train", "approx",
)


def load_timetable(path: Path = TIMETABLE_PATH) -> dict[str, dict]:
    """Return ``route_id`` → timetable row. Empty dict if the file is missing."""
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return {row["route_id"]: row for row in csv.DictReader(f)}


def approx_fields(row: dict) -> frozenset[str]:
    """Return which time fields in this row are estimates — subset of {dep, arr}."""
    raw = (row.get("approx") or "").replace(";", ",")
    return frozenset(token.strip() for token in raw.split(",") if token.strip())
