# Online-Karte via GitHub Pages

Diese Anleitung beschreibt, wie die laienfreundliche Webseite gebaut und über
GitHub Pages veröffentlicht wird. Ziel: Wer kein QGIS hat, öffnet einfach eine
URL und sieht eine interaktive Karte plus eine lesbare Routen-/Ziel-Übersicht.

## Was wird angezeigt?

Die Seite (`tools/build_site.py` → `site/index.html`) ist **self-contained**:
die Daten sind direkt eingebettet, sie funktioniert daher auch lokal per
Doppelklick (`file://`). Inhalt:

- **Interaktive Karte** (Leaflet, OpenStreetMap-Hintergrund) mit ein-/
  ausschaltbaren Layern:
  - Routenkorridore (gestrichelte braune Linien) – Popup mit Strecke und Länge
  - Bahnstationen (graue Punkte)
  - Reiseziele (Form/Farbe je Kategorie: Dracula-Stadt = dunkelroter Kreis,
    Stadt = sepia Quadrat, Donaudelta = petrol Dreieck) – Popup mit Notizen
  - Info-Marker „Über diese Karte" – Legende und Hinweise
- **Routen-Übersicht** je Magistrale mit Halten/Hinweisen
- **Reiseziele** gruppiert nach Kategorie

Die Übersichtstexte werden server-seitig gerendert und sind auch ohne
JavaScript lesbar.

## Lokal bauen

```bash
python tools/build_site.py            # erzeugt ./site/index.html
python tools/build_site.py --out _out # alternatives Zielverzeichnis
```

Die Quelle bleibt das versionierte GeoJSON/CSV in `data/processed/`; `site/`
ist ein generiertes Artefakt und wird nicht eingecheckt (siehe `.gitignore`).

## Automatischer Deploy (GitHub Actions)

Workflow: `.github/workflows/pages.yml`

- Läuft bei jedem Push auf `main`, der Daten (`data/processed/**`) oder das
  Build-Skript ändert – sowie manuell (*Actions → Run workflow*).
- Baut die Seite und deployt sie nach GitHub Pages.

**Einmalige Aktivierung (manuell, nicht automatisierbar):**

1. Im GitHub-Repo: *Settings → Pages*.
2. Unter *Build and deployment → Source* **„GitHub Actions"** wählen.
3. Beim nächsten Push (oder manuellem Run) erscheint die öffentliche URL
   `https://<user>.github.io/<repo>/` im Workflow-Log und unter *Settings →
   Pages*.

## Bahndaten aktualisieren

Workflow: `.github/workflows/refresh-data.yml`

- Manuell auslösen (*Actions → „Bahndaten aktualisieren (Overpass)" → Run
  workflow*).
- Holt frische Daten von der Overpass-API (`tools/fetch_cfr_data.py`) und öffnet
  einen **Pull Request** mit dem Datendiff (Branch `data/overpass-refresh`).
- Nach dem Review/Merge baut `pages.yml` die Seite automatisch neu.

> Die Overpass-API kann langsam oder zeitweise nicht erreichbar sein. Deshalb
> läuft der Refresh bewusst nur auf Knopfdruck (ein wöchentlicher `cron` ist im
> Workflow als Vorlage auskommentiert).
