# CLI-Option (oder "CL-Interface")

## Kurzfazit

Ja, eine CLI ist sinnvoll, aber als **Nebenwerkzeug**:

- schneller Datencheck ohne QGIS-UI
- einfache Filter (`Kategorie`, `Route`)
- kompakte Routenübersicht inkl. An-/Abfahrten (`overview`)
- guter Einstieg für spätere Automatisierung (Import/Validierung)

Für das Karten-Editing selbst bleibt QGIS das Hauptwerkzeug.

## Enthaltenes Tool

- Script: `tools/reiseplan_cli.py`
- Keine externen Python-Pakete nötig (nur Standardbibliothek)
- Ausführung über **uv** (`pyproject.toml` definiert den Entrypoint `reiseplan-cli`)

## Beispiele

```bash
uv run reiseplan-cli list-categories
uv run reiseplan-cli list-destinations --category dracula_city
uv run reiseplan-cli list-routes
uv run reiseplan-cli overview
uv run reiseplan-cli show-route R2
```

Ohne Installation des Entrypoints geht es auch direkt:

```bash
uv run python tools/reiseplan_cli.py overview
```

> Die CLI sucht `data/processed` ausgehend vom aktuellen Verzeichnis aufwärts –
> am einfachsten also aus dem Repo-Wurzelverzeichnis aufrufen.

## Sinnvolle Erweiterungen (später)

- Import echter GTFS-Fahrpläne in `data/raw`
- Validierung, ob alle POIs einen naheliegenden Bahnhof haben
- Export einer "Tagesvorschlag"-Liste für QField-Formulare
