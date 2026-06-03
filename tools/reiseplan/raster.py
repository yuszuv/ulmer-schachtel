"""Thin GDAL subprocess wrappers — raster processing for terrain and land cover.

Each function wraps exactly one GDAL CLI tool.  The style mirrors
``packaging.GpkgBuilder``: ``shutil.which`` guard first, then
``subprocess.run`` with ``check=True`` so any GDAL error aborts loudly.

All functions accept plain ``pathlib.Path`` objects and stringify them before
passing to the CLI.  The caller is responsible for ensuring parent directories
exist (use ``path.parent.mkdir(parents=True, exist_ok=True)``).

Available GDAL tools required:
    gdalwarp, gdalbuildvrt, gdaldem, gdal_contour, gdal_translate

GDAL 3.13+ is available on the development machine (verified in planning).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _require(tool: str) -> str:
    """Return the full path to *tool* or exit with a helpful message."""
    path = shutil.which(tool)
    if path is None:
        print(
            f"  ✗ '{tool}' not found — please install GDAL "
            "(pacman -S gdal  /  apt install gdal-bin).",
            file=sys.stderr,
        )
        sys.exit(1)
    return path


def _run(args: list[str]) -> None:
    """Run a subprocess, streaming output; raise on non-zero exit."""
    subprocess.run(args, check=True)


# ---------------------------------------------------------------------------
# VRT mosaic
# ---------------------------------------------------------------------------

def buildvrt(inputs: list[Path], out: Path) -> None:
    """Assemble multiple rasters into a VRT mosaic.

    ``gdalbuildvrt`` is used to create a virtual mosaic from individual
    DEM tiles before clipping / warping to the project extent.
    """
    _run([
        _require("gdalbuildvrt"),
        str(out),
        *(str(p) for p in inputs),
    ])


# ---------------------------------------------------------------------------
# Clip / reproject
# ---------------------------------------------------------------------------

def warp_clip(
    src: Path,
    dst: Path,
    *,
    t_srs: str = "EPSG:3844",
    te: tuple[float, float, float, float] | None = None,
    te_srs: str = "EPSG:4326",
    resampling: str = "bilinear",
    nodata: float | None = None,
    compress: str = "LZW",
) -> None:
    """Clip and reproject a raster with ``gdalwarp``.

    ``te`` is (xmin, ymin, xmax, ymax) in ``te_srs`` CRS.  When ``None``, no
    spatial extent clipping is applied (full extent of ``src`` is kept).
    """
    args = [
        _require("gdalwarp"),
        "-t_srs", t_srs,
        "-r", resampling,
        "-co", f"COMPRESS={compress}",
        "-overwrite",
    ]
    if te is not None:
        xmin, ymin, xmax, ymax = te
        args += ["-te", str(xmin), str(ymin), str(xmax), str(ymax),
                 "-te_srs", te_srs]
    if nodata is not None:
        args += ["-dstnodata", str(nodata)]
    args += [str(src), str(dst)]
    _run(args)


# ---------------------------------------------------------------------------
# Hillshade
# ---------------------------------------------------------------------------

def hillshade(
    dem: Path,
    out: Path,
    *,
    z_factor: float = 2.0,
    azimuth: float = 315.0,
    altitude: float = 45.0,
    combined: bool = True,
    compress: str = "LZW",
) -> None:
    """Generate a hillshade GeoTIFF from a DEM using ``gdaldem hillshade``.

    ``combined`` uses multi-directional hillshade for a richer result.
    ``z_factor`` exaggerates relief; 2.0 is a common atlas value.
    """
    args = [
        _require("gdaldem"), "hillshade",
        str(dem), str(out),
        "-z", str(z_factor),
        "-az", str(azimuth),
        "-alt", str(altitude),
        "-co", f"COMPRESS={compress}",
    ]
    if combined:
        args.append("-combined")
    _run(args)


# ---------------------------------------------------------------------------
# Contour lines
# ---------------------------------------------------------------------------

def contours(
    dem: Path,
    out: Path,
    *,
    interval: float = 100.0,
    attribute: str = "ele",
    driver: str = "GeoJSON",
) -> None:
    """Extract contour lines from a DEM using ``gdal_contour``.

    ``interval`` is the elevation step in metres.  ``out`` is a vector file
    (default: GeoJSON).  The ``attribute`` argument names the elevation
    field written to each contour feature.
    """
    _run([
        _require("gdal_contour"),
        "-a", attribute,
        "-i", str(interval),
        "-f", driver,
        str(dem),
        str(out),
    ])


# ---------------------------------------------------------------------------
# Reclassify (via gdal_calc or color relief → reclass raster)
# ---------------------------------------------------------------------------

def translate(
    src: Path,
    dst: Path,
    *,
    of: str = "GTiff",
    compress: str = "LZW",
    extra_args: list[str] | None = None,
) -> None:
    """Convert / copy a raster with ``gdal_translate``."""
    args = [
        _require("gdal_translate"),
        "-of", of,
        "-co", f"COMPRESS={compress}",
        *(extra_args or []),
        str(src), str(dst),
    ]
    _run(args)
