"""Land-cover ingest — CORINE Land Cover 2018 → reclassified GeoJSON polygons.

Uses the CORINE Land Cover 2018 dataset (CLC2018) as the authoritative atlas
source for agricultural and land-use classification.  CORINE has 44 classes
which are re-mapped to 8 broad atlas categories.

Data source
-----------
CORINE Land Cover 2018, v2020_20u1
Publisher: European Environment Agency (EEA) / Copernicus Land Service
Download: https://land.copernicus.eu/pan-european/corine-land-cover/clc2018
Format: GPKG or GeoTIFF (download the 100 m GeoTIFF for speed, or the vector
  GPKG for full precision).

⚠  Manual download required (one-time, free Copernicus account):
   1. Go to https://land.copernicus.eu/pan-european/corine-land-cover/clc2018
   2. Download "CLC 2018 — vector" or "CLC 2018 raster 100m"
   3. Place the file(s) in  data/raw/corine/
      • Vector:  data/raw/corine/U2018_CLC2018_V2020_20u1.gpkg
      • Raster:  data/raw/corine/U2018_CLC2018_V2020_20u1_100m.tif

This script accepts either format.

Alternatively, use ESA WorldCover 2021 (10 m, no login required, AWS COG):
   uv run reiseplan-cli fetch-landcover --source worldcover
See docs/data-and-layers/terrain-landcover.md for the WorldCover workflow.

Attribution
-----------
© European Environment Agency (EEA) / Copernicus Land Monitoring Service.
CORINE Land Cover is freely available under the Copernicus Data Policy
(open access, attribution required).

Output files
------------
  data/processed/landcover.geojson         — simplified Polygons, EPSG:4326
  data/processed/landcover_attribution.json

Usage (via CLI)
---------------
  uv run reiseplan-cli fetch-landcover
  uv run reiseplan-cli fetch-landcover --source worldcover
"""

from __future__ import annotations

import argparse
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

from .paths import ROOT
from .themes import KUK_ROI

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

CORINE_DIR      = ROOT / "data" / "raw" / "corine"
CORINE_GPKG     = CORINE_DIR / "U2018_CLC2018_V2020_20u1.gpkg"
CORINE_RASTER   = CORINE_DIR / "U2018_CLC2018_V2020_20u1_100m.tif"
WORLDCOVER_DIR  = ROOT / "data" / "raw" / "worldcover"
LANDCOVER_PATH  = ROOT / "data" / "processed" / "landcover.geojson"
ATTRIBUTION_PATH = ROOT / "data" / "processed" / "landcover_attribution.json"

# ---------------------------------------------------------------------------
# CORINE class → atlas category mapping
# ---------------------------------------------------------------------------

# 44 CORINE classes → 8 atlas categories.
# Source: https://land.copernicus.eu/user-corner/technical-library/corine-land-cover-nomenclature-guidelines
CORINE_TO_ATLAS: dict[int, str] = {
    # Arable land
    211: "arable", 212: "arable", 213: "arable",
    # Permanent crops (vineyards, orchards, olive groves)
    221: "vineyard", 222: "orchard", 223: "orchard",
    # Pasture / heterogeneous agricultural
    231: "pasture",
    241: "arable", 242: "arable", 243: "arable", 244: "arable",
    # Forests
    311: "forest", 312: "forest", 313: "forest",
    # Shrub / grassland / natural vegetation
    321: "grassland", 322: "grassland", 323: "grassland", 324: "grassland",
    331: "barren", 332: "barren", 333: "barren", 334: "barren", 335: "barren",
    # Wetlands
    411: "wetland", 412: "wetland", 421: "wetland", 422: "wetland", 423: "wetland",
    # Water
    511: "water", 512: "water", 521: "water", 522: "water", 523: "water",
    # Urban / artificial surfaces
    111: "urban", 112: "urban",
    121: "urban", 122: "urban", 123: "urban", 124: "urban",
    131: "urban", 132: "urban", 133: "urban",
    141: "urban", 142: "urban",
}

# Atlas category → display colour (atlas brown/green palette, QGIS-ready hex).
ATLAS_COLOURS: dict[str, str] = {
    "arable":    "#e8d5a3",
    "vineyard":  "#c0a86a",
    "orchard":   "#b5c45a",
    "pasture":   "#d4e8b0",
    "forest":    "#7ab87a",
    "grassland": "#c8e0a0",
    "barren":    "#d8cdb8",
    "wetland":   "#a8c8d8",
    "water":     "#88b4d0",
    "urban":     "#c8b4a8",
}


# ---------------------------------------------------------------------------
# ogr2ogr helpers
# ---------------------------------------------------------------------------

def _require_ogr() -> str:
    path = shutil.which("ogr2ogr")
    if path is None:
        print(
            "  ✗ 'ogr2ogr' not found — please install GDAL.",
            file=sys.stderr,
        )
        sys.exit(1)
    return path


