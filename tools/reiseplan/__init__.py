"""Reiseplan – Romania travel planner package.

Layers (innermost first):
  domain     – pure value objects, no IO
  catalog    – static CFR magistrală definitions
  result     – Maybe / Result monads
  repository – GeoJSON / CSV data access (Repository pattern)
  overpass   – OSM gateway + station name index
  ingest     – data-ingest use-case
  packaging  – GPKG build + QField packaging
  tables     – Rich terminal rendering (presentation)
  web        – static site builder (presentation)
  cli        – Command-Registry + argparse entry point
"""
