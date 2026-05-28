# QGIS Setup (Basic v1)

## Ziel

Ein einfaches QGIS-Projekt mit:

- POIs (wichtige Ziele)
- Bahnstationen
- groben Routenkorridoren
- historisch anmutender Symbolik

## Schritte

1. QGIS starten und neues Projekt erstellen.
2. Projekt-CRS auf `EPSG:4326 (WGS 84)` setzen.
3. Daten laden:
- `data/processed/poi_destinations.geojson`
- `data/processed/rail_stations.geojson`
- `data/processed/rail_route_options.geojson`
4. Layer-Reihenfolge (oben nach unten):
- `poi_destinations`
- `rail_stations`
- `rail_route_options`
5. Stil laden:
- `poi_destinations`: `qgis/styles/poi_destinations.qml`
6. Labeling:
- POIs: Feld `name`
- Stations: Feld `name` in kleinerer Schrift
7. Projekt speichern unter:
- `qgis/projects/romania_reiseplaner_basic.qgz`

## Empfohlene Symbolik (wenn manuell gesetzt)

- Hintergrundfarbe Kartenfenster: warmes Off-White (`#f3ecd5`)
- Routenlinien: braun (`#6b4f2a`), 0.9 pt, gestrichelt
- Bahnhofsmarker: dunkelgrau (`#4c4c4c`), kleine Kreise
- POI-Kategorien:
- `dracula_city`: dunkelrot
- `city`: sepia-braun
- `danube_delta`: gedecktes petrolgruen
