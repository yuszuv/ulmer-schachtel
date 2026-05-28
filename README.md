# Reiseplaner Rumaenien (QGIS -> QField)

Basis fuer eine einfache, historisch anmutende Karten-Anwendung zur Urlaubsplanung mit Bahnstationen in Rumaenien.

## Zielbild (Basic v1)

- Planung von Bahnstationen mit mehreren Routenoptionen.
- Marker fuer priorisierte Ziele:
- Dracula-Staedte: Brasov, Sighisoara
- Staedte: Timisoara (Temeschburg), Bucuresti (Bukarest)
- Donaudelta-Highlights: Sulina, Sfantu Gheorghe, Letea Forest
- Vorbereitung fuer spaeteren Export nach QField.

## Ordnerstruktur

- `data/raw`: Rohdaten (zukuenftig z. B. GTFS, OSM-Exporte)
- `data/processed`: Verwendete Vektor- und Tabellendaten
- `data/reference/historical`: Referenzmaterial fuer historischen Kartenstil
- `qgis/projects`: QGIS-Projektdateien
- `qgis/styles`: QGIS-Stildateien (`.qml`)
- `docs`: Arbeits- und Exportdokumentation
- `tools`: kleine Hilfsskripte/CLI

## Schnellstart

1. QGIS oeffnen (>= 3.28 empfohlen).
2. Projekt neu anlegen, CRS auf `EPSG:4326`.
3. Layer laden:
- `data/processed/poi_destinations.geojson`
- `data/processed/rail_stations.geojson`
- `data/processed/rail_route_options.geojson`
4. Stil fuer POIs anwenden:
- Rechtsklick Layer `poi_destinations` -> `Eigenschaften` -> `Symbologie` -> `Stil laden...` -> `qgis/styles/poi_destinations.qml`.
5. Optional im Terminal:
- `python3 tools/reiseplan_cli.py list-routes`
- `python3 tools/reiseplan_cli.py show-route R1`

## Weiterfuehrung

- QGIS-Setup: [01_qgis_setup.md](/home/jan/137/spielwiese/reiseführer/docs/01_qgis_setup.md)
- QField-Export: [02_qfield_export.md](/home/jan/137/spielwiese/reiseführer/docs/02_qfield_export.md)
- CLI-Einschaetzung: [03_cli_option.md](/home/jan/137/spielwiese/reiseführer/docs/03_cli_option.md)
- Fancy-Stil-TODO: [STYLE_TODO_FANCY.md](/home/jan/137/spielwiese/reiseführer/docs/STYLE_TODO_FANCY.md)
