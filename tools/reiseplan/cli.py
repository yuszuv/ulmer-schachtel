"""CLI entry point — Command-Registry pattern (Pattern 1).

Instead of a long build_parser() that manually wires up every subcommand,
each command is registered via the ``@command`` decorator.  build_parser()
then iterates the registry and constructs the argparse tree dynamically.

Benefits:
  • Adding a command = one decorated function, zero boilerplate elsewhere.
  • The registry is inspectable (tests can assert all expected commands exist).
  • Argument declarations live next to the handler, not in a distant parser block.

Usage:
    uv run reiseplan-cli <subcommand> [options]

All data inspection commands accept ``--json`` for machine-readable output.
Build commands (build-gpkg, build-qfield, build-site) have no ``--json`` flag.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from rich.console import Console

from .banner import print_banner

# ---------------------------------------------------------------------------
# Registry infrastructure
# ---------------------------------------------------------------------------

@dataclass
class _Arg:
    """Descriptor for one argparse argument on a command."""
    flags: list[str]         # e.g. ["route_id"] or ["--out", "-o"]
    kwargs: dict             # passed straight to parser.add_argument()


@dataclass
class _CommandSpec:
    name: str
    help: str
    description: str
    handler: Callable
    has_json: bool = False
    args: list[_Arg] = field(default_factory=list)


REGISTRY: list[_CommandSpec] = []


def command(
    name: str,
    *,
    help: str,
    description: str = "",
    json: bool = False,
    args: list[_Arg] | None = None,
) -> Callable:
    """Decorator that registers a CLI subcommand.

    Example::

        @command("list-routes", help="Alle Magistralen anzeigen", json=True)
        def _list_routes(args):
            tables.list_routes(args)
    """
    def decorator(fn: Callable) -> Callable:
        REGISTRY.append(_CommandSpec(
            name=name,
            help=help,
            description=description or help,
            handler=fn,
            has_json=json,
            args=args or [],
        ))
        return fn
    return decorator


def _arg(*flags: str, **kwargs) -> _Arg:
    """Shorthand for declaring a command argument inside @command(args=[...]).

    Usage:
        args=[_arg("route_id", help="z.B. M300")]           # positional
        args=[_arg("--out", metavar="DIR", help="…")]        # optional
    """
    return _Arg(flags=list(flags), kwargs=kwargs)


# ---------------------------------------------------------------------------
# Command registrations
# (imports happen here so tables/packaging don't depend on cli.py)
# ---------------------------------------------------------------------------

from . import packaging, tables, wikivoyage  # noqa: E402  (after registry setup)


@command("list-routes", help="Alle Magistralen anzeigen", json=True)
def _list_routes(args):
    tables.list_routes(args)


@command("list-categories", help="POI-Kategorien anzeigen", json=True)
def _list_categories(args):
    tables.list_categories(args)


@command(
    "list-destinations",
    help="Destinationen anzeigen",
    json=True,
    args=[_arg("--category", help="Filter nach Kategorie")],
)
def _list_destinations(args):
    tables.list_destinations(args)


@command("overview", help="Alle Magistralen inkl. Haltefolge kompakt", json=True)
def _overview(args):
    tables.overview(args)


@command(
    "timetable",
    help="Verbindungen (Abfahrt/Ankunft/via) je Magistrale",
    json=True,
)
def _timetable(args):
    tables.timetable(args)


@command(
    "show-route",
    help="Haltefolge einer Magistrale",
    json=True,
    args=[_arg("route_id", help="z.B. M300")],
)
def _show_route(args):
    tables.show_route(args)


@command(
    "fetch-wikivoyage",
    help="Fetch de.wikivoyage cities for each historical region of Romania",
    description=(
        "Fetches cities (place=city|town) from the historical regions of Romania "
        "via Overpass and keeps only those with an article on de.wikivoyage.org "
        "(the German edition is both source and filter). "
        "Writes data/processed/wikivoyage_cities.geojson. "
        "Sources: OSM © ODbL · WikiVoyage texts CC BY-SA 3.0."
    ),
    args=[_arg("--offline", action="store_true",
               help="Rebuild from data/raw/osm_ro_cities.json only (no network).")],
)
def _fetch_wikivoyage(args):
    wikivoyage.run(args.offline)


@command("build-gpkg", help="GeoJSON zu einer reiseplan.gpkg bündeln")
def _build_gpkg(args):
    packaging.GpkgBuilder().build()


@command(
    "build-qfield",
    help="QField-Paket aus .qgs + GPKG + Raster erzeugen",
    description=(
        "Erzeugt ein selbst-enthaltenes QField-Paket (3 Dateien: "
        "reiseplan.qgz + reiseplan.gpkg + arcanum2_ro_clip.tif) im Zielordner. "
        "Voraussetzung: build-gpkg muss aktuell sein."
    ),
    args=[_arg("--out", metavar="DIR", help="Zielordner (Standard: qfield/current/)")],
)
def _build_qfield(args):
    packaging.QFieldPackager().build(Path(args.out) if args.out else None)


# ---------------------------------------------------------------------------
# Parser builder (iterates registry)
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the full argparse tree from the REGISTRY."""
    parser = argparse.ArgumentParser(
        prog="reiseplan-cli",
        description="Basis-CLI für den Rumänien-Reiseplaner",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Shared parent: --json flag for all data-inspection commands.
    jsonp = argparse.ArgumentParser(add_help=False)
    jsonp.add_argument(
        "--json",
        action="store_true",
        help="Maschinenlesbare JSON-Ausgabe (für Pipes/jq)",
    )

    for spec in REGISTRY:
        parents = [jsonp] if spec.has_json else []
        p = sub.add_parser(
            spec.name,
            help=spec.help,
            description=spec.description,
            parents=parents,
        )
        for arg in spec.args:
            p.add_argument(*arg.flags, **arg.kwargs)
        p.set_defaults(func=spec.handler)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()

    # Nackter Aufruf (kein Subcommand): Banner + Hilfe statt argparse-Fehler.
    if len(sys.argv) == 1:
        print_banner(Console())
        parser.print_help()
        return

    args = parser.parse_args()

    # Banner nach stderr — stdout bleibt sauber für Pipes/jq. Bei --json (rein
    # maschinenlesbare Ausgabe) wird das Banner ganz unterdrückt.
    if not getattr(args, "json", False):
        print_banner(Console(stderr=True))

    args.func(args)


if __name__ == "__main__":
    main()
