# Ulmer Schachtel – QGIS Setup (Basic v1)

## Ziel

Ein einfaches QGIS-Projekt mit:

- POIs (wichtige Ziele)
- Bahnstationen
- groben Routenkorridoren
- dezent historisch anmutender Symbolik (Pergament + Sepia)

## Schritte

1. QGIS starten und neues Projekt erstellen.
2. Projekt-CRS auf `EPSG:3844 (Stereo70)` setzen – offizielle rumänische Nationalprojektion, eliminiert die Verzerrung bei 4326. Die GeoJSON-Daten bleiben in 4326; QGIS reprojiziiert on-the-fly.
3. Daten laden – Bündel zuerst bauen (`uv run reiseplan-cli build-gpkg`),
   dann die vier Layer aus `data/processed/reiseplan.gpkg`:
   - `poi_destinations`
   - `rail_stations`
   - `rail_route_options`
   - `info_markers` (ℹ „Über diese Karte" – Bedien-/Legenden-Hilfe)
   (Die GeoJSON bleiben das versionierte Quellformat; die GPKG ist das
   generierte Ein-Datei-Bündel für QGIS/QField.)
4. Layer-Reihenfolge (oben nach unten):
   - `info_markers`
   - `poi_destinations`
   - `rail_stations`
   - `rail_route_options`
5. Stile laden (Layer-Eigenschaften → Symbologie → *Stil laden…*):
   - `poi_destinations` → `qgis/styles/poi_destinations.qml`
   - `rail_route_options` → `qgis/styles/rail_route_options.qml`
   - `rail_stations` → `qgis/styles/rail_stations.qml`
   - `info_markers` → `qgis/styles/info_markers.qml`
   > Beim *Stil laden…* **alle Kategorien** aktiviert lassen: Die `.qml` tragen
   > jetzt auch **Map-Tips** (Kategorie *Map-Tips*, HTML-Karte beim Antippen).
   > Lädst du nur „Symbologie", fehlen die Map-Tips. Für `info_markers` zusätzlich
   > das Anzeige-Feld auf `title` setzen (Layer-Eigenschaften → *Anzeige*).
6. Hintergrundkarte via **QuickMapServices**-Plugin:
   - Plugin installieren: *Erweiterungen → Erweiterungen verwalten → „QuickMapServices"*
   - Karte laden: *Web → QuickMapServices → OSM → OSM Standard* (oder Stamen Toner für historischeren Look)
   - QGIS reprojiziiert die Kacheln (EPSG:3857) automatisch auf Stereo70 – keine manuelle Anpassung nötig.
   - Projekt → Eigenschaften → *Allgemein* → Hintergrundfarbe `#f3ecd5` (greift wenn kein Tile-Layer aktiv).
   > Labels (POI-Namen 8pt bold sepia, Stationsnamen 6.5pt grau) sind bereits in den QML-Dateien eingebettet – kein manueller Schritt nötig.
   > Weitere sinnvolle Hintergrundkarten (Bahn-Overlay, Relief, Satellit, historisch)
   > als Ein-Klick-Import: siehe [Weitere Hintergrundkarten](#weitere-hintergrundkarten).
7. Projekt speichern unter:
   - `qgis/projects/ulmer_schachtel_basic.qgz`
   - Beim Speichern darauf achten, dass **relative Pfade** verwendet werden
     (Projekt → Eigenschaften → *Allgemein* → Pfade „relativ").
   - Die Stile werden dabei ins `.qgz` eingebettet – für QField genügt es,
     `.qgz` + `reiseplan.gpkg` zu kopieren (siehe [02_qfield_export.md](02_qfield_export.md)).

## Weitere Hintergrundkarten

Über OSM Standard hinaus sind je nach Zweck andere Basemaps sinnvoll. Alle sind
in `qgis/xyz_connections.xml` als XYZ-Verbindungen vorbereitet.

**Ein-Klick-Import:** Browser-Panel → Rechtsklick auf *XYZ Tiles* →
*Verbindungen laden…* → `qgis/xyz_connections.xml` wählen. Danach liegen alle
Karten unter *XYZ Tiles* und werden per Doppelklick als Layer geladen (unter die
eigenen Vektordaten legen).

| Karte | Zweck |
|---|---|
| **CARTO Positron / Voyager** | Helle, dezente Alltags-Basemap – ruhiger als OSM Standard, lässt die Sepia-Marker leuchten. |
| **OpenRailwayMap** | Bahn-Overlay (Strecken, Elektrifizierung, Bahnhöfe) – halbtransparent über die eigene Route legen, um Korridore gegen reale Strecken zu prüfen. |
| **OpenTopoMap / ESRI World Hillshade** | Gelände/Relief – erklärt die Trassenführung durch die Karpaten (Brașov, Sighișoara). |
| **ESRI World Imagery** | Satellit – gezielt fürs Donaudelta, wo die Wasserkanäle (Sulina, Sf. Gheorghe, Letea) das Eigentliche sind. |
| **Arcanum 2. Militäraufnahme** | Historische Grundkarte für die Fancy-Stufe (1806–1869). Braucht Referer-Header (in der XML hinterlegt). Details: [STYLE_TODO_FANCY.md](STYLE_TODO_FANCY.md). |

> **Offline/QField:** Alle Dienste brauchen eine Internetverbindung. Für die
> Reise selbst müssen die Kacheln des gewählten Hintergrunds als
> MBTiles/GeoPackage-Raster gecacht werden – sonst sind sie im Feld leer.

## Farbwelt (dezent-sepia, bereits in den QML)

- Hintergrund Kartenfenster: warmes Off-White `#f3ecd5`
- Routenlinien: Sepia-Braun `#6b4f2a`, ~0.9 pt, gestrichelt
- Bahnhofsmarker: dunkelgrau `#4c4c4c`, kleine Kreise
- POI-Kategorien:
  - `dracula_city`: dunkelrot (Kreis)
  - `city`: sepia-braun (Quadrat)
  - `danube_delta`: gedecktes Petrolgrün (Dreieck)

> Die volle historische Anmutung (Rasterkarte, Kartusche, Serifentypografie) folgt
> in der Fancy-Stufe – siehe [STYLE_TODO_FANCY.md](STYLE_TODO_FANCY.md).
