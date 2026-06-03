"""Build steps: GPKG bundle and QField package.

GpkgBuilder   — runs ogr2ogr to consolidate all vector layers into one GPKG
                (EPSG:3844); idempotent (deletes and recreates on each run).

QFieldPackager — reads qgis/reiseplan.qgs + qgis/reiseplan_attachments.zip,
                 rewrites all datasource paths to local bundle references,
                 and writes a self-contained 3-file QField package:
                   reiseplan.qgz          — project XML + embedded styles
                   reiseplan.gpkg         — all vector layers, EPSG:3844
                   arcanum2_ro_clip.tif   — raster, copied as-is

rewrite_datasources() is a module-level pure function (no IO) so it is directly
importable by tests without instantiating the packager.

LAYERS defines the vector layers included in both the GPKG build and the QGS
rewrite; keeping it here (not in repository.py) avoids pulling ogr2ogr concerns
into the data-access layer.
"""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import NamedTuple

from rich.console import Console

from .paths import QFIELD_DIR, QGIS_DIR, ROOT
from .repository import GPKG_PATH

console = Console()


class _Layer(NamedTuple):
    """Descriptor for one vector layer included in the QField bundle."""
    gpkg_name: str         # output layer name in the QField GPKG
    source: str            # path relative to repo ROOT (the file itself, no |layername= suffix)
    src_layer: str | None  # source layer name for GPKG inputs; None for single-layer files
    qgs_token: str         # the literal datasource string in the .qgs XML to replace


# Vector layers bundled into the QField GPKG.
# Order = ogr2ogr call order; first call creates the GPKG, subsequent calls add layers.
LAYERS: list[_Layer] = [
    # data/processed/ — core travel layers
    _Layer("poi_destinations",
           "data/processed/poi_destinations.geojson", None,
           "../data/processed/poi_destinations.geojson"),
    _Layer("rail_stations",
           "data/processed/rail_stations.geojson", None,
           "../data/processed/rail_stations.geojson"),
    _Layer("rail_lines",
           "data/processed/rail_lines.geojson", None,
           "../data/processed/rail_lines.geojson"),
    _Layer("rail_gaps",
           "data/processed/rail_gaps.geojson", None,
           "../data/processed/rail_gaps.geojson"),
    _Layer("info_markers",
           "data/processed/info_markers.geojson", None,
           "../data/processed/info_markers.geojson"),
    _Layer("wikivoyage_cities",
           "data/processed/wikivoyage_cities.geojson", None,
           "../data/processed/wikivoyage_cities.geojson"),
    # data/reference/historical/ — historical context layers
    _Layer("historische_regionen",
           "data/reference/historical/historische_regionen.geojson", None,
           "../data/reference/historical/historische_regionen.geojson"),
    _Layer("historische_reiche",
           "data/reference/historical/historische_reiche.geojson", None,
           "../data/reference/historical/historische_reiche.geojson"),
    _Layer("historische_staedte",
           "data/reference/historical/historische_staedte.geojson", None,
           "../data/reference/historical/historische_staedte.geojson"),
    _Layer("kuk_clip",
           "data/reference/historical/kuk_clip.geojson", None,
           "../data/reference/historical/kuk_clip.geojson"),
    _Layer("staatsgrenzen",
           "data/reference/historical/staatsgrenzen.geojson", None,
           "../data/reference/historical/staatsgrenzen.geojson"),
    # data/processed/ — natural features (Gebirge & Landschaft)
    _Layer("natural_ridges",
           "data/processed/natural_ridges.geojson", None,
           "../data/processed/natural_ridges.geojson"),
    _Layer("mountain_peaks",
           "data/processed/mountain_peaks.geojson", None,
           "../data/processed/mountain_peaks.geojson"),
    _Layer("landscape_labels",
           "data/processed/landscape_labels.geojson", None,
           "../data/processed/landscape_labels.geojson"),
    # data/processed/ — thematic atlas layers (fetch-mining / fetch-industry)
    # These files are optional at bundle time — only included when present.
    _Layer("mineral_resources",
           "data/processed/mineral_resources.geojson", None,
           "../data/processed/mineral_resources.geojson"),
    _Layer("industry_sites",
           "data/processed/industry_sites.geojson", None,
           "../data/processed/industry_sites.geojson"),
    # data/processed/ — terrain contours (fetch-terrain; optional)
    _Layer("contours",
           "data/processed/contours.geojson", None,
           "../data/processed/contours.geojson"),
    # data/processed/ — land cover (fetch-landcover; optional)
    _Layer("landcover",
           "data/processed/landcover.geojson", None,
           "../data/processed/landcover.geojson"),
    # root GPKG — merged empire polygons (label-only; distinct from the geojson entry above)
    _Layer("historische_reiche_merged",
           "historische_reiche.gpkg", "historische_reiche",
           "../historische_reiche.gpkg|layername=historische_reiche"),
]

