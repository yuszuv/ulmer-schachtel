# QField Export (Basic v1)

Es gibt zwei Wege aufs Gerät:

- **Variante A – GPKG direkt kopieren:** Für die überwiegend **lesende** Nutzung
  (Marker und Routen ansehen). Kein Plugin nötig, nur zwei Dateien kopieren.
- **Variante B – alles über QFieldSync:** Das Plugin übernimmt den kompletten
  Export inkl. selbst gerenderter **Offline-Basemap**. Nötig für Offline-Karten
  ohne manuelles Kacheln-Besorgen sowie fürs **Bearbeiten + Zurücksynchronisieren**
  im Feld.

Wer nur lesen will und die Hintergrundkarte nicht offline braucht, nimmt
Variante A.

## Variante A (empfohlen): GPKG direkt kopieren

QField öffnet `.qgz`-Projekte nativ – kein Paketier-Schritt, keine
Verschachtelung, nur zwei Dateien.

### Voraussetzung

- Daten-Bündel gebaut: `uv run reiseplan-cli build-gpkg`
  → `data/processed/reiseplan.gpkg` (alle vier Layer in einer Datei).
- Projekt in QGIS aus dieser GPKG aufgebaut und als `.qgz` gespeichert
  (siehe [01_qgis_setup.md](01_qgis_setup.md)).
