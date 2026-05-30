```text
 _   _ _
| | | | |_ __  ___ _ _
| |_| | | '  \/ -_) '_|
 \___/|_|_|_|_\___|_|
 ___     _            _   _       _
/ __| __| |_  __ _ __| |_| |_ ___| |
\__ \/ _| ' \/ _` / _| ' \  _/ -_) |
|___/\__|_||_\__,_\__|_||_\__\___|_|

         |>>>
         |
   ______|__________________________
  / ___  ___  ___  ___  ___  ___     \
 | |_o_||_o_||_o_||_o_||_o_||_o_|     |
  \________________________________ _/
~~~~~~~~~~~~~~ Donau ~~~~~~~~~~~~~~~~~~~
```

# Ulmer Schachtel – Reiseplaner Rumänien (QGIS → QField)

> *Benannt nach der **»Ulmer Schachtel«** – dem einfachen hölzernen
> Donau-Flachboot, mit dem im 18./19. Jahrhundert Auswanderer von Ulm
> flussabwärts bis ins Banat (Rumänien) fuhren. Einbahn-Fahrt: am Ziel wurde
> das Boot zerlegt – das Holz diente den Siedlern zum Hausbau.*

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
   - `rail_lines` (Magistralen; tragen die Verbindungsdaten aus `timetable.csv` als Attribute)
   - `info_markers` (ℹ „Über diese Karte" – in-App-Hilfe)

   Die Layer liegen in `EPSG:4326` vor und werden von QGIS on-the-fly nach
   `EPSG:3844` projiziert — die Daten bleiben unverändert. Fragt QGIS, ob das
   Projekt-CRS auf das des Layers umgestellt werden soll: **ablehnen**.
4. Stile anwenden (Layer-Eigenschaften → Symbologie → *Stil laden…*, **alle Kategorien**):
   - `poi_destinations` → `qgis/styles/poi_destinations.qml`
   - `rail_lines` → `qgis/styles/rail_lines.qml`
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

Exakte Fahrplanzeiten stellt CFR nicht als offenen Feed bereit. `route_stops.csv`
enthält daher nur die **Haltefolge** je Magistrale (Reihenfolge + Rolle), keine
Zeiten. Echte Verbindungen (Abfahrt/Ankunft/Tage/via) werden **von Hand** in
`data/processed/timetable.csv` gepflegt — eine Zeile je Magistrale; das Fetch-Skript
legt diese Vorlage nur an, wenn sie fehlt, und überschreibt eingetragene Zeiten nie.
Beim nächsten `fetch …` wandern die Zeiten als Attribute in `rail_lines.geojson`
(Quelle für Zeiten: <https://mersultrenurilor.infofer.ro>). Übersicht per
`uv run reiseplan-cli timetable`.

Wie die Overpass-Abfrage funktioniert und wie du sie anpasst, erklärt
[docs/05_overpass_101.md](docs/05_overpass_101.md).

## Weiterführung

- QGIS-Setup: [docs/01_qgis_setup.md](docs/01_qgis_setup.md)
- QField-Export: [docs/02_qfield_export.md](docs/02_qfield_export.md)
- CLI-Einschätzung: [docs/03_cli_option.md](docs/03_cli_option.md)
- Online-Karte / GitHub Pages: [docs/04_web_pages.md](docs/04_web_pages.md)
- Overpass 101 (Bahndaten aus OSM): [docs/05_overpass_101.md](docs/05_overpass_101.md)
- CFR-Fetch-Prozess und Datenfluss: [docs/06_cfr_daten_fetch.md](docs/06_cfr_daten_fetch.md)
- Fancy-Stil-TODO: [docs/STYLE_TODO_FANCY.md](docs/STYLE_TODO_FANCY.md)
