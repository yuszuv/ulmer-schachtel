# CLI-Option (oder "CL-Interface")

## Kurzfazit

Ja, eine CLI ist sinnvoll, aber als Nebenwerkzeug:

- schneller Datencheck ohne QGIS-UI
- einfache Filter (`Kategorie`, `Route`)
- guter Einstieg fuer spaetere Automatisierung (Import/Validierung)

Fuer das Karten-Editing selbst bleibt QGIS das Hauptwerkzeug.

## Enthaltenes Tool

- Script: `tools/reiseplan_cli.py`
- Kein externes Python-Paket noetig

## Beispiele

```bash
python3 tools/reiseplan_cli.py list-categories
python3 tools/reiseplan_cli.py list-destinations --category dracula_city
python3 tools/reiseplan_cli.py list-routes
python3 tools/reiseplan_cli.py show-route R2
```

## Sinnvolle Erweiterungen (spaeter)

- Import echter GTFS-Fahrplaene in `data/raw`
- Validierung, ob alle POIs einen naheliegenden Bahnhof haben
- Export einer "Tagesvorschlag"-Liste fuer QField-Formulare
