# 07 – Code-Architektur: DDD + drei Patterns

Dieses Dokument erklärt die Designentscheidungen hinter dem Refactoring
der Python-Codebasis (v0.2.0, Mai 2026).

---

## Warum überhaupt refactoren?

Die fünf ursprünglichen Skripte unter `tools/` waren als schnelle Prototypen
entstanden und hatten keine Trennung der Verantwortlichkeiten:

| Datei | Zeilen | Probleme |
|---|---|---|
| `reiseplan_cli.py` | 461 | Daten laden + Rich-Tabellen + GPKG + QField + argparse |
| `fetch_cfr_data.py` | 497 | Liniendefinitionen + Netzwerk + Index + Ausgabe |
| `build_site.py` | 636 | ~330 Z. eingebetteter Template-String |
| `_paths.py`, `timetable.py` | 68 | Hilfsdateien ohne klares Zuhause |

Das Problem: Wenn man eine Funktion verstehen wollte, musste man den ganzen
Kontext einer 500-Zeilen-Datei im Kopf halten.

---

## Zielstruktur: Domain-Driven Design (DDD)

DDD organisiert Code um die **Domänensprache** (hier: rumänische Bahnen,
Reiseziele, Fahrpläne) statt um technische Schichten.

```
tools/reiseplan/
  paths.py       ← Pfad-Auflösung (kein Domänenwissen)
  result.py      ← Monaden (pure Fehlerbehandlung, kein IO)
  domain.py      ← Value Objects (reine Domänenobjekte, kein IO)
  catalog.py     ← Statische Liniendaten (reine Domänendaten)
  repository.py  ← Datenzugriff (GeoJSON/CSV)
  overpass.py    ← Externer Service-Gateway
  ingest.py      ← Use-Case (Orchestrierung)
  packaging.py   ← Infrastruktur (GPKG/QField-Build)
  tables.py      ← Präsentation (Rich Terminal)
  web.py         ← Präsentation (Website)
  template.html  ← Präsentation (HTML-Template)
  cli.py         ← Einstiegspunkt (argparse)
```

### Schichtenregel

Importe dürfen nur **nach innen** (zur Domäne hin) zeigen:

```
cli.py → tables.py, packaging.py  (Präsentation nutzt Domäne)
web.py → repository.py, domain.py
ingest.py → overpass.py, catalog.py, repository.py
overpass.py → domain.py, result.py
repository.py → domain.py, paths.py
domain.py → (nichts aus dem Paket)
result.py → (nichts aus dem Paket)
```

**Zirkuläre Imports sind verboten.** `cli.py` importiert `tables` und
`packaging`, aber `tables` importiert **nicht** `cli`.

---

## Pattern 1 – Command-Registry (Decorator)

**Problem:** `build_parser()` war ein langer Block, der für jeden Sub-Befehl
manuell `add_parser`, `add_argument` und `set_defaults` aufrief. Das fühlte sich
wie Konfiguration an, nicht wie Programmlogik.

**Lösung in `cli.py`:**

```python
# Infrastruktur:
REGISTRY: list[_CommandSpec] = []

def command(name, *, help, json=False, args=None):
    def decorator(fn):
        REGISTRY.append(_CommandSpec(name=name, help=help, ...))
        return fn
    return decorator

# Registrierung:
@command("list-routes", help="Alle Magistralen anzeigen", json=True)
def _list_routes(args):
    tables.list_routes(args)

# Parser-Aufbau aus der Registry:
def build_parser():
    for spec in REGISTRY:
        p = sub.add_parser(spec.name, ...)
        p.set_defaults(func=spec.handler)
```

**Lernpunkt:** Ein Decorator ist eine Funktion, die eine andere Funktion
*zurückgibt* und dabei Nebeneffekte haben darf (hier: in die Registry schreiben).
Der `@`-Syntax ist nur syntaktischer Zucker für `fn = command(...)(fn)`.

**Vorteile:**
- Neuen Befehl hinzufügen = eine dekorierte Funktion, null Boilerplate
- Die Registry ist zur Laufzeit inspizierbar (`tests/test_cli.py` nutzt das)
- Argument-Deklaration steht neben dem Handler, nicht 100 Zeilen weiter unten

---

## Pattern 2 – Result/Maybe-Monaden

**Problem:** Fehlerbehandlung war verstreut: `SystemExit` tief im `fetch_overpass()`-
Aufruf, `None` als Rückgabe aus `resolve()`. Callers wussten nicht, was sie
erwarten konnten.

**Lösung in `result.py`:**

```python
# Maybe: Wert der fehlen kann
some_coord = Some(Coordinate(26.07, 44.45))  # Bahnhof gefunden
no_coord   = Nothing                          # Bahnhof nicht in OSM

if some_coord.is_some:
    lon = some_coord.unwrap().lon

# Result: Operation die scheitern kann
data = load_or_fetch(offline=True)  # → Ok(dict) oder Err("Cache fehlt")
parsed = data.unwrap_or_exit()      # SystemExit bei Err, dict bei Ok
```

**Einsatzorte (bewusst sparsam):**

| Funktion | Rückgabetyp | Warum |
|---|---|---|
| `OverpassGateway.fetch()` | `Result[dict]` | Netzwerk-/JSON-Fehler sind erwartet |
| `StationIndex.resolve()` | `Maybe[Coordinate]` | Name nicht in OSM = normales Ergebnis |

**Lernpunkt:** Das Monad-Pattern sagt: *Fehler und Absenz sind Werte, keine
Ausnahmen.* `Nothing.map(fn)` ruft `fn` nicht auf und propagiert `Nothing`
— der Aufrufer muss explizit `.is_some` prüfen. Am Systemrand
(in `ingest.main()`) übersetzt `.unwrap_or_exit()` zurück in `SystemExit`.

