"""Build steps: GPKG bundle and QField package.

GpkgBuilder   — runs ogr2ogr to consolidate GeoJSON layers into one GPKG
                (EPSG:3844); idempotent (deletes and recreates on each run).

QFieldPackager — opens qgis/reiseplan.qgz (a ZIP), rewrites GeoJSON datasource
                 paths to GPKG layer references, writes the patched .qgz and
                 a GPKG copy side-by-side in the target directory.

rewrite_datasources() is a module-level pure function (no IO) so it is directly
importable by tests without instantiating the packager.

GPKG_LAYERS defines the layer order for both the GPKG build and the QGS rewrite;
keeping it here (not in repository.py) avoids pulling ogr2ogr concerns into the
data-access layer.
"""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

from rich.console import Console

from .paths import QFIELD_DIR, QGIS_DIR
from .repository import GPKG_PATH

console = Console()

# Layername in GPKG → source GeoJSON filename.
# Order = ogr2ogr call order; first call creates the GPKG, subsequent add layers.
GPKG_LAYERS: list[tuple[str, str]] = [
    ("poi_destinations",  "poi_destinations.geojson"),
    ("rail_stations",     "rail_stations.geojson"),
    ("rail_lines",        "rail_lines.geojson"),
    ("info_markers",      "info_markers.geojson"),
]


# ---------------------------------------------------------------------------
# Pure helper (tested directly)
# ---------------------------------------------------------------------------

def rewrite_datasources(qgs_xml: str, gpkg_filename: str) -> str:
    """Rewrite GeoJSON datasource paths in a .qgs XML string to GPKG references.

    The desktop project references vector layers as relative GeoJSON paths
    (``../data/processed/xxx.geojson``).  For the QField package we rewrite
    them to GPKG layer references (``./reiseplan.gpkg|layername=xxx``) so the
    package is entirely self-contained (two files, no external paths).

    Raises SystemExit with a clear message if an expected path is missing —
    loud failure beats a silently broken half-done package.
    """
    result = qgs_xml
    for layer_name, geojson_name in GPKG_LAYERS:
        old = f"../data/processed/{geojson_name}"
        new = f"./{gpkg_filename}|layername={layer_name}"
        if old not in result:
            raise SystemExit(
                f"Erwartete Datenquelle nicht im .qgs gefunden: {old!r}\n"
                "Bitte prüfen ob das Projekt mit relativen Pfaden gespeichert wurde\n"
                "(Projekt → Eigenschaften → Allgemein → Pfade: relativ)."
            )
        result = result.replace(old, new)
    return result


# ---------------------------------------------------------------------------
# GpkgBuilder
# ---------------------------------------------------------------------------

class GpkgBuilder:
    """Consolidates all GeoJSON layers into a single GPKG (EPSG:3844).

    GeoJSON files remain the versioned source of truth (EPSG:4326, GeoJSON
    spec); the GPKG is a reproducible, gitignored bundle for QGIS/QField
    (one file, multiple layers) reprojected to the project CRS EPSG:3844.
    """

    def build(self) -> None:
        if shutil.which("ogr2ogr") is None:
            raise SystemExit(
                "ogr2ogr nicht gefunden – bitte GDAL installieren "
                "(Arch: 'pacman -S gdal')."
            )

        from .repository import PROCESSED  # local import avoids top-level path dep

        # Delete first → idempotent, clean rebuild every time.
        GPKG_PATH.unlink(missing_ok=True)

        for idx, (layer_name, source_file) in enumerate(GPKG_LAYERS):
            source = PROCESSED / source_file
            if not source.is_file():
                raise SystemExit(f"Quelle fehlt: {source}")
            # First call creates the GPKG; subsequent calls add layers via -update.
            update_flags = [] if idx == 0 else ["-update"]
            subprocess.run(
                [
                    "ogr2ogr", "-f", "GPKG", *update_flags,
                    "-t_srs", "EPSG:3844",
                    str(GPKG_PATH), str(source), "-nln", layer_name,
                ],
                check=True,
            )

        print(f"GPKG gebaut: {GPKG_PATH}")
        for layer_name, _ in GPKG_LAYERS:
            print(f"  - {layer_name}")


# ---------------------------------------------------------------------------
# QFieldPackager
# ---------------------------------------------------------------------------

class QFieldPackager:
    """Produces a reproducible QField package from .qgz + .gpkg.

    The package contains exactly two files side-by-side in the target directory:
      reiseplan.qgz   – project file with datasources rewritten to GPKG refs
      reiseplan.gpkg  – data bundle (all four layers, EPSG:3844)

    Prerequisites:
      - data/processed/reiseplan.gpkg must be current → run build-gpkg first.
      - qgis/reiseplan.qgz must be saved with relative paths
        (Projekt → Eigenschaften → Allgemein → Pfade: relativ).
    """

    GPKG_FILENAME = "reiseplan.gpkg"

    def build(self, out_dir: Path | None = None) -> None:
        # ── 1. Prerequisites ────────────────────────────────────────────────
        if not GPKG_PATH.is_file():
            raise SystemExit(
                "reiseplan.gpkg nicht gefunden — bitte zuerst ausführen:\n"
                "  uv run reiseplan-cli build-gpkg"
            )
        qgz_path = QGIS_DIR / "reiseplan.qgz"
        if not qgz_path.is_file():
            raise SystemExit(f"Projektdatei nicht gefunden: {qgz_path}")

        # ── 2. Target directory ─────────────────────────────────────────────
        # Default: qfield/current/ — fixed Syncthing path; overridable via --out.
        target = out_dir or QFIELD_DIR / "current"
        target.mkdir(parents=True, exist_ok=True)

        # ── 3. Open .qgz, rewrite datasources, write patched .qgz ──────────
        # .qgz is a standard ZIP containing a .qgs (QGIS project XML) and
        # optionally a styles DB (.db).  We rewrite only the .qgs member.
        out_qgz = target / "reiseplan.qgz"
        with zipfile.ZipFile(qgz_path, "r") as zin:
            member_names = zin.namelist()
            qgs_name = next((n for n in member_names if n.endswith(".qgs")), None)
            if qgs_name is None:
                raise SystemExit(
                    f"Kein .qgs-Member in {qgz_path} gefunden.\n"
                    f"Inhalt: {member_names}"
                )
            qgs_xml = zin.read(qgs_name).decode("utf-8")
            qgs_rewritten = rewrite_datasources(qgs_xml, self.GPKG_FILENAME)

            with zipfile.ZipFile(out_qgz, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                for name in member_names:
                    data = qgs_rewritten.encode("utf-8") if name == qgs_name else zin.read(name)
                    zout.writestr(name, data)

        # ── 4. Copy GPKG next to the .qgz ──────────────────────────────────
        shutil.copy2(GPKG_PATH, target / self.GPKG_FILENAME)

        # ── 5. Success output ───────────────────────────────────────────────
        console.print(f"\n[bold green]✓  QField-Paket erstellt[/bold green]  →  {target}")
        console.print("   [dim]reiseplan.qgz[/dim]   Projektdatei (Datenquellen → GPKG)")
        console.print(f"   [dim]reiseplan.gpkg[/dim]  {len(GPKG_LAYERS)} Layer in EPSG:3844")
        console.print()
        console.print(
            "[dim]Syncthing-Hinweis: qfield/current/ synct auf das Gerät.\n"
            "In QField: Ordner öffnen → reiseplan.qgz antippen.[/dim]"
        )
