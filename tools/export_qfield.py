#!/usr/bin/env python3
"""Canonical QField export: build GPKG + pack self-contained .qgz bundle.

Produces a 3-file package in qfield/current/ (or a custom --out folder):

  reiseplan.qgz          — project XML (datasources rewritten) + embedded styles
  reiseplan.gpkg         — all vector layers (12), EPSG:3844
  arcanum2_ro_clip.tif   — Arcanum raster, copied as-is

Usage:
    uv run tools/export_qfield.py                # → qfield/current/
    uv run tools/export_qfield.py --out ~/some/path
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as a standalone script without installing the package.
sys.path.insert(0, str(Path(__file__).parent))

from reiseplan.packaging import GpkgBuilder, QFieldPackager


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--out",
        metavar="DIR",
        default=None,
        help="Zielordner (Standard: qfield/current/)",
    )
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else None

    GpkgBuilder().build()
    QFieldPackager().build(out_dir)


if __name__ == "__main__":
    main()
