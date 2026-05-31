#!/usr/bin/env python3
"""Pack a .qgs project into a .qgz bundle for QField export.

QGIS 4.0 stores project attachments in one of two ways alongside a .qgs file:
  - <project>_attachments.zip  (created when saving .qgs in QGIS 4.0)
  - <project>_styles.db        (manually extracted or from older format)

Both are handled transparently. The output .qgz contains the .qgs plus all
attachment files, which QGIS resolves via the attachment:/// URI scheme.

Usage:
    uv run tools/export_qfield.py                          # exports reiseplan.qgs → qfield/
    uv run tools/export_qfield.py qgis/reiseplan.qgs       # explicit source
    uv run tools/export_qfield.py qgis/reiseplan.qgs out/  # custom output dir
"""

import pathlib
import sys
import zipfile

DEFAULT_SOURCE = pathlib.Path("qgis/reiseplan.qgs")
DEFAULT_TARGET_DIR = pathlib.Path("qfield")


def pack_qgz(qgs_path: pathlib.Path, target_dir: pathlib.Path) -> pathlib.Path:
    qgs_path = qgs_path.resolve()
    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    attachments_zip = qgs_path.with_name(qgs_path.stem + "_attachments.zip")
    styles_db = qgs_path.with_name(qgs_path.stem + "_styles.db")

    out_path = target_dir / qgs_path.with_suffix(".qgz").name
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        zout.write(qgs_path, qgs_path.name)

        if attachments_zip.exists():
            with zipfile.ZipFile(attachments_zip) as zin:
                for entry in zin.infolist():
                    zout.writestr(entry, zin.read(entry.filename))
        elif styles_db.exists():
            zout.write(styles_db, styles_db.name)
        else:
            raise FileNotFoundError(
                f"no attachments found for {qgs_path.name}: "
                f"expected {attachments_zip.name} or {styles_db.name}"
            )

    print(f"exported: {out_path}")
    return out_path


def main() -> None:
    args = sys.argv[1:]
    qgs_path = pathlib.Path(args[0]) if len(args) >= 1 else DEFAULT_SOURCE
    target_dir = pathlib.Path(args[1]) if len(args) >= 2 else DEFAULT_TARGET_DIR
    pack_qgz(qgs_path, target_dir)


if __name__ == "__main__":
    main()
