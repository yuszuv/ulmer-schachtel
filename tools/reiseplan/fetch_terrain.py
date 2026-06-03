"""Terrain ingest — Copernicus GLO-30 DEM → hillshade + contour lines.

Downloads 1°×1° COG tiles from the publicly-accessible Copernicus DEM AWS
bucket (no login required), assembles them into a mosaic, clips to the project
ROI, and derives a hillshade GeoTIFF and a contours GeoJSON.

Data source
-----------
Copernicus DEM GLO-30 — publicly available via AWS Open Data.
Bucket: s3://copernicus-dem-30m  (also accessible via HTTPS)
Tile URL pattern:
  https://copernicus-dem-30m.s3.amazonaws.com/
      Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM/
      Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM.tif

  For West longitudes replace E with W and use absolute value.

License: Copernicus DEM © ESA/Copernicus, permissive use under the
Copernicus Data and Information Policy.  Attribution required.
See https://spacedata.copernicus.eu/documents/20126/0/CSCDA_ESA_Mission-specific+Annex+%281%29.pdf

Output files
------------
  data/raw/dem/         — downloaded 1°×1° GeoTIFF tiles (cached)
  data/raw/dem.vrt      — GDAL VRT mosaic
  data/raster/terrain_dem.tif        — clipped DEM (EPSG:3844)
  data/raster/terrain_hillshade.tif  — hillshade (EPSG:3844)
  data/processed/contours.geojson    — 100 m contour lines (EPSG:4326)
  data/processed/terrain_attribution.json

Usage (via CLI)
---------------
  uv run reiseplan-cli fetch-terrain
  uv run reiseplan-cli fetch-terrain --offline          # skip DEM download
  uv run reiseplan-cli fetch-terrain --interval 200     # 200 m contours
  uv run reiseplan-cli fetch-terrain --no-hillshade     # skip hillshade
  uv run reiseplan-cli fetch-terrain --no-contours      # skip contours
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .http import USER_AGENT
from .paths import ROOT
from . import raster
from .themes import KUK_ROI

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RAW_DEM_DIR   = ROOT / "data" / "raw"   / "dem"
VRT_PATH      = ROOT / "data" / "raw"   / "dem.vrt"
DEM_PATH      = ROOT / "data" / "raster" / "terrain_dem.tif"
HILLSHADE_PATH = ROOT / "data" / "raster" / "terrain_hillshade.tif"
CONTOURS_PATH  = ROOT / "data" / "processed" / "contours.geojson"
ATTRIBUTION_PATH = ROOT / "data" / "processed" / "terrain_attribution.json"

# ---------------------------------------------------------------------------
# DEM tile URLs (Copernicus GLO-30, AWS HTTPS)
# ---------------------------------------------------------------------------

_COG_BASE = (
    "https://copernicus-dem-30m.s3.amazonaws.com/"
    "Copernicus_DSM_COG_10_{hem}{lat:02d}_00_{ew}{lon:03d}_00_DEM/"
    "Copernicus_DSM_COG_10_{hem}{lat:02d}_00_{ew}{lon:03d}_00_DEM.tif"
)


def _tile_url(lat: int, lon: int) -> str:
    """Return the AWS HTTPS URL for the 1°×1° GLO-30 tile at (lat, lon).

    ``lat``/``lon`` are the integer floor values of the tile's SW corner.
    Positive lat → N, positive lon → E.
    """
    hem = "N" if lat >= 0 else "S"
    ew  = "E" if lon >= 0 else "W"
    return _COG_BASE.format(hem=hem, lat=abs(lat), ew=ew, lon=abs(lon))


def _tile_path(lat: int, lon: int) -> Path:
    """Return the local cache path for one DEM tile."""
    hem = "N" if lat >= 0 else "S"
    ew  = "E" if lon >= 0 else "W"
    stem = f"Copernicus_DSM_COG_10_{hem}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"
    return RAW_DEM_DIR / f"{stem}.tif"


def _roi_tile_coords(roi=KUK_ROI) -> list[tuple[int, int]]:
    """Return the (lat, lon) SW corner of every 1°×1° tile covering the ROI."""
    coords = []
    lat = int(roi.south) - (1 if roi.south < 0 else 0)
    while lat <= int(roi.north):
        lon = int(roi.west) - (1 if roi.west < 0 else 0)
        while lon <= int(roi.east):
            coords.append((lat, lon))
            lon += 1
        lat += 1
    return coords


# ---------------------------------------------------------------------------
# Tile download
# ---------------------------------------------------------------------------

def _download_tile(lat: int, lon: int) -> Path | None:
    """Download one GLO-30 tile if not already cached.  Returns path or None."""
    path = _tile_path(lat, lon)
    if path.is_file():
        return path

    url = _tile_url(lat, lon)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None  # tile doesn't exist (ocean / edge of dataset)
        print(f"  ! HTTP {exc.code} for {url}", file=sys.stderr)
        return None
    except urllib.error.URLError as exc:
        print(f"  ! Network error for {url}: {exc.reason}", file=sys.stderr)
        return None

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def fetch_tiles(offline: bool = False) -> list[Path]:
    """Download (or locate cached) DEM tiles covering the ROI.

    Returns the list of tile paths that were successfully found/downloaded.
    """
    coords = _roi_tile_coords()
    tiles: list[Path] = []

    if offline:
        for lat, lon in coords:
            p = _tile_path(lat, lon)
            if p.is_file():
                tiles.append(p)
        print(f"[offline] {len(tiles)}/{len(coords)} DEM-Kacheln im Cache")
        return tiles

    print(f"[online]  {len(coords)} DEM-Kacheln herunterladen (oder aus Cache) …")
    found = skipped = 0
    for lat, lon in coords:
        p = _download_tile(lat, lon)
        if p:
            tiles.append(p)
            found += 1
        else:
            skipped += 1
    print(f"[online]  {found} Kacheln OK, {skipped} übersprungen (kein Tile)")
    return tiles


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------

def _write_attribution(interval: int) -> None:
    attr = {
        "generated":  datetime.date.today().isoformat(),
        "source":     "Copernicus DEM GLO-30",
        "provider":   "ESA / Copernicus",
        "url":        "https://spacedata.copernicus.eu/",
        "license":    "Copernicus Data and Information Policy (open, attribution required)",
        "attribution_required": (
            "© ESA/Copernicus. Contains modified Copernicus DEM data."
        ),
        "tile_base_url": _COG_BASE,
        "roi_bbox": {
            "south": KUK_ROI.south, "west": KUK_ROI.west,
            "north": KUK_ROI.north, "east": KUK_ROI.east,
        },
        "outputs": {
            "terrain_dem.tif":       "Clipped DEM, EPSG:3844, LZW",
            "terrain_hillshade.tif": "Multi-directional hillshade, EPSG:3844, LZW",
            "contours.geojson":      f"Contour lines every {interval} m, EPSG:4326",
        },
        "methodology": (
            f"1°×1° GLO-30 COG tiles downloaded from AWS HTTPS bucket. "
            f"gdalbuildvrt mosaic → gdalwarp clip + reproject (EPSG:3844). "
            f"gdaldem hillshade (z-factor 2, combined). "
            f"gdal_contour every {interval} m → GeoJSON (EPSG:4326 via gdalwarp)."
        ),
    }
    ATTRIBUTION_PATH.write_text(
        json.dumps(attr, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(
    offline: bool = False,
    interval: int = 100,
    hillshade: bool = True,
    make_contours: bool = True,
) -> None:
    """End-to-end: download tiles → DEM → hillshade + contours."""
    tiles = fetch_tiles(offline)
    if not tiles:
        print("[error]   Keine DEM-Kacheln verfügbar — Abbruch.", file=sys.stderr)
        sys.exit(1)

    # 1. VRT mosaic
    VRT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"[gdal]    gdalbuildvrt: {len(tiles)} Kacheln → {VRT_PATH.name}")
    raster.buildvrt(tiles, VRT_PATH)

    # 2. Clip + reproject → terrain_dem.tif
    DEM_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"[gdal]    gdalwarp → {DEM_PATH.name}")
    raster.warp_clip(
        VRT_PATH, DEM_PATH,
        t_srs="EPSG:3844",
        te=(KUK_ROI.west, KUK_ROI.south, KUK_ROI.east, KUK_ROI.north),
        te_srs="EPSG:4326",
        resampling="bilinear",
        nodata=-9999.0,
    )
    print(f"  → {DEM_PATH.relative_to(ROOT)}")

    # 3. Hillshade
    if hillshade:
        print(f"[gdal]    gdaldem hillshade → {HILLSHADE_PATH.name}")
        raster.hillshade(DEM_PATH, HILLSHADE_PATH, z_factor=2.0, combined=True)
        print(f"  → {HILLSHADE_PATH.relative_to(ROOT)}")

    # 4. Contours (in WGS84 for GeoJSON convention)
    if make_contours:
        import tempfile
        from pathlib import Path as _Path
        print(f"[gdal]    gdal_contour {interval} m → {CONTOURS_PATH.name}")
        # Contours are generated in native CRS then re-projected to WGS84.
        with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as tf:
            tmp = _Path(tf.name)
        try:
            raster.contours(DEM_PATH, tmp, interval=interval, driver="GeoJSON")
            CONTOURS_PATH.parent.mkdir(parents=True, exist_ok=True)
            # Re-project to EPSG:4326 for GeoJSON convention
            raster.warp_clip(
                tmp, CONTOURS_PATH,
                t_srs="EPSG:4326",
                resampling="near",
            )
        finally:
            if tmp.is_file():
                tmp.unlink()
        print(f"  → {CONTOURS_PATH.relative_to(ROOT)}")

    _write_attribution(interval)
    print(f"  → {ATTRIBUTION_PATH.relative_to(ROOT)}")
    print("[done]    Terrain fertig. In QGIS laden: tools/qgis_terrain.py")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--offline", action="store_true",
        help="Skip DEM download — use only cached tiles from data/raw/dem/.",
    )
    parser.add_argument(
        "--interval", type=int, default=100, metavar="M",
        help="Contour interval in metres (default: 100).",
    )
    parser.add_argument(
        "--no-hillshade", action="store_true",
        help="Skip hillshade generation.",
    )
    parser.add_argument(
        "--no-contours", action="store_true",
        help="Skip contour-line extraction.",
    )
    args = parser.parse_args()
    run(
        offline=args.offline,
        interval=args.interval,
        hillshade=not args.no_hillshade,
        make_contours=not args.no_contours,
    )


if __name__ == "__main__":
    main()
