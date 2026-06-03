"""Tests for tiles.py — BBox, tile_grid, fetch_tiled (offline path).

No network access — online fetch path is not tested here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reiseplan.tiles import BBox, tile_grid, fetch_tiled
from reiseplan.result import Ok, Err


# ---------------------------------------------------------------------------
# BBox
# ---------------------------------------------------------------------------

def test_bbox_as_tuple():
    bb = BBox(south=1.0, west=2.0, north=3.0, east=4.0)
    assert bb.as_tuple() == (1.0, 2.0, 3.0, 4.0)


def test_bbox_immutable():
    bb = BBox(south=0.0, west=0.0, north=1.0, east=1.0)
    with pytest.raises((AttributeError, TypeError)):
        bb.south = 99.0  # type: ignore


# ---------------------------------------------------------------------------
# tile_grid — coverage and overlap
# ---------------------------------------------------------------------------

def test_tile_grid_covers_roi():
    roi = BBox(south=44.0, west=20.0, north=50.0, east=28.0)
    tiles = tile_grid(roi, step_deg=4.0, overlap_deg=0.0)
    # All tiles combined should cover the full ROI.
    assert all(t.south >= roi.south for t in tiles)
    assert all(t.west  >= roi.west  for t in tiles)
    assert all(t.north <= roi.north + 4.0 + 0.1 for t in tiles)
    assert all(t.east  <= roi.east  + 4.0 + 0.1 for t in tiles)


def test_tile_grid_count_small_roi():
    # 2 ° wide × 4 ° tall, step 4 ° → should produce 1 tile per column/row
    roi = BBox(south=44.0, west=20.0, north=45.0, east=22.0)
    tiles = tile_grid(roi, step_deg=4.0, overlap_deg=0.0)
    assert len(tiles) >= 1


def test_tile_grid_overlap_widens_tiles():
    roi = BBox(south=44.0, west=20.0, north=48.0, east=24.0)
    tiles_no_overlap  = tile_grid(roi, step_deg=4.0, overlap_deg=0.0)
    tiles_with_overlap = tile_grid(roi, step_deg=4.0, overlap_deg=0.5)
    # Overlap tiles must be at least as wide/tall.
    for tn, to in zip(tiles_no_overlap, tiles_with_overlap):
        assert to.north >= tn.north
        assert to.east  >= tn.east


def test_tile_grid_natural_roi_count():
    # The k.u.k. ROI at 4°×4° step should produce the same count as the old
    # fetch_natural._tile_grid() would.  k.u.k. extent ≈ 8.5° lat × 20.5° lon
    # → ceil(8.5/4) * ceil(20.5/4) = 3 * 6 = 18 tiles.
    from reiseplan.themes import KUK_ROI
    tiles = tile_grid(KUK_ROI, step_deg=4.0, overlap_deg=0.1)
    assert len(tiles) == 18


# ---------------------------------------------------------------------------
# fetch_tiled — offline path
# ---------------------------------------------------------------------------

def test_fetch_tiled_offline_reads_cache(tmp_path: Path):
    elements = [{"type": "node", "id": 1, "tags": {"name": "Test"}}]
    cache = {"elements": elements, "generated": "2026-01-01T00:00:00Z"}
    cache_path = tmp_path / "osm_test.json"
    cache_path.write_text(json.dumps(cache), encoding="utf-8")

    roi = BBox(44.0, 20.0, 48.0, 24.0)
    result = fetch_tiled(roi, [], cache_path, offline=True)
    assert isinstance(result, Ok)
    assert result.value == elements


def test_fetch_tiled_offline_missing_cache(tmp_path: Path):
    roi = BBox(44.0, 20.0, 48.0, 24.0)
    result = fetch_tiled(roi, [], tmp_path / "missing.json", offline=True)
    assert isinstance(result, Err)
    assert "--offline" in result.message


def test_fetch_tiled_offline_corrupt_cache(tmp_path: Path):
    cache_path = tmp_path / "bad.json"
    cache_path.write_text("not json", encoding="utf-8")
    roi = BBox(44.0, 20.0, 48.0, 24.0)
    result = fetch_tiled(roi, [], cache_path, offline=True)
    assert isinstance(result, Err)
