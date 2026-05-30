# QGIS projects

> **Hinweis:** Das Projektverzeichnis `qgis/projects/` ist vestigial — die
> eigentliche Projektdatei liegt eine Ebene höher:
>
> `qgis/reiseplan.qgz`
>
> Dieses Verzeichnis kann ignoriert werden.

## Kurzreferenz

- Das Projekt wird **direkt in QGIS** geöffnet und gespeichert.
- Beim Speichern **relative Pfade** aktivieren:
  *Projekt → Eigenschaften → Allgemein → Pfade: relativ*
- Styles vor dem Speichern mit **All Categories** laden, damit Map Tips im
  `.qgz` eingebettet werden.
- Für den QField-Export: `uv run reiseplan-cli build-qfield`
  (baut `qfield/current/{reiseplan.qgz, reiseplan.gpkg}`)

Vollständige Anleitung: [../../docs/01_qgis_setup.md](../../docs/01_qgis_setup.md)
