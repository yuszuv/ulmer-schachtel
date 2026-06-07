"""Fetch river data from two sources for the Ulmer Schachtel atlas.

Natural Earth rivers (overview, three resolutions)
---------------------------------------------------
Natural Earth river centerlines are available at three generalisation levels:
  10m  — ~1:10 000 000, most detailed, all named tributaries
  50m  — ~1:50 000 000, medium, major rivers only
  110m — ~1:110 000 000, coarsest, only the largest rivers

Each resolution is downloaded, clipped to the KUK_ROI, and written to its
own GeoJSON.  All three can be loaded in QGIS as a resolution pyramid —
each layer active in its optimal scale band.

Outputs (EPSG:4326, RFC 7946):
  data/processed/rivers_major_10m.geojson
  data/processed/rivers_major_50m.geojson
  data/processed/rivers_major_110m.geojson

Raw caches (for --offline rebuild):
  data/raw/natural_earth/ne_rivers_10m.zip
  data/raw/natural_earth/ne_rivers_50m.zip
  data/raw/natural_earth/ne_rivers_110m.zip

OSM Danube Delta (fine detail)
------------------------------
Waterways (river/canal/stream) in the Danube Delta bounding box, fetched via
Overpass, converted to LineStrings.  The raw JSON is cached to
data/raw/osm_delta_waterways.json.

Output: data/processed/rivers_delta.geojson
Attribution: data/processed/rivers_attribution.json

Usage
-----
  uv run reiseplan-cli fetch-rivers              # all three NE scales + delta
  uv run reiseplan-cli fetch-rivers --scale 10m  # only 10m + delta
  uv run reiseplan-cli fetch-rivers --offline    # rebuild from caches (no network)
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .geo import way_to_linestring
from .http import USER_AGENT
from .overpass import OVERPASS_URL, post_overpass
from .paths import PROCESSED, ROOT
from .repository import feature_collection, write_json
from .result import Err
from .themes import KUK_ROI

# ---------------------------------------------------------------------------
# Natural Earth resolution config
# ---------------------------------------------------------------------------

_NE_RAW_DIR = ROOT / "data" / "raw" / "natural_earth"

_NE_BASE = "https://naciscdn.org/naturalearth/{res}/physical/ne_{res}_rivers_lake_centerlines.zip"


@dataclass(frozen=True)
class _NeScale:
    resolution: str         # "10m" | "50m" | "110m"
    url: str
    cache_path: Path
    output_path: Path


NE_SCALES: dict[str, _NeScale] = {
    res: _NeScale(
        resolution=res,
        url=_NE_BASE.format(res=res),
        cache_path=_NE_RAW_DIR / f"ne_rivers_{res}.zip",
        output_path=PROCESSED / f"rivers_major_{res}.geojson",
    )
    for res in ("10m", "50m", "110m")
}

ALL_SCALES = list(NE_SCALES.keys())

# ---------------------------------------------------------------------------
# OSM Danube Delta
# ---------------------------------------------------------------------------

RIVERS_DELTA_PATH = PROCESSED / "rivers_delta.geojson"
DELTA_CACHE_PATH  = ROOT / "data" / "raw" / "osm_delta_waterways.json"
ATTR_PATH         = PROCESSED / "rivers_attribution.json"

# Danube Delta bbox (S, W, N, E) — covers all delta branches + coastal lagoons.
DELTA_BBOX = (44.7, 28.5, 45.7, 30.4)

_DELTA_QUERY = """\
[out:json][timeout:120];
(
  way["waterway"~"^(river|canal|stream)$"]({s},{w},{n},{e});
);
out geom;
""".format(s=DELTA_BBOX[0], w=DELTA_BBOX[1], n=DELTA_BBOX[2], e=DELTA_BBOX[3])


# ---------------------------------------------------------------------------
# Natural Earth helpers
# ---------------------------------------------------------------------------

def _download_ne_zip(scale: _NeScale) -> None:
    print(f"Downloading Natural Earth rivers {scale.resolution} …")
    req = urllib.request.Request(scale.url, headers={"User-Agent": USER_AGENT})
    data = urllib.request.urlopen(req, timeout=120).read()
    print(f"  {len(data) // 1024} kB received")
    scale.cache_path.parent.mkdir(parents=True, exist_ok=True)
    scale.cache_path.write_bytes(data)


def _extract_shp(zip_path: Path, tmp_dir: str) -> str:
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(tmp_dir)
    shp_files = [f for f in os.listdir(tmp_dir) if f.endswith(".shp")]
    if not shp_files:
        sys.exit(f"No .shp found in {zip_path}")
    return os.path.join(tmp_dir, shp_files[0])


def _clip_ne_rivers(shp: str, out_path: Path) -> int:
    """Clip NE rivers SHP to KUK_ROI and write to *out_path*.  Returns feature count."""
    w, s, e, n = KUK_ROI.west, KUK_ROI.south, KUK_ROI.east, KUK_ROI.north
    out_path.unlink(missing_ok=True)
    result = subprocess.run(
        [
            "ogr2ogr",
            "-f", "GeoJSON",
            str(out_path),
            shp,
            "-where", "featurecla = 'River'",
            "-select", "name,name_alt,scalerank,min_zoom",
            "-clipdst", str(w), str(s), str(e), str(n),
            "-t_srs", "EPSG:4326",
            "-lco", "RFC7946=YES",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit(f"ogr2ogr failed for {out_path.name}: {result.stderr[:400]}")
    fc = json.loads(out_path.read_text(encoding="utf-8"))
    return len(fc.get("features", []))


def _fetch_one_ne_scale(scale: _NeScale, offline: bool) -> None:
    if offline:
        if not scale.cache_path.is_file():
            sys.exit(f"--offline, aber Cache fehlt: {scale.cache_path}")
        print(f"[offline] NE-Cache ({scale.resolution}): {scale.cache_path.name}")
    else:
        _download_ne_zip(scale)

    with tempfile.TemporaryDirectory() as tmp:
        shp = _extract_shp(scale.cache_path, tmp)
        n = _clip_ne_rivers(shp, scale.output_path)

    print(f"  → {n} Flüsse ({scale.resolution}) → {scale.output_path.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# OSM Danube Delta
# ---------------------------------------------------------------------------

def _fetch_delta(offline: bool) -> int:
    if offline:
        if not DELTA_CACHE_PATH.is_file():
            sys.exit(f"--offline, aber Delta-Cache fehlt: {DELTA_CACHE_PATH}")
        print(f"[offline] Delta-Cache: {DELTA_CACHE_PATH.name}")
        raw = json.loads(DELTA_CACHE_PATH.read_text(encoding="utf-8"))
    else:
        print("[online]  frage Overpass (Donaudelta) ab …")
        result = post_overpass(_DELTA_QUERY, url=OVERPASS_URL)
        if isinstance(result, Err):
            sys.exit(f"Overpass-Fehler: {result.message}")
        raw = result.value
        DELTA_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        write_json(DELTA_CACHE_PATH, raw)
        print(f"[online]  {len(raw.get('elements', []))} Elemente gecacht → {DELTA_CACHE_PATH.name}")

    features: list[dict] = []
    for el in raw.get("elements", []):
        if el.get("type") != "way":
            continue
        coords = way_to_linestring(el)
        if coords is None:
            continue
        tags = el.get("tags", {})
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {
                "osm_id":   el.get("id"),
                "name":     tags.get("name"),
                "waterway": tags.get("waterway"),
            },
        })

    write_json(RIVERS_DELTA_PATH, feature_collection("rivers_delta", features))
    return len(features)


# ---------------------------------------------------------------------------
# Attribution sidecar
# ---------------------------------------------------------------------------

def _write_attribution(fetched_scales: list[str]) -> None:
    ne_sources = [
        {
            "resolution": res,
            "url": NE_SCALES[res].url,
            "output": NE_SCALES[res].output_path.name,
            "license": "Public Domain — https://www.naturalearthdata.com/about/terms-of-use/",
            "roi_bbox": {
                "south": KUK_ROI.south, "west": KUK_ROI.west,
                "north": KUK_ROI.north, "east": KUK_ROI.east,
            },
        }
        for res in fetched_scales
    ]
    attr = {
        "generated": datetime.date.today().isoformat(),
        "sources": [
            {
                "name": "Natural Earth Rivers + Lake Centerlines",
                "resolutions_fetched": fetched_scales,
                "layers": ne_sources,
            },
            {
                "name": "OpenStreetMap contributors",
                "url": "https://www.openstreetmap.org",
                "license": "© OpenStreetMap contributors, ODbL 1.0 — https://opendatacommons.org/licenses/odbl/",
                "output": RIVERS_DELTA_PATH.name,
                "delta_bbox": {
                    "south": DELTA_BBOX[0], "west": DELTA_BBOX[1],
                    "north": DELTA_BBOX[2], "east": DELTA_BBOX[3],
                },
            },
        ],
        "methodology": (
            f"rivers_major_{{10m|50m|110m}}: Natural Earth river centerlines at selected "
            f"resolutions ({', '.join(fetched_scales)}), clipped to the KUK/Romania atlas "
            f"extent via ogr2ogr (featurecla='River', RFC7946). "
            "rivers_delta: OSM waterway=river|canal|stream ways in the Danube Delta "
            "fetched via Overpass API, converted to GeoJSON LineStrings."
        ),
    }
    write_json(ATTR_PATH, attr)
    print(f"  → Attribution → {ATTR_PATH.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(offline: bool = False, scales: list[str] | None = None) -> None:
    """Fetch NE river layers (one or more resolutions) and OSM delta waterways.

    Args:
        offline: Rebuild from cached raw data without network access.
        scales:  Which NE resolutions to fetch — subset of ["10m","50m","110m"].
                 Defaults to all three.
    """
    if scales is None:
        scales = ALL_SCALES

    unknown = [s for s in scales if s not in NE_SCALES]
    if unknown:
        sys.exit(f"Unbekannte Auflösung(en): {unknown}. Erlaubt: {ALL_SCALES}")

    PROCESSED.mkdir(parents=True, exist_ok=True)

    print("── Übersichtsflüsse (Natural Earth) ─────────────────────────")
    for res in scales:
        _fetch_one_ne_scale(NE_SCALES[res], offline)

    print("── Donaudelta-Gewässer (OSM / Overpass) ──────────────────────")
    n_delta = _fetch_delta(offline)
    print(f"  → {n_delta} Delta-Gewässer → {RIVERS_DELTA_PATH.relative_to(ROOT)}")

    _write_attribution(scales)
    print("\nFertig. Nächster Schritt: qgis_rivers.py in der QGIS-Konsole ausführen.")


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="reiseplan-rivers",
        description=(
            "Flussdaten holen: Natural-Earth-Übersichtsflüsse (Auflösungspyramide: "
            "10m/50m/110m) + OSM-Donaudelta-Gewässer. "
            "Quelle NE: Public Domain. Quelle OSM: © OpenStreetMap contributors, ODbL 1.0."
        ),
    )
    parser.add_argument(
        "--scale",
        choices=[*ALL_SCALES, "all"],
        default="all",
        help=(
            "Welche NE-Auflösung(en) holen: 10m | 50m | 110m | all (Standard: all). "
            "'all' holt alle drei als Auflösungspyramide für QGIS."
        ),
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help=(
            "Nur aus data/raw/ neu bauen (kein Netz). "
            "Erfordert die entsprechenden data/raw/natural_earth/ne_rivers_*.zip "
            "und data/raw/osm_delta_waterways.json."
        ),
    )
    args = parser.parse_args()
    scales = ALL_SCALES if args.scale == "all" else [args.scale]
    run(offline=args.offline, scales=scales)


if __name__ == "__main__":
    main()
