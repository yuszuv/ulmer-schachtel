# QField Export (Basic v1)

## Voraussetzung

- QGIS mit installiertem Plugin `QFieldSync`
- Projekt vorher sauber speichern (`.qgz`)
- Relative Pfade in den Layerquellen verwenden

## Exportablauf

1. In QGIS: `Plugins -> QFieldSync -> Package for QField`.
2. Zielordner setzen, z. B. `qfield/package_v1`.
3. Layer-Konfiguration im Dialog:
- `poi_destinations`: `Offline editing` nur falls unterwegs Bearbeitung geplant
- `rail_stations`: `Copy` (read-only ausreichend)
- `rail_route_options`: `Copy` (read-only ausreichend)
4. Basemap-Strategie:
- Basic v1: ohne Raster-Kacheln starten (spart Volumen)
- Optional spaeter: MBTiles offline erzeugen und mit exportieren
5. Paket bauen und auf Geraet uebertragen.

## Auf dem Smartphone (QField)

1. Projektordner in QField oeffnen.
2. Layer sichtbar schalten und Labels pruefen.
3. Marker antippen und Attribute checken (`name`, `category`, `notes`).
4. Optional: GNSS aktivieren, um Position zur Route zu sehen.

## Typische Stolpersteine

- Fehlende Symbole:
- `qml` nach dem Export erneut im Projekt speichern, dann neu paketieren.
- Layer nicht sichtbar:
- Maßstabsabhaengigkeiten in Layer-Eigenschaften pruefen.
- Umlaute:
- Dateicodierung UTF-8 belassen.
