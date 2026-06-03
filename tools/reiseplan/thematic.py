"""Generic thematic-layer pipeline runner — Pattern 4 (Template Method).

``run(spec, offline, enrich, **opts)`` is the single entry point for any
ThemeSpec-based data fetch.  It wires together tiles, enrich, geo, and
repository into a reproducible pipeline:

    fetch_tiled  →  german_names  →  _build_features  →  write GeoJSON + attribution

Importable from cli.py and from each thin fetch_*.py wrapper.

The three theme modules are imported here (side effect: populates
themes.REGISTRY so ``REGISTRY["natural"]`` etc. work anywhere after this
module is loaded).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .enrich import german_names, resolve_name_de
from .wikidata import WikidataNames
from . import geo
from .paths import ROOT
from .repository import feature_collection, write_json
from .tiles import BBox, fetch_tiled
from .themes import REGISTRY, OutputLayer, ThemeSpec
# Side-effectful imports — registers the three specs into REGISTRY.
from .themes import natural as _th_natural   # noqa: F401
from .themes import mining  as _th_mining    # noqa: F401
from .themes import industry as _th_industry  # noqa: F401

PROCESSED        = ROOT / "data" / "processed"
RAW              = ROOT / "data" / "raw"
WIKIDATA_CACHE   = RAW / "wikidata_de_labels.json"
_QUERY_TIMEOUT   = 75  # seconds, embedded in the Overpass QL header


# ---------------------------------------------------------------------------
# Overpass query builders
# ---------------------------------------------------------------------------

def _overpass_filter(selector: str) -> str:
    """Convert ``'key=value'`` to Overpass QL filter ``'["key"="value"]'``."""
    if "=" in selector:
        key, value = selector.split("=", 1)
        return f'["{key}"="{value}"]'
    return f'["{selector}"]'


def _node_query_builder(
    filters: tuple[str, ...], require_name: bool
) -> Any:  # Callable[[float,float,float,float], str]
    """Return a node query builder for the given filter tuple."""
    name_part = '["name"]' if require_name else ""
    filter_strs = [_overpass_filter(f) for f in filters]

    def builder(s: float, w: float, n: float, e: float) -> str:
        bb = f"{s},{w},{n},{e}"
        lines = "\n".join(f'  node{flt}{name_part}({bb});' for flt in filter_strs)
        return (
            f"[out:json][timeout:{_QUERY_TIMEOUT}];\n"
            f"(\n{lines}\n);\n"
            "out geom;\n"
        )
    return builder


def _way_query_builder(
    filters: tuple[str, ...], require_name: bool
) -> Any:
    """Return a way query builder (LineString geometry)."""
    name_part = '["name"]' if require_name else ""
    filter_strs = [_overpass_filter(f) for f in filters]

    def builder(s: float, w: float, n: float, e: float) -> str:
        bb = f"{s},{w},{n},{e}"
        lines = "\n".join(f'  way{flt}{name_part}({bb});' for flt in filter_strs)
        return (
            f"[out:json][timeout:{_QUERY_TIMEOUT}];\n"
            f"(\n{lines}\n);\n"
            "out geom;\n"
        )
    return builder


def _area_query_builder(
    filters: tuple[str, ...], require_name: bool
) -> Any:
    """Return an area query builder (way centroid via ``out tags center;``)."""
    name_part = '["name"]' if require_name else ""
    filter_strs = [_overpass_filter(f) for f in filters]

    def builder(s: float, w: float, n: float, e: float) -> str:
        bb = f"{s},{w},{n},{e}"
        lines = "\n".join(f'  way{flt}{name_part}({bb});' for flt in filter_strs)
        return (
            f"[out:json][timeout:{_QUERY_TIMEOUT}];\n"
            f"(\n{lines}\n);\n"
            "out tags center;\n"
        )
    return builder


def _query_builders(spec: ThemeSpec) -> list:
    """Build the ordered list of Overpass query callables for a ThemeSpec."""
    builders = []
    if spec.way_filters:
        builders.append(_way_query_builder(spec.way_filters, spec.require_name))
    if spec.node_filters:
        builders.append(_node_query_builder(spec.node_filters, spec.require_name))
    if spec.area_filters:
        builders.append(_area_query_builder(spec.area_filters, spec.require_name))
    return builders


# ---------------------------------------------------------------------------
# Feature builder
# ---------------------------------------------------------------------------

def _build_features(
    elements: list[dict],
    spec: ThemeSpec,
    wikidata_de: dict[str, WikidataNames],
    opts: dict,
) -> dict[str, list[dict]]:
    """Classify elements into per-layer GeoJSON feature lists.

    For each element:
    1. Apply ``require_name`` and ``filter_el`` gates.
    2. Build common props (osm_id, osm_type, name, name_de, name_de_src, wikidata).
    3. Call ``extra_props(el, tags, opts)`` — ``None`` return means skip.
    4. Merge common + extra props.
    5. Find the first ``OutputLayer`` whose ``accepts(el)`` returns ``True``.
    6. Extract the geometry (LineString / Point / centroid) for that layer.
    7. Append the GeoJSON Feature.
    """
    get_extra = spec.extra_props or (lambda el, tags, opts: {})
    filter_fn = spec.filter_el   or (lambda el, tags, opts: True)

    out: dict[str, list[dict]] = {layer.key: [] for layer in spec.layers}

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")

        if spec.require_name and not name:
            continue
        if not filter_fn(el, tags, opts):
            continue

        extra = get_extra(el, tags, opts)
        if extra is None:
            continue  # spec says skip this element

        # Common properties (shared across all themes)
        name_de, name_de_src = resolve_name_de(name, tags, wikidata_de)
        props = {
            "osm_id":      el.get("id"),
            "osm_type":    el.get("type"),
            "name":        name,
            "name_de":     name_de,
            "name_de_src": name_de_src,
            "wikidata":    tags.get("wikidata"),
            **extra,
        }

        # Claim element with the first matching OutputLayer
        el_type = el.get("type")
        for layer in spec.layers:
            if not layer.accepts(el):
                continue

            if layer.geom == "LineString":
                coords = geo.way_to_linestring(el)
                if coords is None:
                    break
                out[layer.key].append({
                    "type": "Feature",
                    "properties": props,
                    "geometry": {"type": "LineString", "coordinates": coords},
                })
            elif layer.geom == "Point":
                if el_type == "node":
                    point = geo.node_to_point(el)
                elif el_type == "way":
                    # area with "out tags center;" → use centroid
                    point = geo.centroid_of(el)
                else:
                    point = None
                if point is None:
                    break
                out[layer.key].append({
                    "type": "Feature",
                    "properties": props,
                    "geometry": {"type": "Point", "coordinates": point},
                })
            break  # element claimed; don't check further layers

    return out


def _sort_features(features: list[dict], layer: OutputLayer) -> list[dict]:
    """Return a sorted copy using ``layer.sort_key`` (or name-sort by default)."""
    key_fn = layer.sort_key or (lambda f: f["properties"].get("name") or "")
    return sorted(features, key=key_fn)


def _count_de_sources(*feature_lists: list[dict]) -> tuple[int, int, int]:
    """Return ``(osm, wikipedia, wikidata)`` counts of features with a German name."""
    osm = wiki = wd = 0
    for features in feature_lists:
        for f in features:
            src = f["properties"].get("name_de_src")
            if src == "osm":
                osm += 1
            elif src == "wikipedia":
                wiki += 1
            elif src == "wikidata":
                wd += 1
    return osm, wiki, wd


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(
    spec: ThemeSpec,
    *,
    offline: bool = False,
    enrich: bool  = True,
    **opts,
) -> None:
    """End-to-end: tiled Overpass fetch → Wikidata enrich → GeoJSON + attribution.

    ``**opts`` are forwarded to ``spec.extra_props`` and ``spec.filter_el``
    (e.g. ``min_ele=1500`` for the natural theme's peak filter).
    """
    cache_path = RAW / f"osm_{spec.name}_features.json"

    elements = fetch_tiled(
        spec.roi,
        _query_builders(spec),
        cache_path,
        offline,
        label=spec.name,
    ).unwrap_or_exit()

    if enrich and spec.enrich_de:
        wikidata_de = german_names(elements, offline, WIKIDATA_CACHE)
    else:
        wikidata_de = {}

    print(f"[parse]   {len(elements)} Overpass-Elemente verarbeiten …")
    layer_features = _build_features(elements, spec, wikidata_de, opts)

    sorted_layers: list[tuple[OutputLayer, list[dict]]] = []
    for layer in spec.layers:
        feats = _sort_features(layer_features[layer.key], layer)
        sorted_layers.append((layer, feats))
        write_json(PROCESSED / layer.filename,
                   feature_collection(layer.key, feats))

    if spec.attribution:
        attr_path = PROCESSED / f"{spec.name}_attribution.json"
        write_json(attr_path, spec.attribution())

    all_feat_lists = [feats for _, feats in sorted_layers]
    osm_de, wiki_de, wd_de = _count_de_sources(*all_feat_lists)

    for layer, feats in sorted_layers:
        print(f"  → {(PROCESSED / layer.filename).relative_to(ROOT)}"
              f"  ({len(feats)} Features)")
    if spec.attribution:
        print(f"  → {attr_path.relative_to(ROOT)}")
    if enrich and spec.enrich_de:
        print(f"[de-namen] {osm_de} aus OSM name:de, {wiki_de} aus Wikipedia, "
              f"{wd_de} aus Wikidata")
    print(f"[done]    {spec.name} fertig.")


# ---------------------------------------------------------------------------
# Console-script entry points for mining / industry
# (reiseplan-natural uses fetch_natural.main for full argparse compatibility)
# ---------------------------------------------------------------------------

def _main_for(name: str) -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description=f"Fetch {name} features from OSM Overpass.",
    )
    parser.add_argument(
        "--offline", action="store_true",
        help=f"Rebuild from data/raw/osm_{name}_features.json (no network).",
    )
    parser.add_argument(
        "--no-enrich", action="store_true",
        help="Skip Wikidata German-name enrichment.",
    )
    args = parser.parse_args()
    run(REGISTRY[name], offline=args.offline, enrich=not args.no_enrich)


def _main_mining() -> None:
    _main_for("mining")


def _main_industry() -> None:
    _main_for("industry")
