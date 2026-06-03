"""Thematic-layer pipeline — Pattern 4 (Strategy + Registry).

A ``ThemeSpec`` declares *what* to fetch and *how* to classify the results.
``thematic.run()`` is the generic runner that executes any spec.

Adding a new atlas theme
------------------------
1. Create ``themes/mytheme.py`` that defines a module-level ``SPEC: ThemeSpec``
   and calls ``_register(SPEC)`` at the bottom.
2. Import the module in ``thematic.py`` (alongside existing theme imports) so
   the spec is registered when the package is loaded.
3. Add a ``@command`` in ``cli.py`` that calls
   ``thematic.run(REGISTRY["mytheme"], …)``.

OutputLayer
-----------
Describes one GeoJSON output file.  ``accepts(el)`` is a static closure that
inspects ``el["type"]`` and ``el["tags"]`` to decide which layer claims the
element.  The first layer in ``ThemeSpec.layers`` whose ``accepts`` returns
``True`` wins.  ``sort_key`` is an optional feature-level sort callable
(receives the full GeoJSON feature dict); ``None`` means sort by name.

ThemeSpec
---------
``extra_props(el, tags, opts) → dict | None``
    Called after the common props (osm_id/type/name/name_de…) are built.
    Return ``None`` to exclude this element from all output layers.
    Return ``{}`` for no extra fields; return ``{"commodity": "coal"}`` etc.

``filter_el(el, tags, opts) → bool``
    Pre-filter called before geometry extraction and before ``extra_props``.
    Return ``False`` to skip.  Default (``None``) = accept all.

``attribution() → dict``
    Returns the sidecar JSON written alongside each run's GeoJSON output.

``enrich_de``
    Whether to attempt Wikidata German-name enrichment (default ``True``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..tiles import BBox


# The k.u.k. / Romania ~1880 extent — shared ROI for all atlas themes.
# Derived from data/reference/historical/kuk_clip.geojson.
KUK_ROI = BBox(south=42.929272, west=9.464611, north=51.077385, east=30.432847)


@dataclass(frozen=True)
class OutputLayer:
    """Descriptor for one GeoJSON output file produced by a ThemeSpec."""
    key:      str                       # e.g. "mineral_resources"
    filename: str                       # → data/processed/<filename>
    geom:     str                       # "Point" | "LineString"
    accepts:  Callable[[dict], bool]    # el → True if this layer claims it
    sort_key: Callable[[dict], Any] | None = None  # None → sort by name


@dataclass(frozen=True)
class ThemeSpec:
    """Declarative specification for one atlas-theme data-ingest pipeline."""
    name:         str              # registry key + raw-cache filename stem
    roi:          BBox
    # Overpass tag selectors per query type.  Each string is one OSM filter,
    # e.g. ``'natural=peak'``, ``'man_made=mineshaft'``, ``'landuse=quarry'``.
    node_filters: tuple[str, ...]  # nodes   → ``out geom;``
    way_filters:  tuple[str, ...]  # ways    → ``out geom;`` (LineString)
    area_filters: tuple[str, ...]  # ways    → ``out tags center;`` (Point centroid)
    require_name: bool             # add ``["name"]`` to all selectors
    layers:       tuple[OutputLayer, ...]
    # (el, tags, opts) → dict | None.  None = skip this element.
    extra_props:  Callable[[dict, dict, dict], dict | None] | None = None
    # (el, tags, opts) → bool.  False = skip before geometry extraction.
    filter_el:    Callable[[dict, dict, dict], bool] | None = None
    # Returns attribution sidecar dict written per-run.
    attribution:  Callable[[], dict] | None = None
    enrich_de:    bool = True


# ---------------------------------------------------------------------------
# Registry — populated by each theme module calling _register(SPEC).
# ---------------------------------------------------------------------------

REGISTRY: dict[str, ThemeSpec] = {}


def _register(spec: ThemeSpec) -> ThemeSpec:
    """Add a ThemeSpec to REGISTRY and return it (use at module level)."""
    REGISTRY[spec.name] = spec
    return spec
