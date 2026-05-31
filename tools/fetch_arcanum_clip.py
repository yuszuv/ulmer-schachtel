#!/usr/bin/env python3
"""Build a local, clipped GeoTIFF of the Arcanum 2nd Military Survey (1806-1869).

Why this exists
---------------
QGIS (incl. 4.0) cannot non-destructively clip a *raster* to a polygon on the
interactive map canvas -- the new 4.0 clip features are layout/atlas only. To show
the historical map only inside the countries we have rail data for (Romania + the
historical Austria-Hungary, which together cover today's Romania), while letting a
different basemap show through outside, the remote Arcanum XYZ tiles must be baked
into a local raster that is transparent outside the cutline. This runs *outside*
QGIS (pure GDAL); wire the resulting GeoTIFF into the project with
``tools/qgis_bootstrap.py``.

Pipeline
--------
1. Build the cutline (union of the 'Romania' + 'Austria Hungary' polygons from the
   historical borders layer) if it is missing.
2. Emit a GDAL WMS descriptor for the Arcanum 2nd survey XYZ service (with the
   required Referer header and a local tile cache).
3. ``gdalwarp -cutline ... -crop_to_cutline -dstalpha`` -> local GeoTIFF, transparent
   outside the cutline, in EPSG:3857 (Arcanum's native grid; QGIS reprojects to
   EPSG:3844 on the fly like every other layer).

Run it from the repo root::

    python tools/fetch_arcanum_clip.py            # overview resolution (zoom 9)
    python tools/fetch_arcanum_clip.py --zoom 10  # sharper, larger download

Needs GDAL CLI tools (``ogr2ogr``, ``gdalwarp``) in PATH and a network connection.

Attribution: (c) Arcanum Maps / HM Hadtorteneti Intezet -- free for non-commercial
use. See qgis/xyz_connections.xml for the licence note.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# --- Arcanum 2nd Military Survey (Franziszeische Landesaufnahme, 1806-1869) -------
ARCANUM_URL = (
    "https://tiles.arcanum.com/mercator/europe-19century-secondsurvey/${z}/${x}/${y}"
)
ARCANUM_REFERER = "https://maps.arcanum.com"
MAX_TILE_LEVEL = 14  # zmax of the service (see qgis/xyz_connections.xml)

# Web Mercator (EPSG:3857) full extent and pixel resolution per zoom level.
MERC_HALF = 20037508.342789244
WEBMERC_RES_Z0 = 156543.03392804097  # metres/pixel at zoom 0 (3857 units)

# Historical borders: which 1880 polygons enclose our rail data. Today's Romania
# spans the Kingdom of Romania (Regat) + Transylvania/Banat, the latter part of
# Austria-Hungary in 1880 -- so both are needed to cover the whole rail network.
CUTLINE_NAMES = ("Romania", "Austria Hungary")
BORDERS_REL = Path("data/reference/historical/staatsgrenzen.geojson")
CUTLINE_REL = Path("data/reference/historical/arcanum_clip.geojson")
OUTPUT_REL = Path("data/raster/arcanum2_ro_clip.tif")
CACHE_REL = Path("data/raw/arcanum2_tilecache")  # GDAL WMS tile cache (gitignored)


def repo_root() -> Path:
    """Repo root = parent of this script's tools/ directory."""
    return Path(__file__).resolve().parent.parent


def run(cmd: list[str]) -> None:
    print("  $", " ".join(cmd))
    subprocess.run(cmd, check=True)


def ogr_layer_name(path: Path) -> str:
    """First OGR layer name inside ``path`` (GeoJSON 'name' may differ from filename)."""
    out = subprocess.run(
        ["ogrinfo", str(path)], check=True, capture_output=True, text=True
    ).stdout
    for line in out.splitlines():
        # e.g. "1: world_1880 (Multi Polygon)"
        if line[:1].isdigit() and ":" in line:
            return line.split(":", 1)[1].strip().split(" (")[0].strip()
    sys.exit(f"  ! could not determine OGR layer name in {path}")


def zoom_resolution(zoom: int) -> float:
    """Ground resolution (EPSG:3857 metres/pixel) for a web-mercator zoom level."""
    return WEBMERC_RES_Z0 / (2 ** zoom)


