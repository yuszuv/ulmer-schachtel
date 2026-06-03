"""OSM cities/towns/villages layer — two-tier spatial fetch.

Fetches settlements from OpenStreetMap via Overpass in two tiers:

**Tier "kuk"** — inside the historic k.u.k. empire polygon (``kuk_clip.geojson``):
    all named ``place=city|town|village`` nodes, clipped to the actual polygon
    (not just the bounding box) using a stdlib ray-casting test.

**Tier "context"** — outside ``kuk_clip``, within a Mitteleuropa/Danube rectangle
    (W=4°, S=40°, N=54°, E=32°): only important cities/towns, i.e.
    ``place=city`` *or* ``population ≥ 50 000``.

Each feature carries ``tier``, ``importance``, ``kind``, and (where available)
``population`` and ``name_de``, so QGIS can drive scale-dependent label
visibility from a single layer.

Output (EPSG:4326)
------------------
  data/processed/cities.geojson         one Point per settlement
  data/raw/osm_cities_kuk.json          raw Overpass cache — inner areal
  data/raw/osm_cities_context.json      raw Overpass cache — outer ring

Attribution (required when redistributing)
-------------------------------------------
  Geometry / tags: © OpenStreetMap contributors, ODbL 1.0.
  German names: Wikidata, CC0.

Usage
-----
  uv run reiseplan-cli fetch-cities              # full online fetch
  uv run reiseplan-cli fetch-cities --offline    # rebuild from cache (no network)
  uv run reiseplan-cli fetch-cities --no-enrich  # skip Wikidata name enrichment
"""

from __future__ import annotations

import datetime
import json

from .enrich import german_names, resolve_name_de
from .overpass import OVERPASS_URL
from .paths import ROOT
from .repository import feature_collection, write_json
from .themes import KUK_ROI
from .tiles import BBox, fetch_tiled

# ---------------------------------------------------------------------------
# Paths and ROIs
# ---------------------------------------------------------------------------

_KUK_CLIP_PATH = ROOT / "data" / "reference" / "historical" / "kuk_clip.geojson"
_WIKIDATA_CACHE = ROOT / "data" / "raw" / "wikidata_de_labels.json"

_RAW_KUK  = ROOT / "data" / "raw" / "osm_cities_kuk.json"
_RAW_CTX  = ROOT / "data" / "raw" / "osm_cities_context.json"
_OUT_PATH = ROOT / "data" / "processed" / "cities.geojson"
_ATTR_PATH = ROOT / "data" / "processed" / "cities_attribution.json"

# Mitteleuropa/Danube bounding box — contains KUK_ROI; outer-ring fetch.
CONTEXT_ROI = BBox(south=40.0, west=4.0, north=54.0, east=32.0)

# Outer-tier thresholds
_OUTER_POP_THRESHOLD = 50_000

# Importance thresholds (used for both tiers)
_IMP1_POP = 100_000   # importance 1: city or population ≥ this
_IMP2_POP  =  10_000  # importance 2: town or population ≥ this
# importance 3: village or anything smaller


# ---------------------------------------------------------------------------
# Point-in-polygon — stdlib ray-casting, no shapely
# ---------------------------------------------------------------------------

def _load_kuk_ring() -> list[tuple[float, float]]:
    """Return the outer ring of the kuk_clip polygon as (lon, lat) pairs."""
    raw = json.loads(_KUK_CLIP_PATH.read_text(encoding="utf-8"))
    coords = raw["features"][0]["geometry"]["coordinates"][0]
    return [(float(x), float(y)) for x, y in coords]


def _in_ring(lon: float, lat: float, ring: list[tuple[float, float]]) -> bool:
    """Return True when (lon, lat) lies inside the polygon ring.

    Uses the ray-casting algorithm (odd number of edge crossings = inside).
    Valid for a single, non-self-intersecting ring without Antimeridian issues.
    """
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            xint = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lon < xint:
                inside = not inside
    return inside


# ---------------------------------------------------------------------------
# Overpass query builders
# ---------------------------------------------------------------------------

_QUERY_TIMEOUT = 90


def build_inner_query(s: float, w: float, n: float, e: float) -> str:
    """All named place=city|town|village nodes within a tile (inner tier)."""
    bb = f"{s},{w},{n},{e}"
    return (
        f"[out:json][timeout:{_QUERY_TIMEOUT}];\n"
        f'node["place"~"^(city|town|village)$"]["name"]({bb});\n'
        "out tags center;\n"
    )


def build_city_query(s: float, w: float, n: float, e: float) -> str:
    """All named place=city nodes within a tile (outer tier — cities)."""
    bb = f"{s},{w},{n},{e}"
    return (
        f"[out:json][timeout:{_QUERY_TIMEOUT}];\n"
        f'node["place"="city"]["name"]({bb});\n'
        "out tags center;\n"
    )


