"""Natural-feature ingest — mountain ridges, peaks, valleys, landscape labels.

Fetches named natural features in the Austria-Hungary / Romania region (k.u.k.
extent ~1880) via the Overpass API and splits them into three GeoJSON layers
ready for QGIS curved-label styling (atlas look, see docs/08_curved_labels.md).

Strategy: the k.u.k. bounding box is too large for a single Overpass call; the
server times out on area queries of this scale.  Instead the region is tiled
into 4 ° × 4 ° cells and one query is run per tile (with a pause between calls
for politeness).  Way geometry and node coordinates require ``out geom``;
``out tags`` intentionally omits lat/lon for nodes.

Output layers (EPSG:4326)
--------------------------
  data/processed/natural_ridges.geojson    — LineString  (natural=ridge ways)
  data/processed/mountain_peaks.geojson    — Point       (natural=peak nodes)
  data/processed/landscape_labels.geojson  — Point       (mountain_range, valley,
                                                           region label anchors)
  data/processed/natural_features_attribution.json  — ODbL sidecar

Attribution (required when redistributing)
-------------------------------------------
  Geometry / tags: OpenStreetMap via Overpass API.
  © OpenStreetMap contributors, ODbL 1.0.

Usage
-----
  uv run reiseplan-natural                 # fetch online + cache
  uv run reiseplan-natural --offline       # rebuild from data/raw/osm_natural_features.json
  uv run reiseplan-natural --min-ele 1500  # keep only peaks ≥ 1500 m (default)
"""

from __future__ import annotations

import argparse
import datetime
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .overpass import OVERPASS_URL, USER_AGENT
from .paths import ROOT
from .repository import feature_collection, write_json
from .result import Err, Ok, Result

# ---------------------------------------------------------------------------
# Region of interest — k.u.k. / Romania ~1880 extent from kuk_clip.geojson
# ---------------------------------------------------------------------------

_ROI_SOUTH = 42.929272
_ROI_WEST  =  9.464611
_ROI_NORTH = 51.077385
_ROI_EAST  = 30.432847

# ---------------------------------------------------------------------------
# Tile settings
# ---------------------------------------------------------------------------

# A single Overpass call for the full ROI bbox times out (too large).
# 4 ° × 4 ° tiles run in ~20-55 s each (Alps are denser than Carpathians).
# Relations are excluded — mountain-range names are always duplicated on a
# node with natural=mountain_range in OSM, so we avoid the heavyweight
# relation-member geometry.
_TILE_STEP_DEG     = 4.0   # tile width/height in degrees
_TILE_OVERLAP_DEG  = 0.1   # small overlap to avoid missing border features
_TILE_PAUSE_S      = 2.0   # politeness pause between Overpass requests

# Overpass query timeout (s) embedded in the QL header; set conservatively
# below the nginx/proxy hard limit (~90 s) so we get a structured error
# rather than a bare 504 when the server is under load.
_OVERPASS_QUERY_TIMEOUT = 75
# Local urllib socket timeout — large enough to receive the full response
# (dense tiles like the Alps can return 200+ ways × thousands of geometry pts).
_HTTP_SOCKET_TIMEOUT = 180

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RAW_CACHE_PATH   = ROOT / "data" / "raw"       / "osm_natural_features.json"
RIDGES_PATH      = ROOT / "data" / "processed" / "natural_ridges.geojson"
PEAKS_PATH       = ROOT / "data" / "processed" / "mountain_peaks.geojson"
LANDSCAPE_PATH   = ROOT / "data" / "processed" / "landscape_labels.geojson"
ATTRIBUTION_PATH = ROOT / "data" / "processed" / "natural_features_attribution.json"

# ---------------------------------------------------------------------------
# Overpass query builders (one per feature class)
# ---------------------------------------------------------------------------
#
# The combined k.u.k. bbox is too large for a single Overpass call.  Even at
# 4 ° × 4 ° tile granularity, a combined ways+nodes query times out in the
# Alps because the node count exceeds ~20k — so we issue *two* separate
# requests per tile: one for line ways, one for label nodes.  Each individual
# query finishes in 30-45 s on the densest (Alpine) tiles.


def _way_query(south: float, west: float, north: float, east: float) -> str:
    """Overpass QL query for ridge ways in one tile.

    ``out geom`` on ways returns the full vertex list needed to build
    GeoJSON LineString coordinates.
    """
    bb = f"{south},{west},{north},{east}"
    return (
        f"[out:json][timeout:{_OVERPASS_QUERY_TIMEOUT}];\n"
        f'way["natural"="ridge"]["name"]({bb});\n'
        "out geom;\n"
    )


