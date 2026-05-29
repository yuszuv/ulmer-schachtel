# QField Export (Basic v1)

Für die überwiegend **lesende** Nutzung (Marker und Routen ansehen) brauchst du
QFieldSync nicht. Es reicht, das gespeicherte Projekt plus das Daten-Bündel
direkt aufs Gerät zu kopieren. QFieldSync ist erst nötig, wenn du **im Feld
bearbeiten und zurücksynchronisieren** willst.

## Variante A (empfohlen): GPKG direkt kopieren

QField öffnet `.qgz`-Projekte nativ – kein Paketier-Schritt, keine
Verschachtelung, nur zwei Dateien.

### Voraussetzung

- Daten-Bündel gebaut: `uv run reiseplan-cli build-gpkg`
  → `data/processed/reiseplan.gpkg` (alle drei Layer in einer Datei).
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

## Variante B: QFieldSync (nur für Feldbearbeitung)

Nur nötig für Offline-**Editieren mit Sync-zurück**, Area-of-Interest-Filter
oder Basemap→MBTiles-Konvertierung.

> ⚠️ **Zielordner außerhalb des Projektordners wählen** (z. B.
> `~/qfield_export/v1`). QFieldSync kopiert beim Paketieren alles
> Projektrelevante in den Zielordner – liegt dieser *im* Projektbaum, schluckt
> jeder Lauf den vorherigen Export (`qfield/qfield/qfield/…`).

1. Projekt vorher speichern (sonst `AssertionError` – QFieldSync braucht einen
   `.qgz`/`.qgs`-Dateinamen).
2. `Plugins → QFieldSync → Package for QField`, Zielordner **außerhalb** des Repos.
3. Layer-Konfiguration:
   - `poi_destinations`: `Offline editing` nur falls unterwegs Bearbeitung geplant
   - `rail_stations` / `rail_route_options`: `Copy` (read-only ausreichend)
4. Paket bauen und auf das Gerät übertragen.

## Typische Stolpersteine

- Fehlende Symbole:
  - Stile im Projekt anwenden und `.qgz` neu speichern – sie reisen im Projekt mit.
- Layer nicht sichtbar:
  - Maßstabsabhängigkeiten in Layer-Eigenschaften prüfen.
- Umlaute / Diakritika:
  - Dateicodierung UTF-8 belassen.
- `AssertionError` beim QFieldSync-Export:
  - Projekt war nicht gespeichert → erst als `.qgz` speichern (siehe Variante B, Schritt 1).
