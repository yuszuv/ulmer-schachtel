# Ulmer Schachtel – Reiseplaner Rumänien (QGIS → QField)

Basis für eine einfache, historisch anmutende Karten-Anwendung zur Urlaubsplanung mit Bahnstationen in Rumänien.

## Zielbild (Basic v1)

- Planung von Bahnstationen mit mehreren Routenoptionen.
- Marker für priorisierte Ziele:
  - Dracula-Städte: Brașov, Sighișoara
  - Städte: Timișoara (Temeschburg), București (Bukarest)
  - Donaudelta-Highlights: Sulina, Sfântu Gheorghe, Letea Forest
- Vorbereitung für späteren Export nach QField.

> Hinweis: Die Donaudelta-Highlights sind **nicht per Bahn** erreichbar. Die Schiene
> endet in Tulcea; ab dort geht es per Schiff/Tour ins Delta.

## Ordnerstruktur

- `data/raw`: Rohdaten (zukünftig z. B. GTFS, OSM-Exporte)
- `data/processed`: Verwendete Vektor- und Tabellendaten
- `data/reference/historical`: Referenzmaterial für historischen Kartenstil (Fancy-Stufe)
- `qgis/projects`: QGIS-Projektdateien (`.qgz`, selbst angelegt)
- `qgis/styles`: QGIS-Stildateien (`.qml`)
- `docs`: Arbeits- und Exportdokumentation
- `tools`: kleine Hilfsskripte/CLI

## Schnellstart (QGIS)

0. Daten-Bündel bauen: `uv run reiseplan-cli build-gpkg`
   (erzeugt `data/processed/reiseplan.gpkg` mit allen drei Layern; die GeoJSON
   bleiben das versionierte Quellformat).
1. QGIS öffnen (>= 3.28 empfohlen).
2. Neues Projekt anlegen und **zuerst** das Projekt-CRS setzen:
   *Projekt → Eigenschaften → KBS → `EPSG:3844 (Stereo70)`*.
   Wichtig: Das CRS **vor** dem Laden der Layer setzen. Sonst übernimmt
   QGIS das CRS des ersten Layers (`EPSG:4326`, das WGS84-/GPS-Format, in
   dem GeoJSON laut Standard immer vorliegt) als Projekt-CRS.
3. Layer aus `data/processed/reiseplan.gpkg` laden (3 Layer aus einer Datei):
   - `poi_destinations`
   - `rail_stations`
   - `rail_route_options`

   Die Layer liegen in `EPSG:4326` vor und werden von QGIS on-the-fly nach
   `EPSG:3844` projiziert — die Daten bleiben unverändert. Fragt QGIS, ob das
   Projekt-CRS auf das des Layers umgestellt werden soll: **ablehnen**.
4. Stile anwenden (Layer-Eigenschaften → Symbologie → *Stil laden…*):
   - `poi_destinations` → `qgis/styles/poi_destinations.qml`
   - `rail_route_options` → `qgis/styles/rail_route_options.qml`
   - `rail_stations` → `qgis/styles/rail_stations.qml`
5. Hintergrundkarte laden: *Web → QuickMapServices → OSM Standard* (Plugin nötig).
6. Labels kommen automatisch aus den QML-Dateien.
7. **Projekt speichern**: *Projekt → Speichern unter…* → `qgis/projects/v1.qgz`
   (Endung `.qgz` zwingend). Ohne gespeichertes Projekt schlägt der spätere
   QField-Export mit einem `AssertionError` fehl.

Details: siehe [docs/01_qgis_setup.md](docs/01_qgis_setup.md).

## Schnellstart (CLI, via uv)

```bash
uv run reiseplan-cli list-routes
uv run reiseplan-cli overview
uv run reiseplan-cli show-route R1
uv run reiseplan-cli list-destinations --category dracula_city
```

Alternativ ohne Installation:

```bash
uv run python tools/reiseplan_cli.py overview
```

## Weiterführung

- QGIS-Setup: [docs/01_qgis_setup.md](docs/01_qgis_setup.md)
- QField-Export: [docs/02_qfield_export.md](docs/02_qfield_export.md)
- CLI-Einschätzung: [docs/03_cli_option.md](docs/03_cli_option.md)
- Fancy-Stil-TODO: [docs/STYLE_TODO_FANCY.md](docs/STYLE_TODO_FANCY.md)
