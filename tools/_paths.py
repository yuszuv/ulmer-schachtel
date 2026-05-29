from pathlib import Path


def find_repo_root() -> Path:
    """Repo-Wurzel = erstes Verzeichnis mit ``data/processed``.

    Funktioniert sowohl per ``uv run python tools/...`` als auch per
    installiertem Entrypoint (dann liegt ``__file__`` im venv, nicht im Repo).
    """
    for base in (Path.cwd(), *Path.cwd().parents,
                 Path(__file__).resolve().parent, *Path(__file__).resolve().parents):
        if (base / "data" / "processed").is_dir():
            return base
    raise SystemExit("data/processed nicht gefunden – bitte aus dem Repo ausführen.")


ROOT = find_repo_root()
PROCESSED = ROOT / "data" / "processed"
