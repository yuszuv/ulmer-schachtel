from pathlib import Path


def find_repo_root() -> Path:
    """Return the repo root — first directory containing ``data/processed``.

    Works whether invoked via ``uv run python tools/...`` or via the installed
    entrypoint (where ``__file__`` lives inside the venv, not the repo).
    """
    for base in (Path.cwd(), *Path.cwd().parents,
                 Path(__file__).resolve().parent, *Path(__file__).resolve().parents):
        if (base / "data" / "processed").is_dir():
            return base
    raise SystemExit("data/processed nicht gefunden – bitte aus dem Repo ausführen.")


ROOT = find_repo_root()
PROCESSED = ROOT / "data" / "processed"
QGIS_DIR = ROOT / "qgis"        # Projektdatei + Styles
QFIELD_DIR = ROOT / "qfield"    # Syncthing-Ordner → Handy