def _node_query(south: float, west: float, north: float, east: float) -> str:
    """Overpass QL query for label-anchor nodes in one tile.

    ``out geom`` on nodes returns lat/lon + tags (``out tags`` intentionally
    omits coordinates, unlike for ways).  Valley nodes are included here as
    point label anchors (distinct from the ridge-way labels).
    """
    bb = f"{south},{west},{north},{east}"
    return (
        f"[out:json][timeout:{_OVERPASS_QUERY_TIMEOUT}];\n"
        "(\n"
        f'  node["natural"="peak"]["name"]({bb});\n'
        f'  node["natural"="mountain_range"]["name"]({bb});\n'
        f'  node["natural"="valley"]["name"]({bb});\n'
        ");\n"
        "out geom;\n"
    )


def _tile_grid() -> list[tuple[float, float, float, float]]:
    """Generate overlapping 4 ° × 4 ° tiles covering the ROI.

    Returns (south, west, north, east) tuples.  A small overlap ensures
    features near tile edges are not missed.
    """
    tiles: list[tuple[float, float, float, float]] = []
    lat = _ROI_SOUTH
    while lat < _ROI_NORTH:
        n = min(lat + _TILE_STEP_DEG + _TILE_OVERLAP_DEG, _ROI_NORTH + _TILE_OVERLAP_DEG)
        lon = _ROI_WEST
        while lon < _ROI_EAST:
            e = min(lon + _TILE_STEP_DEG + _TILE_OVERLAP_DEG, _ROI_EAST + _TILE_OVERLAP_DEG)
            tiles.append((round(lat, 6), round(lon, 6), round(n, 6), round(e, 6)))
            lon += _TILE_STEP_DEG
        lat += _TILE_STEP_DEG
    return tiles


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------


