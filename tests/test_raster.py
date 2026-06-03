"""Tests for raster.py — GDAL subprocess wrappers.

Uses unittest.mock to avoid running actual GDAL processes.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import call, patch

import pytest

from reiseplan import raster


# ---------------------------------------------------------------------------
# _require — exits when tool is missing
# ---------------------------------------------------------------------------

def test_require_exits_when_missing():
    with patch("shutil.which", return_value=None):
        with pytest.raises(SystemExit):
            raster._require("ogr2ogr")


def test_require_returns_path_when_found():
    with patch("shutil.which", return_value="/usr/bin/gdalwarp"):
        result = raster._require("gdalwarp")
    assert result == "/usr/bin/gdalwarp"


# ---------------------------------------------------------------------------
# hillshade — correct CLI arguments
# ---------------------------------------------------------------------------

def test_hillshade_calls_gdaldem(tmp_path: Path):
    dem = tmp_path / "dem.tif"
    out = tmp_path / "hillshade.tif"
    with (
        patch("shutil.which", return_value="/usr/bin/gdaldem"),
        patch("subprocess.run") as mock_run,
    ):
        raster.hillshade(dem, out, z_factor=2.0, combined=True)

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "gdaldem" in args[0]
    assert "hillshade" in args
    assert "-combined" in args
    assert "-z" in args
    assert "2.0" in args


def test_hillshade_no_combined_flag(tmp_path: Path):
    dem = tmp_path / "dem.tif"
    out = tmp_path / "hs.tif"
    with (
        patch("shutil.which", return_value="/usr/bin/gdaldem"),
        patch("subprocess.run") as mock_run,
    ):
        raster.hillshade(dem, out, combined=False)

    args = mock_run.call_args[0][0]
    assert "-combined" not in args


# ---------------------------------------------------------------------------
# contours — interval argument passed correctly
# ---------------------------------------------------------------------------

def test_contours_passes_interval(tmp_path: Path):
    dem = tmp_path / "dem.tif"
    out = tmp_path / "contours.geojson"
    with (
        patch("shutil.which", return_value="/usr/bin/gdal_contour"),
        patch("subprocess.run") as mock_run,
    ):
        raster.contours(dem, out, interval=50.0, attribute="elev")

    args = mock_run.call_args[0][0]
    assert "-i" in args
    assert "50.0" in args
    assert "-a" in args
    assert "elev" in args


# ---------------------------------------------------------------------------
# warp_clip — te bbox and t_srs passed correctly
# ---------------------------------------------------------------------------

def test_warp_clip_with_te(tmp_path: Path):
    src = tmp_path / "src.tif"
    dst = tmp_path / "dst.tif"
    with (
        patch("shutil.which", return_value="/usr/bin/gdalwarp"),
        patch("subprocess.run") as mock_run,
    ):
        raster.warp_clip(
            src, dst,
            t_srs="EPSG:3844",
            te=(20.0, 44.0, 30.0, 50.0),
            te_srs="EPSG:4326",
        )

    args = mock_run.call_args[0][0]
    assert "-t_srs" in args
    assert "EPSG:3844" in args
    assert "-te" in args
    assert "20.0" in args


def test_warp_clip_without_te(tmp_path: Path):
    src = tmp_path / "src.tif"
    dst = tmp_path / "dst.tif"
    with (
        patch("shutil.which", return_value="/usr/bin/gdalwarp"),
        patch("subprocess.run") as mock_run,
    ):
        raster.warp_clip(src, dst)

    args = mock_run.call_args[0][0]
    assert "-te" not in args
