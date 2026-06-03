"""Natural-feature ingest — mountain ridges, peaks, valleys, landscape labels.

Thin wrapper around the generic thematic pipeline (see thematic.py and
themes/natural.py).  The fetch logic, output structure, and Wikidata
enrichment now live in the shared infrastructure so they can be reused by
other atlas themes without duplication.

Output layers (EPSG:4326)
--------------------------
  data/processed/natural_ridges.geojson    — LineString  (natural=ridge ways)
  data/processed/mountain_peaks.geojson    — Point       (natural=peak nodes)
  data/processed/landscape_labels.geojson  — Point       (mountain_range, valley,
                                                           region label anchors)
  data/processed/natural_attribution.json  — ODbL + Wikidata CC0 sidecar

Attribution (required when redistributing)
-------------------------------------------
  Geometry / tags: OpenStreetMap via Overpass API.
  © OpenStreetMap contributors, ODbL 1.0.
  German names enriched via Wikidata (wbgetentities labels).  CC0.

Usage
-----
  uv run reiseplan-natural                 # fetch online + cache + enrich
  uv run reiseplan-natural --offline       # rebuild from data/raw caches (no network)
  uv run reiseplan-natural --min-ele 1500  # keep only peaks ≥ 1500 m (default)
  uv run reiseplan-natural --no-enrich     # skip Wikidata, name_de from OSM only
"""

from __future__ import annotations

import argparse

from .thematic import run as _thematic_run
from .themes.natural import SPEC


def run(offline: bool = False, min_ele: int = 1500, enrich: bool = True) -> None:
    """End-to-end: tiled Overpass fetch → Wikidata enrich → 3 GeoJSON + attribution."""
    _thematic_run(SPEC, offline=offline, enrich=enrich, min_ele=min_ele)


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
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip Wikidata German-name enrichment (name_de from OSM only).",
    )
    args = parser.parse_args()
    run(offline=args.offline, min_ele=args.min_ele, enrich=not args.no_enrich)


if __name__ == "__main__":
    main()