def build_town_pop_query(s: float, w: float, n: float, e: float) -> str:
    """Named place=town nodes that carry a population tag (outer tier — large towns)."""
    bb = f"{s},{w},{n},{e}"
    return (
        f"[out:json][timeout:{_QUERY_TIMEOUT}];\n"
        f'node["place"="town"]["name"]["population"]({bb});\n'
        "out tags center;\n"
    )


# ---------------------------------------------------------------------------
# Element → place record
# ---------------------------------------------------------------------------

def _parse_element(el: dict) -> dict | None:
    """Extract a place record from a raw Overpass node element.

    Returns ``None`` if the element has no usable coordinates or name.
    """
    tags = el.get("tags", {})
    name = tags.get("name")
    if not name:
        return None

    # Nodes carry lat/lon directly; ways/areas use center.
    center = el.get("center", {})
    lat = el["lat"] if "lat" in el else center.get("lat")
    lon = el["lon"] if "lon" in el else center.get("lon")
    if lat is None or lon is None:
        return None

    from .geo import parse_population
    return {
        "name":       name,
        "name_de":    tags.get("name:de"),
        "kind":       tags.get("place"),
        "population": parse_population(tags.get("population", "")),
        "wikidata":   tags.get("wikidata"),
        "lon":        float(lon),
        "lat":        float(lat),
        # Keep the raw element so german_names can extract its wikidata tag.
        "_el":        el,
    }


# ---------------------------------------------------------------------------
# Importance classification
# ---------------------------------------------------------------------------

def _assign_importance(kind: str | None, population: int | None) -> int:
    """Return an importance tier (1 = major … 3 = minor).

    1 — place=city or population ≥ 100 000
    2 — place=town or population ≥  10 000
    3 — everything else (villages, unknown)
    """
    pop = population or 0
    if kind == "city" or pop >= _IMP1_POP:
        return 1
    if kind == "town" or pop >= _IMP2_POP:
        return 2
    return 3


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _place_key(place: dict) -> str:
    """Stable identity key — Wikidata QID when present, else rounded coordinates."""
    if place.get("wikidata"):
        return place["wikidata"]
    return f"{round(place['lon'], 5)},{round(place['lat'], 5)}"


# ---------------------------------------------------------------------------
# GeoJSON feature builder
# ---------------------------------------------------------------------------

def _to_feature(
    place: dict,
    tier: str,
    wikidata_de: dict,
) -> dict:
    """Build a GeoJSON Point feature from a place record."""
    importance = _assign_importance(place["kind"], place["population"])

    tags_for_enrich = {}
    if place.get("name_de"):
        tags_for_enrich["name:de"] = place["name_de"]
    if place.get("wikidata"):
        tags_for_enrich["wikidata"] = place["wikidata"]

    name_de, _ = resolve_name_de(place["name"], tags_for_enrich, wikidata_de)

    props: dict = {
        "name":       place["name"],
        "kind":       place["kind"],
        "tier":       tier,
        "importance": importance,
    }
    if name_de:
        props["name_de"] = name_de
    if place.get("population") is not None:
        props["population"] = place["population"]
    if place.get("wikidata"):
        props["wikidata"] = place["wikidata"]

    return {
        "type":       "Feature",
        "properties": props,
        "geometry":   {"type": "Point", "coordinates": [place["lon"], place["lat"]]},
    }


# ---------------------------------------------------------------------------
# Attribution sidecar
# ---------------------------------------------------------------------------