- Beim Speichern **relative Pfade** verwenden
  (Projekt → Eigenschaften → *Allgemein* → Pfade „relativ").
  Stile (Symbologie + Labels) werden dabei automatisch ins `.qgz` eingebettet –
  separate `.qml` musst du **nicht** mitkopieren.

### Ablauf

1. Diese beiden Dateien aufs Gerät übertragen (gleicher Ordner, damit der
   relative Pfad stimmt), z. B. via USB/MTP, Syncthing oder Cloud:
   - `qgis/projects/v1.qgz`
   - `data/processed/reiseplan.gpkg`
2. In QField den Ordner öffnen und das `.qgz` antippen.
3. Layer sichtbar schalten, Labels prüfen, Marker antippen
   (`name`, `category`, `notes`).
4. Optional: GNSS aktivieren, um die eigene Position zur Route zu sehen.

> Basemap: Basic v1 startet ohne Raster-Kacheln (spart Volumen). Optional später
> MBTiles offline erzeugen und mitkopieren.

## Doku in QField (Map-Tips & Info-Marker)

Die Doku reist **im Projekt** mit – keine separaten Dateien, kein Internet nötig.

- **Map-Tips:** Marker oder Routenlinie antippen → QField zeigt beim Identifizieren
  eine formatierte HTML-Karte (POI: Name, Kategorie, Priorität, Notiz; Station:
  Name + Stadt; Route: Name, Von → Nach, Tags). Das HTML steckt in den
  `qgis/styles/*.qml` (Kategorie *Map-Tips*) und wird beim `.qgz`-Speichern
  eingebettet – Voraussetzung ist, dass die Stile **mit allen Kategorien** geladen
  wurden (siehe [01_qgis_setup.md](01_qgis_setup.md), Schritt 5).
- **„Über diese Karte"-Marker:** der ℹ-Punkt (`info_markers`) etwa in der Landesmitte
  ist die Bedien-/Legenden-Hilfe – antippen zeigt Symbol-Erklärung, Bedienung und
  den Donaudelta-/Bahn-Hinweis.

> Auf dem Gerät einmal je einen POI-, Stations-, Routen- und den ℹ-Marker antippen
> und prüfen, dass die HTML-Karte erscheint. Falls nicht: Stile in QGIS neu „mit
> allen Kategorien" laden, `.qgz` neu speichern und erneut übertragen.

## Variante B: Alles über das QFieldSync-Plugin

Hier übernimmt das QFieldSync-Plugin den **kompletten** Weg aufs Gerät: Es bündelt
Projekt + Daten, rendert auf Wunsch eine **Offline-Basemap** und schnürt ein
in sich geschlossenes Paket. Sinnvoll, wenn du

- die Hintergrundkarte **offline** dabei haben willst (Plugin erzeugt MBTiles
  selbst – kein manuelles Kacheln-Besorgen),
- unterwegs **editieren und zurücksynchronisieren** willst, oder
- nur einen Teilausschnitt (Area of Interest) mitnehmen willst.

> ⚠️ **Zielordner außerhalb des Projektordners wählen** (z. B.
> `~/qfield_export/v1`). QFieldSync kopiert beim Paketieren alles
> Projektrelevante in den Zielordner – liegt dieser *im* Projektbaum, schluckt
> jeder Lauf den vorherigen Export (`qfield/qfield/qfield/…`).

### Schritt 1: Plugin installieren

*Erweiterungen → Erweiterungen verwalten und installieren → „QFieldSync" →
Installieren.*

### Schritt 2: Projekt konfigurieren

1. Projekt vorher **speichern** (sonst `AssertionError` – QFieldSync braucht einen
   `.qgz`/`.qgs`-Dateinamen).
2. `Plugins → QFieldSync → Configure Current Project` (Projekt konfigurieren).
3. Layer-Verhalten festlegen:
   - `poi_destinations`: `Offline editing` nur falls unterwegs Bearbeitung geplant,
     sonst `Copy`
   - `rail_stations` / `rail_route_options` / `info_markers`: `Copy`
     (read-only ausreichend)
   - XYZ-/Online-Hintergrundkarte: `Keep existing` (bleibt online) – oder per
     Offline-Basemap ersetzen (Schritt 3).

### Schritt 3 (optional): Offline-Basemap erzeugen lassen

So muss die Hintergrundkarte **nicht** von Hand als MBTiles besorgt werden –
QFieldSync rendert sie beim Paketieren selbst:

1. Im selben Konfigurationsdialog den Bereich **Base map** (Basiskarte) öffnen.
2. **Create base map** aktivieren.
3. Als Quelle das **Kartenthema** oder den Layer der gewünschten Hintergrundkarte
   wählen (z. B. die XYZ-OSM- oder CARTO-Karte aus
   [01_qgis_setup.md](01_qgis_setup.md)).
4. Detailgrad setzen:
   - **Map units per pixel**: kleiner = schärfer, aber größere Datei.
   - **Tile size**: Standard (meist 1024 px) genügt.
5. Ausdehnung auf das Reisegebiet begrenzen, damit das Paket klein bleibt.

> **Internet beim Export nötig:** QFieldSync lädt die Kacheln beim Paketieren aus
> der Online-Quelle. Auf dem Gerät selbst ist die Karte danach offline verfügbar.

### Schritt 4: Paketieren und übertragen

1. `Plugins → QFieldSync → Package for QField`, Zielordner **außerhalb** des Repos
   (z. B. `~/qfield_export/v1`).
2. Paket bauen lassen – es enthält Projekt, alle Layer und ggf. die Offline-Basemap.
3. Den **gesamten Zielordner** aufs Gerät übertragen (USB/MTP, Syncthing, Cloud)
   und in QField öffnen.
4. Bei aktiviertem `Offline editing`: Änderungen später über
   `Plugins → QFieldSync → Synchronize` zurückspielen.

## Typische Stolpersteine

- Fehlende Symbole:
  - Stile im Projekt anwenden und `.qgz` neu speichern – sie reisen im Projekt mit.
- Layer nicht sichtbar:
  - Maßstabsabhängigkeiten in Layer-Eigenschaften prüfen.
- Umlaute / Diakritika:
  - Dateicodierung UTF-8 belassen.
- `AssertionError` beim QFieldSync-Export:
  - Projekt war nicht gespeichert → erst als `.qgz` speichern (siehe Variante B, Schritt 2).