# Raster bundled alongside the GPKG (copied verbatim, no reprojection).
RASTER_SOURCE = "data/raster/arcanum2_ro_clip.tif"
RASTER_QGS_TOKEN = "../data/raster/arcanum2_ro_clip.tif"
RASTER_FILENAME = "arcanum2_ro_clip.tif"


# ---------------------------------------------------------------------------
# Pure helper (tested directly)
# ---------------------------------------------------------------------------

def rewrite_datasources(qgs_xml: str, gpkg_filename: str) -> str:
    """Rewrite all local datasource paths in a .qgs XML string to bundle-local references.

    Vector layers:  ``../data/.../xxx.geojson``  →  ``./gpkg_filename|layername=xxx``
    Root GPKG:      ``../historische_reiche.gpkg|layername=...``  → same scheme
    Raster:         ``../data/raster/arcanum2_ro_clip.tif``  →  ``./arcanum2_ro_clip.tif``

    Raises SystemExit with a clear message if an expected path is missing —
    loud failure beats a silently broken half-done package.
    """
    result = qgs_xml

    for layer in LAYERS:
        old = layer.qgs_token
        new = f"./{gpkg_filename}|layername={layer.gpkg_name}"
        if old not in result:
            raise SystemExit(
                f"Erwartete Datenquelle nicht im .qgs gefunden: {old!r}\n"
                "Bitte prüfen ob das Projekt mit relativen Pfaden gespeichert wurde\n"
                "(Projekt → Eigenschaften → Allgemein → Pfade: relativ)."
            )
        result = result.replace(old, new)

    # Raster — copied as-is, just rewrite the path reference.
    if RASTER_QGS_TOKEN not in result:
        raise SystemExit(
            f"Erwartete Raster-Quelle nicht im .qgs gefunden: {RASTER_QGS_TOKEN!r}\n"
            "Bitte prüfen ob das Projekt mit relativen Pfaden gespeichert wurde."
        )
    result = result.replace(RASTER_QGS_TOKEN, f"./{RASTER_FILENAME}")

    return result


# ---------------------------------------------------------------------------
# GpkgBuilder
# ---------------------------------------------------------------------------

class GpkgBuilder:
    """Consolidates all vector layers into a single GPKG (EPSG:3844).

    Source files remain the versioned source of truth; the GPKG is a
    reproducible, gitignored bundle for QGIS/QField (one file, multiple layers)
    reprojected to the project CRS EPSG:3844.
    """

    def build(self) -> None:
        if shutil.which("ogr2ogr") is None:
            raise SystemExit(
                "ogr2ogr nicht gefunden – bitte GDAL installieren "
                "(Arch: 'pacman -S gdal')."
            )

        # Delete first → idempotent, clean rebuild every time.
        GPKG_PATH.unlink(missing_ok=True)

        # Track whether the GPKG file has been created yet (first ogr2ogr call
        # creates it; subsequent calls use -update to add further layers).
        gpkg_created = False

        for layer in LAYERS:
            source_path = ROOT / layer.source
            if not source_path.is_file():
                # Layers marked with a comment "optional" are skipped when missing;
                # core layers (rail, historical, natural) abort loudly.
                _optional = layer.gpkg_name in {
                    "mineral_resources", "industry_sites", "contours", "landcover"
                }
                if _optional:
                    print(f"  ~ {layer.gpkg_name} übersprungen (Datei fehlt: {source_path.name})")
                    continue
                raise SystemExit(f"Quelle fehlt: {source_path}")

            # First call creates the GPKG; subsequent calls add layers via -update.
            update_flags = [] if not gpkg_created else ["-update"]
            gpkg_created = True

            # For GPKG sources we must name the source layer explicitly;
            # for single-layer files (GeoJSON, etc.) this is not needed.
            src_layer_args = [layer.src_layer] if layer.src_layer else []

            subprocess.run(
                [
                    "ogr2ogr", "-f", "GPKG", *update_flags,
                    "-t_srs", "EPSG:3844",
                    str(GPKG_PATH), str(source_path),
                    *src_layer_args,
                    "-nln", layer.gpkg_name,
                ],
                check=True,
            )

        print(f"GPKG gebaut: {GPKG_PATH}")
        for layer in LAYERS:
            print(f"  - {layer.gpkg_name}")


