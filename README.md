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
- `qgis/reiseplan.qgz`: vorgefertigtes QGIS-Projekt (Layer + Stile)
- `qgis/projects`: Platz für eigene QGIS-Projektdateien (`.qgz`)
- `qgis/styles`: QGIS-Stildateien (`.qml`, inkl. eingebetteter SVG-Marker)
- `docs`: Arbeits- und Exportdokumentation
- `tools`: kleine Hilfsskripte/CLI (inkl. `build_site.py` für die Online-Karte)
- `.github/workflows`: GitHub Actions (Pages-Deploy, Daten-Refresh)

## Schnellstart (QGIS)

0. Daten-Bündel bauen: `uv run reiseplan-cli build-gpkg`
   (erzeugt `data/processed/reiseplan.gpkg` mit allen vier Layern; die GeoJSON
   bleiben das versionierte Quellformat).
1. QGIS öffnen (>= 3.28 empfohlen).
2. Neues Projekt anlegen und **zuerst** das Projekt-CRS setzen:
   *Projekt → Eigenschaften → KBS → `EPSG:3844 (Stereo70)`*.
   Wichtig: Das CRS **vor** dem Laden der Layer setzen. Sonst übernimmt
   QGIS das CRS des ersten Layers (`EPSG:4326`, das WGS84-/GPS-Format, in
   dem GeoJSON laut Standard immer vorliegt) als Projekt-CRS.
3. Layer aus `data/processed/reiseplan.gpkg` laden (4 Layer aus einer Datei):
   - `poi_destinations`
   - `rail_stations`
   - `rail_route_options`
   - `info_markers` (ℹ „Über diese Karte" – in-App-Hilfe)

   Die Layer liegen in `EPSG:4326` vor und werden von QGIS on-the-fly nach
   `EPSG:3844` projiziert — die Daten bleiben unverändert. Fragt QGIS, ob das
   Projekt-CRS auf das des Layers umgestellt werden soll: **ablehnen**.
4. Stile anwenden (Layer-Eigenschaften → Symbologie → *Stil laden…*, **alle Kategorien**):
   - `poi_destinations` → `qgis/styles/poi_destinations.qml`
   - `rail_route_options` → `qgis/styles/rail_route_options.qml`
   - `rail_stations` → `qgis/styles/rail_stations.qml`
   - `info_markers` → `qgis/styles/info_markers.qml`
5. Hintergrundkarte laden: *Web → QuickMapServices → OSM Standard* (Plugin nötig).
6. Labels **und Map-Tips** (HTML-Karte beim Antippen) kommen automatisch aus den QML-Dateien.
7. **Projekt speichern**: *Projekt → Speichern unter…* → `qgis/projects/v1.qgz`
   (Endung `.qgz` zwingend). Ohne gespeichertes Projekt schlägt der spätere
   QField-Export mit einem `AssertionError` fehl.

Details: siehe [docs/01_qgis_setup.md](docs/01_qgis_setup.md).

## Schnellstart (CLI, via uv)

```bash
uv run reiseplan-cli list-routes
uv run reiseplan-cli overview
uv run reiseplan-cli show-route M300
uv run reiseplan-cli list-destinations --category dracula_city
```

Alternativ ohne Installation:

```bash
uv run python tools/reiseplan_cli.py overview
```

## Online-Karte (GitHub Pages)

Für Technik-Laien gibt es eine **interaktive Webseite** mit Karte (Routen,
Bahnstationen, Reiseziele, Info-Marker) und einer lesbaren Routen- und
Ziel-Übersicht – ganz ohne QGIS. Einfach die Pages-URL öffnen:

> `https://<user>.github.io/<repo>/` (URL erscheint nach dem ersten Deploy
> in *Actions* bzw. *Settings → Pages*).

Lokal bauen und im Browser anschauen:

```bash
python tools/build_site.py        # erzeugt site/index.html (self-contained)
xdg-open site/index.html          # oder die Datei direkt im Browser öffnen
```

Die Seite wird automatisch via GitHub Actions gebaut und veröffentlicht
(Workflow `.github/workflows/pages.yml`), sobald sich Daten oder das Build-Skript
auf `main` ändern. **Einmalig nötig:** *Settings → Pages → Source = „GitHub
Actions"*. Frische Bahndaten lassen sich per Knopfdruck holen – Workflow
*„Bahndaten aktualisieren (Overpass)"* unter *Actions* ausführen; er öffnet einen
PR mit dem Datendiff. Details: [docs/04_web_pages.md](docs/04_web_pages.md).

## Datenquellen & Lizenz

Die Bahndaten (Bahnhöfe und Strecken) beruhen auf den **CFR-Magistralen 200–900**
(„Căile Ferate Române main lines") und werden aus **OpenStreetMap** via Overpass
API bezogen:

```bash
uv run python tools/fetch_cfr_data.py            # OSM abfragen, cachen, GeoJSON bauen
uv run python tools/fetch_cfr_data.py --offline  # nur aus data/raw-Cache neu bauen
```

> Kartendaten © **OpenStreetMap-Mitwirkende**, lizenziert unter der
> [Open Database License (ODbL)](https://www.openstreetmap.org/copyright).
> Bei Weitergabe der abgeleiteten Daten ist diese Namensnennung beizulegen.

Exakte Fahrplanzeiten stellt CFR nicht als offenen Feed bereit; die Spalten
`arrival_local`/`departure_local` in `sample_connections.csv` bleiben daher leer
(Quelle für Zeiten: <https://mersultrenurilor.infofer.ro>).

Wie die Overpass-Abfrage funktioniert und wie du sie anpasst, erklärt
[docs/05_overpass_101.md](docs/05_overpass_101.md).

## Weiterführung

- QGIS-Setup: [docs/01_qgis_setup.md](docs/01_qgis_setup.md)
- QField-Export: [docs/02_qfield_export.md](docs/02_qfield_export.md)
- CLI-Einschätzung: [docs/03_cli_option.md](docs/03_cli_option.md)
- Online-Karte / GitHub Pages: [docs/04_web_pages.md](docs/04_web_pages.md)
- Overpass 101 (Bahndaten aus OSM): [docs/05_overpass_101.md](docs/05_overpass_101.md)
- Fancy-Stil-TODO: [docs/STYLE_TODO_FANCY.md](docs/STYLE_TODO_FANCY.md)
