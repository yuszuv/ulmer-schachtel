"""ROI tiling + timed Overpass fetch + JSON cache.

Extracted from fetch_natural.py and generalised for all thematic fetchers.

BBox          — immutable (south, west, north, east) value object.
tile_grid     — generate overlapping degree-tiles covering a BBox.
fetch_tiled   — iterate tiles × query-builders, dedup by (type,id), write cache.

The ``fetch_tiled`` caller provides one or more query-builder callables
``(south, west, north, east) → Overpass QL string``.  Each builder is called
per tile with a politeness pause between calls.  Per-tile failures are
reported but do not abort the run; a fully empty result (all tiles failed /
no features anywhere) is surfaced as an ``Err``.
"""

from __future__ import annotations

import datetime
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .overpass import post_overpass
from .result import Err, Ok, Result

# Defaults match fetch_natural.py constants so the natural-feature behaviour
# is preserved exactly when ThemeSpec uses the default values.
_DEFAULT_TILE_STEP    = 4.0
_DEFAULT_TILE_OVERLAP = 0.1
_DEFAULT_PAUSE_S      = 2.0


@dataclass(frozen=True)
class BBox:
    """Immutable bounding box in WGS84 degrees.

    Attribute order matches the Overpass QL convention: south, west, north, east.
    """
    south: float
    west:  float
    north: float
    east:  float

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.south, self.west, self.north, self.east)


def tile_grid(
    roi: BBox,
    *,
    step_deg:    float = _DEFAULT_TILE_STEP,
    overlap_deg: float = _DEFAULT_TILE_OVERLAP,
) -> list[BBox]:
    """Generate overlapping ``step_deg`` × ``step_deg`` tiles covering ``roi``.

    A small overlap ensures features near tile edges are not missed.
    Returns ``BBox`` objects with 6-decimal-place precision.
    """
    tiles: list[BBox] = []
    lat = roi.south
    while lat < roi.north:
        n = min(lat + step_deg + overlap_deg, roi.north + overlap_deg)
        lon = roi.west
        while lon < roi.east:
            e = min(lon + step_deg + overlap_deg, roi.east + overlap_deg)
            tiles.append(BBox(
                south=round(lat, 6),
                west=round(lon, 6),
                north=round(n, 6),
                east=round(e, 6),
            ))
            lon += step_deg
        lat += step_deg
    return tiles


def fetch_tiled(
    roi: BBox,
    query_builders: list[Callable[[float, float, float, float], str]],
    cache_path: Path,
    offline: bool,
    *,
    step_deg:    float = _DEFAULT_TILE_STEP,
    overlap_deg: float = _DEFAULT_TILE_OVERLAP,
    pause_s:     float = _DEFAULT_PAUSE_S,
    label:       str   = "features",
) -> Result[list[dict]]:
    """Return a deduplicated flat list of Overpass elements — from cache or API.

    Online: iterates the tile grid, calling each query builder per tile (with
    ``pause_s`` between calls for politeness).  Elements are deduplicated by
    ``(type, id)`` so features near tile edges appear exactly once.  The
    combined list is written to ``cache_path`` for ``--offline`` rebuilds.

    Offline: reads ``cache_path`` directly — no network access.

    Returns ``Err`` if the cache is missing (offline) or if the combined
    result is empty (all tiles failed or no matching features in the ROI).
    """
    if offline:
        if not cache_path.is_file():
            return Err(f"--offline, aber Cache fehlt: {cache_path}")
        print(f"[offline] lese Roh-Cache: {cache_path}")
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            return Ok(cached["elements"])
        except (json.JSONDecodeError, KeyError) as exc:
            return Err(f"Cache kein gültiges JSON: {exc}")

    tiles = tile_grid(roi, step_deg=step_deg, overlap_deg=overlap_deg)
    total_calls = len(tiles) * len(query_builders)
    print(
        f"[online]  {len(tiles)} Kacheln à {step_deg}°×{step_deg}°"
        f" × {len(query_builders)} Abfragen = {total_calls} Overpass-Calls …"
    )

    seen:         set[tuple[str, int]] = set()
    all_elements: list[dict]           = []
    failed:       list[str]            = []

    for i, tile in enumerate(tiles):
        if i:
            time.sleep(pause_s)
        s, w, n, e = tile.south, tile.west, tile.north, tile.east
        tile_label = f"({s:.1f},{w:.1f})–({n:.1f},{e:.1f})"

        for j, builder in enumerate(query_builders):
            if j:
                time.sleep(pause_s)
            result = post_overpass(builder(s, w, n, e))
            if isinstance(result, Err):
                tag = f"{tile_label} q{j + 1}"
                print(f"  [{i + 1:2d}/{len(tiles)}] {tag}: SKIP — {result.message}")
                failed.append(tag)
                continue
            elements = result.value.get("elements", [])
            new = 0
            for el in elements:
                key = (el.get("type", ""), el.get("id", 0))
                if key not in seen:
                    seen.add(key)
                    all_elements.append(el)
                    new += 1
            print(f"  [{i + 1:2d}/{len(tiles)}] {tile_label} q{j + 1}: "
                  f"{len(elements)} (+{new} new)")

    if failed:
        print(f"[warn]    {len(failed)} fehlgeschlagene Abfragen:")
        for f in failed:
            print(f"          · {f}")

    if not all_elements:
        return Err(f"Keine {label} gefunden – Abbruch.")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_obj = {
        "generated":       datetime.datetime.now(datetime.UTC).isoformat(),
        "tile_count":      len(tiles),
        "query_builders":  len(query_builders),
        "skipped_queries": len(failed),
        "element_count":   len(all_elements),
        "elements":        all_elements,
    }
    cache_path.write_text(
        json.dumps(cache_obj, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[cache]   {len(all_elements)} Elemente → {cache_path}")
    return Ok(all_elements)
