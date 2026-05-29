# AGENTS.md – Ulmer Schachtel (Rumänien-Reiseplaner)

Leitfaden für KI-Agenten, die in diesem Repo arbeiten. Knapp halten, an den
bestehenden Konventionen orientieren.

## Was das ist

Eine „nette", dezent historisch anmutende Karten-Anwendung zur groben Planung
einer **Bahnreise durch Rumänien** (Dracula-Städte, Temeschburg, Bukarest,
Donaudelta). Hauptwerkzeug ist **QGIS**, Ziel ist der Export nach **QField**.
Eine kleine **uv-CLI** ergänzt die Datenarbeit. Sprache im Projekt: **Deutsch**.

Reifegrad: **Basic v1**. Die volle Vintage-Anmutung (historische Rasterkarte,
Kartusche, Typografie, Etappenplanung) ist bewusst auf eine spätere „Fancy"-Stufe
vertagt – festgehalten in `docs/STYLE_TODO_FANCY.md`.

## Datenfluss (wichtig)

```
data/processed/*.geojson   ── versionierte Quelle der Wahrheit (EPSG:4326)
        │  uv run reiseplan-cli build-gpkg  (nutzt ogr2ogr → EPSG:3844)
        ▼
data/processed/reiseplan.gpkg   ── generiert, GITIGNORIERT, Ein-Datei-Bündel
        ▼
QGIS-Projekt (qgis/projects/*.qgz)   ── Stile + Labels eingebettet
        ▼
QField (qzg + gpkg aufs Gerät kopieren)
```

- **GeoJSON sind die Quelle**, die GPKG ist ein reproduzierbares Build-Artefakt.
  Inhaltliche Änderungen immer an den GeoJSON vornehmen, dann `build-gpkg`.
- `*.gpkg` ist in `.gitignore` – **nicht committen**.
- **Achtung:** Das Desktop-Projekt `qgis/reiseplan.qgz` lädt die GeoJSON **direkt**
  (relative Pfade `../data/processed/*.geojson`), **nicht** die GPKG. Wer eine
  GeoJSON umbenennt, muss den Pfad in der `.qgz` mitziehen (ZIP mit `reiseplan.qgs`).
  Die GPKG ist nur das Bündel für den QField-Export.
- **Verbindungen/Zeiten:** `data/processed/timetable.csv` ist eine **handgepflegte**
  Quelle (eine Zeile je Magistrale, echte Abfahrt/Ankunft/Tage/via). `fetch_cfr_data.py`
  legt sie nur als Vorlage an (falls fehlt) und merged ihre Felder beim Bauen als
  Attribute in `rail_lines.geojson` (Schlüssel: `route_id`). Eingetragene Zeiten
  werden nie überschrieben.

## Konventionen

- **CRS:** Daten liegen in `EPSG:4326` (GeoJSON-Standard). Projekt-/GPKG-CRS ist
  `EPSG:3844` (Stereo70, rumänische Nationalprojektion). Nicht durcheinander­bringen.
- **Zeichensatz:** echte UTF-8-Umlaute/Diakritika (Brașov, Timișoara, București) –
  keine ASCII-Transliteration (`Rumaenien`).
- **QGIS-Pfade:** Projekt mit **relativen** Pfaden speichern, damit `.qgz` + `.gpkg`
  zusammen aufs QField-Gerät kopierbar sind.
- **Stile:** `qgis/styles/*.qml` tragen Symbologie, **Labeling** (POIs 8pt bold
  sepia, Stationen 6.5pt grau) **und Map-Tips** (HTML-Karte beim Antippen,
  Style-Kategorie `MapTips`). Beim *Stil laden…* in QGIS alle Kategorien aktiviert
  lassen, sonst fehlen die Map-Tips. Beim Speichern des `.qgz` werden sie
  eingebettet – separate `.qml` müssen für QField nicht mitkopiert werden.