**Warum nicht überall?** Für interne Fehler (fehlende Datei, falsche GPKG-Pfade)
ist `SystemExit` nach wie vor die richtige Wahl — laut scheitern ist besser als
stilles Halbfertig-Paket.

---

## Pattern 3 – Repository

**Problem:** `json.load`, `csv.DictReader` und Pfad-Konstanten lagen verstreut
über alle Dateien. `reiseplan_cli.py` kannte `POI_PATH`, `build_site.py` hatte
seine eigene Kopie von `STATIONS_PATH`, `fetch_cfr_data.py` hatte wieder andere.

**Lösung in `repository.py`:**

```python
# Alle Pfad-Konstanten an einem Ort:
POI_PATH       = PROCESSED / "poi_destinations.geojson"
ROUTES_PATH    = PROCESSED / "rail_lines.geojson"
TIMETABLE_PATH = PROCESSED / "timetable.csv"
...

# Datenzugriff als benannte Funktionen / Klasse:
def load_geojson(path: Path) -> dict: ...
def stops_for(route_id: str) -> list[dict]: ...

class TimetableRepository:
    def __init__(self, path: Path = TIMETABLE_PATH): ...
    def load(self) -> Timetable: ...     # gibt domain-Objekte zurück
    def scaffold(self, magistralen): ... # idempotent, überschreibt nie
```

**Lernpunkt:** Das Repository-Pattern kapselt *wie* Daten gespeichert werden
hinter einer domänensprachlichen API. Tests können eine andere `path`-Instanz
übergeben ohne echte Dateien zu brauchen (`TimetableRepository(tmp_path / "t.csv")`).

**Unterschied zu einem ORM-Repository:** Hier gibt es keine Datenbank, nur
Dateien — aber das Prinzip ist identisch: der Rest des Codes soll nicht wissen,
*ob* die Daten in einer CSV, einem JSON oder einer SQLite-Datei liegen.

---

## Umbenennung: `Line` → `Magistrale`

In DDD heißt das **Ubiquitous Language** (allgegenwärtige Sprache): die
gleichen Begriffe in Code, Docs und Gesprächen. `Line` war ein generischer
Python-Name. `Magistrale` ist der Begriff, der in der UI, in AGENTS.md und im
Projekt-README verwendet wird.

```python
# Vorher (fetch_cfr_data.py):
@dataclass(frozen=True)
class Line:
    ref: str
    ...

# Nachher (domain.py):
@dataclass(frozen=True)
class Magistrale:
    ref: str
    ...
```

Weitere Umbenennungen mit dem gleichen Motiv:
- `_rewrite_datasources` → `rewrite_datasources` (jetzt öffentlich + testbar)
- `build_index` → `StationIndex.from_overpass` (Objekt statt freie Funktion)
- `resolve` → `StationIndex.resolve` (Methode, nicht global)
- `b64` → `embed_svg` (was die Funktion tut, nicht wie)
- `map_tip` → `maptip_block` (Konventionsname der Funktion)
- `labeling` → `labeling_block`

---

## Template-Extraktion (`build_site.py` → `web.py` + `template.html`)

Der HTML/CSS/JS-Template-String (330 Zeilen) war in `build_site.py` eingebettet
und ließ die eigentliche Python-Logik (70 Zeilen) verschwinden.

Jetzt:
- `template.html` — reines Template, von Editoren als HTML erkennbar
- `web.py` — Python-Logik (`collect()`, `render()`, `build()`)

Ladeweg:
```python
HERE = Path(__file__).resolve().parent
template = (HERE / "template.html").read_text(encoding="utf-8")
html = template.format(bg=BG_COLOR, legend=..., data_js=...)
```

Die `{{`-Escapes im HTML (für CSS/JS-Klammern) bleiben erhalten — das ist
kein Bug sondern die `.format()`-Konvention. Ein `{bg}` im Template wird
ersetzt, ein `{{` wird zu einem literalen `{` in der Ausgabe.

---

## QML-Builder: `Marker`-Dataclass + `qml_document()`-Wrapper

In `build_marker_styles.py` war die POI-Icon-Tabelle ein `dict` mit Tupeln:

```python
# Vorher:
icons = {
    "0": ("dracula_city", "Dracula-Stadt", b64("poi_dracula.svg"), 7.5),
    ...
}
```

Jetzt ein `Marker`-Dataclass mit sprechenden Feldern:
```python
markers = [
    Marker("0", "dracula_city", "Dracula-Stadt", "poi_dracula.svg", 7.5),
    ...
]
```

Der gemeinsame `qml_document()`-Wrapper eliminiert die doppelte DOCTYPE/Header-
Struktur aus `build_poi()` und `build_stations()`.

**Wichtig:** Die **Ausgabe ist byte-gleich** zur vorherigen Version —
das war das Akzeptanzkriterium. Geprüft via `git diff qgis/styles/*.qml` nach
dem Ausführen des Skripts: kein Diff.

---

## Akzeptanzkriterien (alle erfüllt)

```bash
# 44 Tests grün:
uv run --group dev pytest

# Keine Datendiffs nach Offline-Rebuild:
uv run reiseplan-fetch --offline
git diff --stat data/processed/   # → leer

# Keine QML-Diffs nach Style-Rebuild:
python qgis/styles/build_marker_styles.py
git diff --stat qgis/styles/*.qml  # → leer

# CLI funktioniert:
uv run reiseplan-cli list-routes
uv run reiseplan-cli timetable --json | python3 -m json.tool

# Website baut:
uv run reiseplan-site --out /tmp/site
```