def _overpass_post(query: str) -> Result[dict]:
    """POST one Overpass query, return Ok(parsed_json) or Err(message)."""
    req = urllib.request.Request(
        OVERPASS_URL,
        data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_SOCKET_TIMEOUT) as resp:
            payload = resp.read()
    except urllib.error.HTTPError as exc:
        return Err(f"Overpass HTTP {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        return Err(f"Overpass nicht erreichbar: {exc.reason}")
    except TimeoutError as exc:
        return Err(f"Socket-Timeout nach {_HTTP_SOCKET_TIMEOUT}s: {exc}")

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        return Err(f"Kein gültiges JSON: {exc}")

    remark = data.get("remark", "")
    if remark and "timed out" in remark.lower():
        return Err(f"Overpass-Query timed out: {remark}")

    return Ok(data)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _fetch_tile(
    s: float, w: float, n: float, e: float, idx: int, total: int,
    seen: set[tuple[str, int]],
    all_elements: list[dict],
    failed_ways: list[str],
    failed_nodes: list[str],
) -> None:
    """Fetch one tile: first ways, pause, then nodes.  Mutates seen/all_elements."""
    label = f"({s:.1f},{w:.1f})–({n:.1f},{e:.1f})"

    # --- ways ---
    result_w = _overpass_post(_way_query(s, w, n, e))
    if isinstance(result_w, Err):
        print(f"  [{idx:2d}/{total}] {label} ways:  SKIP — {result_w.message}")
        failed_ways.append(label)
    else:
        elements = result_w.value.get("elements", [])
        new = 0
        for el in elements:
            key = (el.get("type", ""), el.get("id", 0))
            if key not in seen:
                seen.add(key)
                all_elements.append(el)
                new += 1
        ways_n = sum(1 for e in elements if e.get("type") == "way")
        print(f"  [{idx:2d}/{total}] {label} ways:  {ways_n} (+{new} new)")

    time.sleep(_TILE_PAUSE_S)

    # --- nodes ---
    result_n = _overpass_post(_node_query(s, w, n, e))
    if isinstance(result_n, Err):
        print(f"  [{idx:2d}/{total}] {label} nodes: SKIP — {result_n.message}")
        failed_nodes.append(label)
    else:
        elements = result_n.value.get("elements", [])
        new = 0
        for el in elements:
            key = (el.get("type", ""), el.get("id", 0))
            if key not in seen:
                seen.add(key)
                all_elements.append(el)
                new += 1
        nodes_n = sum(1 for e in elements if e.get("type") == "node")
        print(f"  [{idx:2d}/{total}] {label} nodes: {nodes_n} (+{new} new)")


def load_or_fetch(offline: bool) -> Result[list[dict]]:
    """Return a flat list of Overpass elements — from cache or tiled API calls.

    Online mode: iterates over the tile grid, issuing *two* requests per tile
    (ways then nodes) to avoid per-tile combined timeouts in the dense Alps.
    The combined list is cached in ``data/raw/osm_natural_features.json``.
    Offline mode: rebuilds from that cache without network access.
    """
    if offline:
        if not RAW_CACHE_PATH.is_file():
            return Err(f"--offline, aber Cache fehlt: {RAW_CACHE_PATH}")
        print(f"[offline] lese Roh-Cache: {RAW_CACHE_PATH}")
        try:
            cached = json.loads(RAW_CACHE_PATH.read_text(encoding="utf-8"))
            return Ok(cached["elements"])
        except (json.JSONDecodeError, KeyError) as exc:
            return Err(f"Cache kein gültiges JSON: {exc}")

    tiles = _tile_grid()
    total_calls = len(tiles) * 2
    print(
        f"[online]  {len(tiles)} Kacheln à {_TILE_STEP_DEG}°×{_TILE_STEP_DEG}°"
        f" × 2 Abfragen = {total_calls} Overpass-Calls …"
    )

    seen:           set[tuple[str, int]] = set()
    all_elements:   list[dict]           = []
    failed_ways:    list[str]            = []
    failed_nodes:   list[str]            = []

    for i, (s, w, n, e) in enumerate(tiles):
        if i:
            time.sleep(_TILE_PAUSE_S)
        _fetch_tile(s, w, n, e, i + 1, len(tiles), seen, all_elements,
                    failed_ways, failed_nodes)

    skipped = len(failed_ways) + len(failed_nodes)
    if skipped:
        print(f"[warn]    {skipped} fehlgeschlagene Abfragen:")
        for f in failed_ways:
            print(f"          · {f} (ways)")
        for f in failed_nodes:
            print(f"          · {f} (nodes)")

    if not all_elements:
        return Err("Keine Elemente gefunden – Abbruch.")

    RAW_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cache = {
        "generated":       datetime.datetime.utcnow().isoformat() + "Z",
        "tile_count":      len(tiles),
        "skipped_queries": skipped,
        "element_count":   len(all_elements),
        "elements":        all_elements,
    }
    RAW_CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[cache]   {len(all_elements)} Elemente → {RAW_CACHE_PATH}")
    return Ok(all_elements)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def _way_to_linestring(el: dict) -> list[list[float]] | None:
    """Extract [[lon, lat], …] from a way's ``geometry`` array ({lat,lon} dicts)."""
    geom = el.get("geometry")
    if not geom:
        return None
    coords = [
        [pt["lon"], pt["lat"]]
        for pt in geom
        if "lon" in pt and "lat" in pt
    ]
    return coords if len(coords) >= 2 else None


def _node_to_point(el: dict) -> list[float] | None:
    """Extract [lon, lat] from a node element (requires ``out geom``, not ``out tags``)."""
    lat, lon = el.get("lat"), el.get("lon")
    if lat is None or lon is None:
        return None
    return [float(lon), float(lat)]


# ---------------------------------------------------------------------------
# Feature builder
# ---------------------------------------------------------------------------


def _props(el: dict) -> dict:
    """Extract display properties from an Overpass element."""
    tags = el.get("tags", {})
    props: dict = {
        "osm_id":   el.get("id"),
        "osm_type": el.get("type"),
        "name":     tags.get("name"),
        "name_de":  tags.get("name:de"),
        "natural":  tags.get("natural"),
        "place":    tags.get("place"),
    }
    ele_raw = tags.get("ele", "").strip()
    if ele_raw:
        # Handle values like "2663", "2 663", "2663 m", "2663.5".
        cleaned = ele_raw.split()[0].replace(",", ".").rstrip("m").strip()
        try:
            props["ele"] = int(float(cleaned))
        except ValueError:
            props["ele"] = ele_raw
    return props


def parse_elements(
    elements: list[dict],
    min_ele: int,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Split Overpass elements into (ridges, peaks, landscape) GeoJSON features.

    ridges    — LineString features (natural=ridge ways → curved QGIS labels)
    peaks     — Point features (natural=peak nodes, filtered by min_ele)
    landscape — Point features (mountain_range / valley label anchors)
    """
    ridges:    list[dict] = []
    peaks:     list[dict] = []
    landscape: list[dict] = []

    for el in elements:
        el_type = el.get("type")
        name    = el.get("tags", {}).get("name")
        if not name:
            continue

        natural = el.get("tags", {}).get("natural", "")
        props   = _props(el)

        if el_type == "way":
            coords = _way_to_linestring(el)
            if coords is None:
                continue
            ridges.append({
                "type": "Feature",
                "properties": props,
                "geometry": {"type": "LineString", "coordinates": coords},
            })

        elif el_type == "node":
            point = _node_to_point(el)
            if point is None:
                continue

            if natural == "peak":
                ele_val = props.get("ele")
                if ele_val is not None:
                    try:
                        if int(float(str(ele_val))) < min_ele:
                            continue
                    except (ValueError, TypeError):
                        pass  # unparseable ele → include anyway
                peaks.append({
                    "type": "Feature",
                    "properties": props,
                    "geometry": {"type": "Point", "coordinates": point},
                })
            else:
                # mountain_range, valley — label anchor point
                landscape.append({
                    "type": "Feature",
                    "properties": props,
                    "geometry": {"type": "Point", "coordinates": point},
                })

    def _peak_sort_key(f: dict) -> tuple[int, str]:
        ele = f["properties"].get("ele")
        try:
            ele_int = int(float(str(ele))) if ele is not None else 0
        except (ValueError, TypeError):
            ele_int = 0
        return (-ele_int, f["properties"].get("name") or "")

    # Stable sort for reproducible GeoJSON diffs.
    ridges.sort(key=lambda f: f["properties"].get("name") or "")
    peaks.sort(key=_peak_sort_key)
    landscape.sort(key=lambda f: f["properties"].get("name") or "")

    return ridges, peaks, landscape


# ---------------------------------------------------------------------------
# Attribution sidecar
# ---------------------------------------------------------------------------


def _write_attribution() -> None:
    tiles = _tile_grid()
    attribution = {
        "generated":       datetime.date.today().isoformat(),
        "source":          "OpenStreetMap via Overpass API",
        "url":             OVERPASS_URL,
        "license":         "ODbL 1.0 — © OpenStreetMap contributors",
        "attribution_url": "https://www.openstreetmap.org/copyright",
        "roi_bbox": {
            "south":       _ROI_SOUTH,
            "west":        _ROI_WEST,
            "north":       _ROI_NORTH,
            "east":        _ROI_EAST,
            "description": (
                "Austria-Hungary + Romania extent ~1880 "
                "(derived from data/reference/historical/kuk_clip.geojson)"
            ),
        },
        "tile_strategy": (
            f"{len(tiles)} tiles of {_TILE_STEP_DEG}° × {_TILE_STEP_DEG}° "
            f"with {_TILE_OVERLAP_DEG}° overlap; 2 Overpass calls per tile "
            f"(ways + nodes separately) to avoid combined timeouts in the "
            f"dense Alpine area; per-call server timeout {_OVERPASS_QUERY_TIMEOUT}s."
        ),
        "methodology": (
            "Named ridge ways → natural_ridges.geojson (LineString, for QGIS "
            "Curved label placement). "
            "Named peak nodes → mountain_peaks.geojson (Point, ele ≥ default "
            "1500 m). "
            "Named mountain_range + valley nodes → landscape_labels.geojson "
            "(Point, straight labels). "
            "Relations excluded — mountain-range names are duplicated on OSM "
            "nodes. "
            "For large arcing names without OSM line geometry (Karpaten, "
            "Südkarpaten, Siebenbürgen), add hand-drawn lines per "
            "docs/08_curved_labels.md."
        ),
        "way_query_template": _way_query(
            _ROI_SOUTH, _ROI_WEST,
            _ROI_SOUTH + _TILE_STEP_DEG, _ROI_WEST + _TILE_STEP_DEG,
        ),
        "node_query_template": _node_query(
            _ROI_SOUTH, _ROI_WEST,
            _ROI_SOUTH + _TILE_STEP_DEG, _ROI_WEST + _TILE_STEP_DEG,
        ),
    }
    ATTRIBUTION_PATH.write_text(
        json.dumps(attribution, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Run + CLI
# ---------------------------------------------------------------------------


def run(offline: bool = False, min_ele: int = 1500) -> None:
    """End-to-end: tiled Overpass fetch → three GeoJSON layers + attribution."""
    elements = load_or_fetch(offline).unwrap_or_exit()
    print(f"[parse]   {len(elements)} Overpass-Elemente verarbeiten …")

    ridges, peaks, landscape = parse_elements(elements, min_ele)

    write_json(RIDGES_PATH,    feature_collection("natural_ridges",   ridges))
    write_json(PEAKS_PATH,     feature_collection("mountain_peaks",   peaks))
    write_json(LANDSCAPE_PATH, feature_collection("landscape_labels", landscape))
    _write_attribution()

    print(f"  → {RIDGES_PATH.relative_to(ROOT)}    ({len(ridges)} Linien)")
    print(f"  → {PEAKS_PATH.relative_to(ROOT)}  ({len(peaks)} Gipfel ≥ {min_ele} m)")
    print(f"  → {LANDSCAPE_PATH.relative_to(ROOT)} ({len(landscape)} Landschaftsnamen)")
    print(f"  → {ATTRIBUTION_PATH.relative_to(ROOT)}")
    print("[done]    Layer in QGIS laden und per docs/08_curved_labels.md stylen.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Rebuild from data/raw/osm_natural_features.json (no network).",
    )
    parser.add_argument(
        "--min-ele",
        type=int,
        default=1500,
        metavar="M",
        help="Minimum peak elevation in metres to include (default: 1500).",
    )
    args = parser.parse_args()
    run(offline=args.offline, min_ele=args.min_ele)


if __name__ == "__main__":
    main()
