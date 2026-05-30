"""Repository-root resolution and well-known path constants.

Works whether invoked via ``uv run reiseplan-cli`` (CWD = repo root) or via
a plain ``python tools/...`` call — the walker tries both the CWD and the
directory of this file.
"""

from pathlib import Path


def find_repo_root() -> Path:
    """Return the repo root — first ancestor containing ``data/processed``."""
    for base in (
        Path.cwd(),
        *Path.cwd().parents,
        Path(__file__).resolve().parent,
        *Path(__file__).resolve().parents,
    ):
        if (base / "data" / "processed").is_dir():
            return base
    raise SystemExit("data/processed nicht gefunden – bitte aus dem Repo ausführen.")


ROOT = find_repo_root()
PROCESSED = ROOT / "data" / "processed"
QGIS_DIR = ROOT / "qgis"       # project file + styles
QFIELD_DIR = ROOT / "qfield"   # Syncthing folder → device