- **Farbwelt (dezent-sepia):** Hintergrund `#f3ecd5`, Routen `#6b4f2a` gestrichelt,
  Stationen `#4c4c4c`. POI-Kategorien: `dracula_city` dunkelrot/Kreis,
  `city` sepia/Quadrat, `danube_delta` petrol/Dreieck.

## CLI (`tools/reiseplan_cli.py`)

- **Nur Standardbibliothek** (argparse/csv/json + subprocess für `ogr2ogr`).
  Keine externen Python-Deps in `pyproject.toml` aufnehmen, ohne Grund.
- Ausführung über **uv**: `uv run reiseplan-cli <cmd>` (Entrypoint in `pyproject.toml`)
  oder `uv run python tools/reiseplan_cli.py <cmd>`.
- Datenverzeichnis wird via `find_data_dir()` vom CWD aufwärts gesucht → aus dem
  Repo-Wurzelverzeichnis aufrufen.
- Kommandos: `list-routes`, `list-categories`, `list-destinations [--category]`,
  `show-route <id>`, `overview`, `timetable`, `build-gpkg`.
- `build-gpkg` braucht **GDAL/ogr2ogr** im PATH (Arch: `pacman -S gdal`).

## Verifikation

```bash
uv run reiseplan-cli overview          # Magistralen + Haltefolge
uv run reiseplan-cli timetable         # Verbindungen (ab/an/via) je Magistrale
uv run reiseplan-cli list-routes       # M200–M900
uv run python -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('data/processed/*.geojson')]"
```

QGIS/QField-Schritte sind manuell – nicht automatisierbar. Vorgehen steht in
`docs/01_qgis_setup.md` (Aufbau) und `docs/02_qfield_export.md` (Export).

## Verzeichnisse

- `data/processed/` – GeoJSON (Quelle) + `route_stops.csv` (generierte Haltefolge je
  Magistrale) + `timetable.csv` (handgepflegte Verbindungen mit echten Zeiten).
  `info_markers.geojson` ist die in-App-Doku (ℹ „Über diese Karte", Bedien-/Legenden-Hilfe).
- `data/raw/` – Platzhalter für GTFS/OSM-Rohdaten
- `data/reference/historical/` – historisches Kartenmaterial (Fancy-Stufe)
- `qgis/styles/` – `.qml` (Symbologie + Labels + Map-Tips)
- `qgis/projects/` – `.qgz` (selbst in QGIS angelegt)
- `qgis/xyz_connections.xml` – vorbereitete XYZ-Basemaps (OSM, CARTO, OpenRailwayMap,
  Relief, Satellit, Arcanum historisch)
- `docs/` – `01_qgis_setup`, `02_qfield_export`, `03_cli_option`, `04_web_pages`,
  `05_overpass_101`, `06_cfr_daten_fetch`, `STYLE_TODO_FANCY`

## Git

- Conventional Commits (`feat:`/`fix:`/`chore:`), imperativ, ggf. Issue-Key.
- **Nie automatisch pushen** – nur auf ausdrückliche Aufforderung.
- Generierte Artefakte (`*.gpkg`, `qfield/`, `__pycache__/`, `.venv/`) bleiben
  ungetrackt (siehe `.gitignore`).

## Daten- und Reise-Annahmen

- Start-/Zielstadt sind bewusst offen → mehrere Routenoptionen (R1–R4) statt einer
  fixen Strecke.
- **Donaudelta ist nicht per Bahn erreichbar:** Schiene endet in Tulcea, weiter per
  Schiff. Diese Notiz in Daten/Doku nicht „wegoptimieren".
- `timetable.csv` enthält **echte**, handgepflegte Verbindungen (eine je Magistrale);
  noch nicht eingetragene Zeiten bleiben leer. Verbindliche/aktuelle Zeiten:
  <https://mersultrenurilor.infofer.ro>. `route_stops.csv` trägt **keine** Zeiten.