def _clip_corine_vector(src: Path, dst: Path) -> None:
    """Clip CORINE vector GPKG to ROI bbox and write GeoJSON."""
    s, w, n, e = KUK_ROI.south, KUK_ROI.west, KUK_ROI.north, KUK_ROI.east
    subprocess.run([
        _require_ogr(),
        "-f", "GeoJSON",
        "-t_srs", "EPSG:4326",
        "-spat", str(w), str(s), str(e), str(n),
        "-spat_srs", "EPSG:4326",
        str(dst), str(src),
    ], check=True)


def _reclassify_features(raw_geojson: Path, out: Path) -> None:
    """Reclassify CLC CODE_18 integers to atlas category strings.

    Reads the clipped GeoJSON, maps CODE_18 → landuse_class, drops features
    with no mapping (sea, no-data), and writes the result.
    """
    import json as _json
    data = _json.loads(raw_geojson.read_text(encoding="utf-8"))
    kept = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        code = props.get("Code_18") or props.get("CODE_18")
        if code is None:
            continue
        category = CORINE_TO_ATLAS.get(int(code))
        if category is None:
            continue
        feat["properties"] = {
            "clc_code":     int(code),
            "landuse_class": category,
            "colour":       ATLAS_COLOURS.get(category, "#cccccc"),
        }
        kept.append(feat)
    data["features"] = kept
    out.write_text(
        _json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------

def _write_attribution(source: str) -> None:
    attr = {
        "generated":  datetime.date.today().isoformat(),
        "source":     "CORINE Land Cover 2018 (CLC2018)" if source == "corine"
                      else "ESA WorldCover 2021",
        "provider":   "European Environment Agency / Copernicus" if source == "corine"
                      else "ESA",
        "license":    "Copernicus Data Policy (open access, attribution required)",
        "download":   (
            "https://land.copernicus.eu/pan-european/corine-land-cover/clc2018"
            if source == "corine"
            else "https://esa-worldcover.org/"
        ),
        "atlas_categories": list(ATLAS_COLOURS.keys()),
        "clc_mapping": CORINE_TO_ATLAS,
        "methodology": (
            "CORINE vector GPKG clipped to ROI via ogr2ogr, CODE_18 integer "
            "reclassified to 8 atlas categories (arable/vineyard/orchard/pasture/"
            "forest/grassland/barren/wetland/water/urban).  Output in EPSG:4326."
        ),
    }
    ATTRIBUTION_PATH.write_text(
        json.dumps(attr, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def _check_corine_input() -> Path | None:
    """Return the CORINE input path if it exists, else None."""
    if CORINE_GPKG.is_file():
        return CORINE_GPKG
    return None


def _print_download_hint() -> None:
    print(
        "\n[error]   CORINE Land Cover source file not found.\n"
        "\n"
        "  Manual download required (one-time, free Copernicus account):\n"
        "    1.  https://land.copernicus.eu/pan-european/corine-land-cover/clc2018\n"
        "    2.  Download 'CLC 2018 — vector (GPKG)'\n"
        f"    3.  Place the file at:  {CORINE_GPKG}\n"
        "\n"
        "  Alternatively, use ESA WorldCover (no login):\n"
        "    uv run reiseplan-cli fetch-landcover --source worldcover\n"
        "\n"
        "  See docs/data-and-layers/terrain-landcover.md for full instructions.\n",
        file=sys.stderr,
    )


def run(source: str = "corine") -> None:
    """End-to-end: clip CORINE/WorldCover → reclassify → GeoJSON + attribution."""
    if source == "corine":
        inp = _check_corine_input()
        if inp is None:
            _print_download_hint()
            sys.exit(1)

        import tempfile
        from pathlib import Path as _Path

        print(f"[clip]    CORINE GPKG → ROI clip …")
        with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as tf:
            tmp = _Path(tf.name)
        try:
            _clip_corine_vector(inp, tmp)
            print(f"[reclass] 44 CLC-Klassen → 8 Atlas-Kategorien …")
            LANDCOVER_PATH.parent.mkdir(parents=True, exist_ok=True)
            _reclassify_features(tmp, LANDCOVER_PATH)
        finally:
            if tmp.is_file():
                tmp.unlink()

    elif source == "worldcover":
        # WorldCover workflow — documented in docs/data-and-layers/terrain-landcover.md.
        # Requires separate download steps; placeholder raises informative error.
        print(
            "[info]    WorldCover workflow not yet implemented.\n"
            "          See docs/data-and-layers/terrain-landcover.md.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print(f"[error]   Unknown source: {source!r}", file=sys.stderr)
        sys.exit(1)

    _write_attribution(source)
    print(f"  → {LANDCOVER_PATH.relative_to(ROOT)}")
    print(f"  → {ATTRIBUTION_PATH.relative_to(ROOT)}")
    print("[done]    Landbedeckung fertig. In QGIS laden: tools/qgis_landcover.py")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source",
        choices=["corine", "worldcover"],
        default="corine",
        help="Land-cover data source (default: corine).",
    )
    args = parser.parse_args()
    run(source=args.source)


if __name__ == "__main__":
    main()
