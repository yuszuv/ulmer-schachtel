"""Reiseplan – Romania travel planner package.

Layers (innermost first):
  domain          – pure value objects, no IO
  catalog         – static CFR magistrală definitions
  result          – Maybe / Result monads
  http            – shared HTTP/JSON base (USER_AGENT, get_json, chunked)
  geo             – Overpass element → GeoJSON coordinate helpers
  enrich          – German-name enrichment (OSM > Wikipedia > Wikidata, shared)
  repository      – GeoJSON / CSV data access (Repository pattern)
  overpass        – OSM gateway (post_overpass) + station name index
  tiles           – ROI tiling + timed Overpass fetch + JSON cache
  wikidata        – batched wbgetentities lookups (German label + dewiki/dewikivoyage)
  themes/         – ThemeSpec + OutputLayer registry (Pattern 4, Strategy)
    natural       – natural-feature theme (ridges/peaks/landscape)
    mining        – mineral-resources theme (mines/quarries/wells)
    industry      – industry-sites theme (power plants/works)
  thematic        – generic pipeline runner (Template Method)
  fetch_natural   – thin wrapper → thematic.run(themes.natural.SPEC, …)
  wikivoyage      – de.wikivoyage city ingest (Overpass → Wikidata → extracts)
  ingest          – CFR rail data-ingest use-case
  raster          – GDAL subprocess wrappers (hillshade, contours, clip)
  fetch_terrain   – Copernicus DEM → hillshade + contours
  fetch_landcover – CORINE Land Cover clip + reclassify
  packaging       – GPKG build + QField packaging
  tables          – Rich terminal rendering (presentation)
  web             – static site builder (presentation)
  cli             – Command-Registry + argparse entry point
"""