# ---------------------------------------------------------------------------
# QFieldPackager
# ---------------------------------------------------------------------------

class QFieldPackager:
    """Produces a reproducible, self-contained QField package.

    Reads the project source from:
      qgis/reiseplan.qgs              — QGIS project XML
      qgis/reiseplan_attachments.zip  — embedded styles (hNhyAH_styles.db etc.)

    Writes three files to the target directory (default qfield/current/):
      reiseplan.qgz          — project XML (paths rewritten) + styles, bundled as ZIP
      reiseplan.gpkg         — all vector layers in EPSG:3844
      arcanum2_ro_clip.tif   — raster, copied as-is

    Prerequisites:
      data/processed/reiseplan.gpkg must be current → run build-gpkg first.

    Note: the project XML contains ``iccProfileId="attachment:///QGIS4-aLCBqh"``
    which has no backing file in the attachments zip. This is a pre-existing
    QGIS 4 colour-profile reference; QField ignores it with a warning — harmless.
    """

    GPKG_FILENAME = "reiseplan.gpkg"

    def build(self, out_dir: Path | None = None) -> None:
        # ── 1. Prerequisites ────────────────────────────────────────────────
        if not GPKG_PATH.is_file():
            raise SystemExit(
                "reiseplan.gpkg nicht gefunden — bitte zuerst ausführen:\n"
                "  uv run reiseplan-cli build-gpkg"
            )

        qgs_path = QGIS_DIR / "reiseplan.qgs"
        if not qgs_path.is_file():
            raise SystemExit(f"Projektdatei nicht gefunden: {qgs_path}")

        attachments_zip = QGIS_DIR / "reiseplan_attachments.zip"
        if not attachments_zip.is_file():
            raise SystemExit(f"Attachments-ZIP nicht gefunden: {attachments_zip}")

        raster_path = ROOT / RASTER_SOURCE
        if not raster_path.is_file():
            raise SystemExit(f"Raster nicht gefunden: {raster_path}")

        # ── 2. Target directory ─────────────────────────────────────────────
        # Default: qfield/current/ — fixed Syncthing path; overridable via --out.
        target = out_dir or QFIELD_DIR / "current"
        target.mkdir(parents=True, exist_ok=True)

        # ── 3. Rewrite datasources in the .qgs XML ──────────────────────────
        qgs_xml = qgs_path.read_text(encoding="utf-8")
        qgs_rewritten = rewrite_datasources(qgs_xml, self.GPKG_FILENAME)

        # ── 4. Write .qgz (ZIP of rewritten .qgs + all styles from attachments) ──
        out_qgz = target / "reiseplan.qgz"
        with zipfile.ZipFile(out_qgz, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            zout.writestr("reiseplan.qgs", qgs_rewritten.encode("utf-8"))
            with zipfile.ZipFile(attachments_zip) as zatt:
                for entry in zatt.infolist():
                    zout.writestr(entry, zatt.read(entry.filename))

        # ── 5. Copy GPKG and raster next to the .qgz ───────────────────────
        shutil.copy2(GPKG_PATH, target / self.GPKG_FILENAME)
        shutil.copy2(raster_path, target / RASTER_FILENAME)

        # ── 6. Success output ───────────────────────────────────────────────
        console.print(f"\n[bold green]✓  QField-Paket erstellt[/bold green]  →  {target}")
        console.print(f"   [dim]reiseplan.qgz[/dim]          Projektdatei (Datenquellen → Bundle)")
        console.print(f"   [dim]reiseplan.gpkg[/dim]         {len(LAYERS)} Vektorlayer in EPSG:3844")
        console.print(f"   [dim]{RASTER_FILENAME}[/dim]  Raster (kopiert)")
        console.print()
        console.print(
            "[dim]Syncthing-Hinweis: qfield/current/ synct auf das Gerät.\n"
            "In QField: Ordner öffnen → reiseplan.qgz antippen.[/dim]"
        )