def _attribution() -> dict:
    return {
        "generated":       datetime.date.today().isoformat(),
        "source":          "OpenStreetMap via Overpass API",
        "url":             OVERPASS_URL,
        "license":         "ODbL 1.0 — © OpenStreetMap contributors",
        "attribution_url": "https://www.openstreetmap.org/copyright",
        "name_de_source": {
            "source":  "Wikidata (wbgetentities labels, languages=de)",
            "license": "CC0",
            "cache":   str(_WIKIDATA_CACHE.relative_to(ROOT)),
            "note": (
                "Where OSM has no name:de tag but the feature carries a "
                "wikidata QID, the German label is used as name_de."
            ),
        },
        "methodology": {
            "tier_kuk": {
                "description": (
                    "All named place=city|town|village nodes within the "
                    "historic k.u.k. empire polygon (kuk_clip.geojson). "
                    "Fetched via tiled Overpass over KUK_ROI bbox, then "
                    "clipped to the actual polygon using ray-casting."
                ),
                "roi_bbox": {
                    "south": KUK_ROI.south,
                    "west":  KUK_ROI.west,
                    "north": KUK_ROI.north,
                    "east":  KUK_ROI.east,
                },
                "place_types": ["city", "town", "village"],
            },
            "tier_context": {
                "description": (
                    "Major cities and large towns OUTSIDE kuk_clip, within "
                    "a Mitteleuropa/Danube rectangle. "
                    "Kept: place=city OR population >= 50 000."
                ),
                "roi_bbox": {
                    "south": CONTEXT_ROI.south,
                    "west":  CONTEXT_ROI.west,
                    "north": CONTEXT_ROI.north,
                    "east":  CONTEXT_ROI.east,
                },
                "filter": f"place=city OR population >= {_OUTER_POP_THRESHOLD}",
            },
            "importance_scale": {
                "1": "place=city or population >= 100 000",
                "2": "place=town or population >= 10 000",
                "3": "village or smaller",
            },
        },
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(offline: bool = False, enrich: bool = True) -> None:
    """End-to-end: two Overpass fetches → polygon clip → enrich → GeoJSON."""

    # ── Stage 1: fetch inner tier (kuk_clip bbox, then polygon-clip) ──────
    print("[cities]  Tier 'kuk': Overpass inner fetch …")
    inner_elements = fetch_tiled(
        KUK_ROI,
        [build_inner_query],
        _RAW_KUK,
        offline,
        label="cities_kuk",
    ).unwrap_or_exit()

    kuk_ring = _load_kuk_ring()
    inner_places: dict[str, dict] = {}
    for el in inner_elements:
        rec = _parse_element(el)
        if rec is None:
            continue
        if not _in_ring(rec["lon"], rec["lat"], kuk_ring):
            continue
        key = _place_key(rec)
        if key not in inner_places:
            inner_places[key] = rec

    print(f"[cities]  Tier 'kuk': {len(inner_places)} Orte nach Polygon-Clip.")

    # ── Stage 2: fetch outer tier (context bbox, exclude kuk polygon) ─────
    print("[cities]  Tier 'context': Overpass outer fetch …")
    ctx_elements = fetch_tiled(
        CONTEXT_ROI,
        [build_city_query, build_town_pop_query],
        _RAW_CTX,
        offline,
        label="cities_context",
    ).unwrap_or_exit()

    outer_places: dict[str, dict] = {}
    for el in ctx_elements:
        rec = _parse_element(el)
        if rec is None:
            continue
        # Skip anything already inside the kuk polygon (tier 1 is authoritative).
        if _in_ring(rec["lon"], rec["lat"], kuk_ring):
            continue
        # Apply outer-tier importance filter.
        kind = rec["kind"]
        pop  = rec["population"] or 0
        if kind != "city" and pop < _OUTER_POP_THRESHOLD:
            continue
        key = _place_key(rec)
        # Tier-1 wins dedup across both tiers.
        if key in inner_places:
            continue
        if key not in outer_places:
            outer_places[key] = rec

    print(f"[cities]  Tier 'context': {len(outer_places)} Orte (außerhalb kuk_clip).")

    # ── Stage 3: Wikidata German-name enrichment ──────────────────────────
    all_records  = list(inner_places.values()) + list(outer_places.values())
    all_elements = [r["_el"] for r in all_records]

    if enrich and all_elements:
        wikidata_de = german_names(all_elements, offline, _WIKIDATA_CACHE)
    else:
        wikidata_de = {}

    # ── Stage 4: build features ───────────────────────────────────────────
    features: list[dict] = []
    for key, rec in inner_places.items():
        features.append(_to_feature(rec, "kuk", wikidata_de))
    for key, rec in outer_places.items():
        features.append(_to_feature(rec, "context", wikidata_de))

    # Sort: importance ascending (1 first), then name for stable output.
    features.sort(key=lambda f: (f["properties"]["importance"], f["properties"]["name"]))

    # ── Stage 5: write output ─────────────────────────────────────────────
    write_json(_OUT_PATH, feature_collection("cities", features))
    write_json(_ATTR_PATH, _attribution())

    kuk_count  = sum(1 for f in features if f["properties"]["tier"] == "kuk")
    ctx_count  = sum(1 for f in features if f["properties"]["tier"] == "context")
    print(f"  → {_OUT_PATH.relative_to(ROOT)}  ({len(features)} Features)")
    print(f"      kuk={kuk_count}  context={ctx_count}")
    imp_counts = {1: 0, 2: 0, 3: 0}
    for f in features:
        imp_counts[f["properties"]["importance"]] += 1
    print(f"      importance 1={imp_counts[1]}  2={imp_counts[2]}  3={imp_counts[3]}")
    print(f"  → {_ATTR_PATH.relative_to(ROOT)}")


def main() -> None:
    """Standalone entry point (``reiseplan-cities``)."""
    import argparse

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Rebuild from cached raw JSON only (no network).",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip Wikidata German-name enrichment.",
    )
    args = parser.parse_args()
    run(offline=args.offline, enrich=not args.no_enrich)


if __name__ == "__main__":
    main()
