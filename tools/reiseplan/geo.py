"""Geometry helpers — Overpass element → GeoJSON coordinate shapes.

Shared by all thematic fetchers; keeps each theme module thin.

All output coordinates follow GeoJSON convention: [lon, lat] (EPSG:4326).
Reprojection to EPSG:3844 happens later via ogr2ogr (see packaging.py).
"""

from __future__ import annotations

import re


def way_to_linestring(el: dict) -> list[list[float]] | None:
    """Extract [[lon, lat], …] from a way's ``geometry`` array ({lat,lon} dicts).

    Requires ``out geom;`` in the Overpass query.  Returns ``None`` if the
    geometry array is absent or has fewer than 2 points.
    """
    geom = el.get("geometry")
    if not geom:
        return None
    coords = [
        [pt["lon"], pt["lat"]]
        for pt in geom
        if "lon" in pt and "lat" in pt
    ]
    return coords if len(coords) >= 2 else None


def node_to_point(el: dict) -> list[float] | None:
    """Extract [lon, lat] from a node element.

    Requires ``out geom;`` in the Overpass query (``out tags;`` omits lat/lon).
    Returns ``None`` if coordinates are missing.
    """
    lat, lon = el.get("lat"), el.get("lon")
    if lat is None or lon is None:
        return None
    return [float(lon), float(lat)]


def centroid_of(el: dict) -> list[float] | None:
    """Extract [lon, lat] from the ``center`` field of a way or area element.

    Overpass returns a ``center`` dict when the query includes ``out center;``
    or ``out tags center;``.  Used to reduce heavy area polygons (quarries,
    industrial zones) to a single anchor Point for atlas piktogram layers.
    Returns ``None`` if the center is absent.
    """
    center = el.get("center", {})
    lat, lon = center.get("lat"), center.get("lon")
    if lat is None or lon is None:
        return None
    return [float(lon), float(lat)]


def parse_ele(raw: str) -> int | str | None:
    """Parse an OSM ``ele`` tag value to an integer metres value.

    Handles formats like ``"2663"``, ``"2 663"``, ``"2663 m"``, ``"2663.5"``.
    Returns the raw string on parse failure so callers can still include the
    feature.  Returns ``None`` if the input is empty or whitespace-only.
    """
    cleaned = raw.strip()
    if not cleaned:
        return None
    # Take the first whitespace-separated token, strip trailing unit letters.
    token = cleaned.split()[0].replace(",", ".").rstrip("m").strip()
    try:
        return int(float(token))
    except ValueError:
        return raw


def parse_population(raw: str) -> int | None:
    """Parse an OSM ``population`` tag value to an integer.

    Handles the common OSM variants — plain ``"50000"``, thousands separators
    (``"50.000"``, ``"50 000"``, ``"50,000"``), approximation marks
    (``"~50000"``) and trailing year annotations (``"50000 (2011)"``).  The year
    in parentheses is dropped first, then every non-digit is stripped.  Returns
    ``None`` for empty or digit-free input.
    """
    before_paren = raw.split("(")[0]
    digits = re.sub(r"\D", "", before_paren)
    return int(digits) if digits else None
