"""ASCII-Banner für die CLI.

Erzeugt mit ``figlet -f small "Ulmer Schachtel"`` und hier als Literal
eingebettet — keine Laufzeit-Abhängigkeit auf figlet/pyfiglet, deterministische
Ausgabe. Gerendert über ``rich`` in der Sepia-Palette des Projekts (vgl.
``qgis/styles/README.md``).

Platzierung (siehe ``cli.py``):
  • nackter Aufruf (kein Subcommand) → Banner + Hilfe nach stdout
  • normaler Befehl → Banner nach **stderr**, damit stdout für Pipes sauber bleibt
  • ``--json`` → Banner wird ganz unterdrückt (maschinenlesbare Ausgabe)
"""

from __future__ import annotations

from rich.console import Console

# figlet -f contessa "Ulmer Schachtel"  (Breite 60 — passt in 80-Spalten-Terminals)
_ART = r"""
.  ..              __.   .        .   ,    .
|  ||._ _  _ ._.  (__  _.|_  _. _.|_ -+- _ |
|__||[ | )(/,[    .__)(_.[ )(_](_.[ ) | (/,|
"""

_SUBTITLE = "Rumänien-Reiseplaner · CFR-Magistralen M200–M900 · QGIS → QField"

def print_banner(console: Console | None = None) -> None:
    """Render the ASCII banner in the project's sepia palette.

    ``console`` lets the caller route output to stderr (``Console(stderr=True)``)
    so the banner never contaminates a piped stdout.
    """
    console = console or Console()
    console.print(_ART.strip("\n"), style="bold #b5651d")  # amber/sepia
    console.print("\n")
    console.print(_SUBTITLE, style="#6b4f2a", highlight=False)
    console.print()