def build_cutline(borders: Path, cutline: Path, force: bool) -> None:
    if cutline.exists() and not force:
        print(f"  cutline exists: {cutline}  (use --force to rebuild)")
        return
    if not borders.exists():
        sys.exit(f"  ! borders layer missing: {borders}")
    layer = ogr_layer_name(borders)  # internal OGR layer name (may differ from filename)
    names = ",".join(f"'{n}'" for n in CUTLINE_NAMES)
    sql = (
        f"SELECT ST_Union(ST_MakeValid(geometry)) AS geometry "
        f"FROM {layer} WHERE NAME IN ({names})"
    )
    cutline.parent.mkdir(parents=True, exist_ok=True)
    cutline.unlink(missing_ok=True)
    print(f"  building cutline (union of {', '.join(CUTLINE_NAMES)}) -> {cutline}")
    # NOTE: -dialect SQLite + ST_Union/ST_MakeValid need GDAL built with SpatiaLite.
    run([
        "ogr2ogr", "-f", "GeoJSON", "-dialect", "SQLite", "-sql", sql,
        str(cutline), str(borders),
    ])


def write_wms_xml(xml_path: Path, cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    xml = f"""<GDAL_WMS>
  <Service name="TMS">
    <ServerUrl>{ARCANUM_URL}</ServerUrl>
  </Service>
  <DataWindow>
    <UpperLeftX>{-MERC_HALF}</UpperLeftX>
    <UpperLeftY>{MERC_HALF}</UpperLeftY>
    <LowerRightX>{MERC_HALF}</LowerRightX>
    <LowerRightY>{-MERC_HALF}</LowerRightY>
    <TileLevel>{MAX_TILE_LEVEL}</TileLevel>
    <TileCountX>1</TileCountX>
    <TileCountY>1</TileCountY>
    <YOrigin>top</YOrigin>
  </DataWindow>
  <Projection>EPSG:3857</Projection>
  <BlockSizeX>256</BlockSizeX>
  <BlockSizeY>256</BlockSizeY>
  <BandsCount>3</BandsCount>
  <Referer>{ARCANUM_REFERER}</Referer>
  <ZeroBlockHttpCodes>204,403,404</ZeroBlockHttpCodes>
  <ZeroBlockOnServerException>true</ZeroBlockOnServerException>
  <Cache><Path>{cache_dir}</Path></Cache>
</GDAL_WMS>
"""
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    xml_path.write_text(xml, encoding="utf-8")
    print(f"  WMS descriptor -> {xml_path}")


def warp(wms_xml: Path, cutline: Path, output: Path, zoom: int) -> None:
    res = zoom_resolution(zoom)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    print(f"  warping Arcanum 2 -> {output}  (zoom {zoom}, ~{res:.1f} m/px)")
    run([
        "gdalwarp",
        "-cutline", str(cutline),
        "-crop_to_cutline",
        "-t_srs", "EPSG:3857",
        "-tr", str(res), str(res),
        "-dstalpha",
        "-r", "bilinear",
        "-co", "COMPRESS=DEFLATE",
        "-co", "TILED=YES",
        "-co", "BIGTIFF=IF_SAFER",
        "-wo", "NUM_THREADS=ALL_CPUS",
        "--config", "GDAL_HTTP_REFERER", ARCANUM_REFERER,
        str(wms_xml), str(output),
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--zoom", type=int, default=9,
        help="web-mercator zoom level / resolution (default 9 ~= 306 m/px, sized "
             "for 1:2M-1:20M overview; 10 ~= 153 m/px is sharper but larger).",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help=f"output GeoTIFF (default {OUTPUT_REL})",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="rebuild the cutline even if it already exists",
    )
    args = parser.parse_args()

    for exe in ("ogr2ogr", "gdalwarp"):
        if shutil.which(exe) is None:
            sys.exit(f"  ! {exe} not found in PATH (Arch: pacman -S gdal)")

    root = repo_root()
    borders = root / BORDERS_REL
    cutline = root / CUTLINE_REL
    output = args.output if args.output else root / OUTPUT_REL
    cache_dir = root / CACHE_REL
    wms_xml = cache_dir.parent / "arcanum2_secondsurvey.wms.xml"

    print("Arcanum 2 -> local clipped GeoTIFF")
    build_cutline(borders, cutline, args.force)
    write_wms_xml(wms_xml, cache_dir)
    warp(wms_xml, cutline, output, args.zoom)

    print(f"\nDone: {output}")
    print("  Next: open qgis/reiseplan.qgz, run tools/qgis_bootstrap.py +")
    print("        tools/qgis_setup_scales.py in the Python console, then save.")


if __name__ == "__main__":
    main()
