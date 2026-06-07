"""Vendor the Muris Atlas Design System into vendor/muris-atlas/.

Downloads (or reads from a local file) the design-system export tarball and
extracts the canonical token files and fonts into a versioned vendor directory.
The vendored files are the single source of truth for the site build; run this
command whenever the upstream design system is updated.

Usage:
    uv run reiseplan-vendor-design                          # live download
    uv run reiseplan-vendor-design --file /path/to/ds.bin  # from local tarball
    uv run reiseplan-vendor-design --url <custom-url>       # alternate endpoint

Source: https://claude.ai/design/p/d9d61088-d2af-40aa-9826-03653630082e
Export: https://api.anthropic.com/v1/design/h/yH3MwJYkrVUXa-fdGHz1Ug
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import tarfile
import urllib.request
from pathlib import Path

from .http import USER_AGENT, read_url
from .paths import ROOT

DESIGN_PROJECT_URL = "https://claude.ai/design/p/d9d61088-d2af-40aa-9826-03653630082e"
DESIGN_EXPORT_URL  = "https://api.anthropic.com/v1/design/h/yH3MwJYkrVUXa-fdGHz1Ug"

VENDOR_DIR = ROOT / "vendor" / "muris-atlas"

# Paths inside the tarball (prefix + project/)
_TAR_PREFIX   = "muris-atlas-design-system/project/"
_TOKENS_CSS   = "colors_and_type.css"
_TOKENS_JSON  = "figma/tokens.json"
_FONTS_SUBDIR = "fonts/"


def _fetch_tarball(url: str) -> bytes:
    """Download the design-system export tarball via the shared HTTP helper."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    print(f"Lade Design-Export von {url} …")
    data = read_url(req, timeout=180)
    print(f"  {len(data):,} Bytes empfangen")
    return data


def _extract(data: bytes, vendor_dir: Path) -> list[str]:
    """Extract the whitelisted files from the gzip tarball into vendor_dir.

    Uses a member whitelist (never extractall) to prevent path-traversal
    exploits: only files under the known project/ prefix are written, and only
    to the expected subdirectory layout inside vendor_dir.
    """
    vendor_dir.mkdir(parents=True, exist_ok=True)
    fonts_dir = vendor_dir / "fonts"
    fonts_dir.mkdir(exist_ok=True)

    written: list[str] = []

    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            rel = member.name
            if not rel.startswith(_TAR_PREFIX):
                continue
            inner = rel[len(_TAR_PREFIX):]   # path relative to project/

            if inner == _TOKENS_CSS:
                dest = vendor_dir / _TOKENS_CSS
            elif inner == _TOKENS_JSON:
                (vendor_dir / "figma").mkdir(exist_ok=True)
                dest = vendor_dir / "figma" / "tokens.json"
            elif inner.startswith(_FONTS_SUBDIR):
                face = Path(inner).name
                dest = fonts_dir / face
            else:
                continue  # not in the whitelist

            body = tf.extractfile(member)
            if body is None:
                continue
            dest.write_bytes(body.read())
            written.append(str(dest.relative_to(ROOT)))

    return sorted(written)


def _write_vendor_md(vendor_dir: Path, url: str, sha256: str, files: list[str]) -> None:
    """Write a provenance record so every vendor snapshot is auditable."""
    today = datetime.date.today().isoformat()
    lines = [
        "# vendor/muris-atlas — Muris Atlas Design System",
        "",
        f"**Design project:** {DESIGN_PROJECT_URL}",
        f"**Export URL:**     {url}",
        f"**Fetched:**        {today}",
        f"**SHA-256:**        {sha256}",
        "",
        "## Vendored files",
        "",
    ]
    for f in files:
        lines.append(f"- `{f}`")
    lines += [
        "",
        "## Updating",
        "",
        "Run `uv run reiseplan-vendor-design` to re-fetch the latest export.",
        "Rebuild the site afterwards: `uv run reiseplan-site --out site`.",
        "",
        "## Switching to a git submodule later",
        "",
        "If the design system is ever published as its own git repository, replace",
        "this directory with a submodule at the same path (`vendor/muris-atlas/`)",
        "and remove or repurpose this script.",
    ]
    (vendor_dir / "VENDOR.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="reiseplan-vendor-design",
        description="Vendors the Muris Atlas Design System into vendor/muris-atlas/.",
    )
    parser.add_argument(
        "--url",
        default=DESIGN_EXPORT_URL,
        help="Design-export endpoint (default: %(default)s)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        metavar="PATH",
        help="Use a locally downloaded tarball instead of fetching from --url.",
    )
    args = parser.parse_args()

    if args.file:
        print(f"Lese lokalen Tarball: {args.file}")
        data = args.file.read_bytes()
    else:
        data = _fetch_tarball(args.url)

    sha256 = hashlib.sha256(data).hexdigest()
    print(f"SHA-256: {sha256}")

    files = _extract(data, VENDOR_DIR)
    if not files:
        raise SystemExit(
            "Keine Dateien extrahiert — Tarball-Format geändert? "
            f"Erwartet: Prefix '{_TAR_PREFIX}'"
        )

    _write_vendor_md(VENDOR_DIR, args.url, sha256, files)
    print(f"\nVendored {len(files)} Datei(en) nach {VENDOR_DIR.relative_to(ROOT)}:")
    for f in files:
        print(f"  {f}")
    print(f"\nVendor-Protokoll: vendor/muris-atlas/VENDOR.md")


if __name__ == "__main__":
    main()
