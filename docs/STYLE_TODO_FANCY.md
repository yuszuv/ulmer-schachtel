# Ulmer Schachtel – TODO: Fancy Stil (historisch)

## Ziel für spätere Ausbaustufe

Ein visuell deutlich aufgewerteter Reiseplaner mit historischem Kartencharakter,
orientiert an spät-18.-Jahrhundert-Kartenästhetik.

## Stil-Referenz (festgehalten)

Referenzseite:
`https://www.vintage-maps.com/de/antike-landkarten/europa/rumaenien-moldawien/von-reilly-rumaenien-moldawien-temescher-banat-temeswar-timisoara::12254`

Wichtige Merkmale laut Seiteninhalt:

- Karte: „Das Temeschvarer Bannat."
- Kartograph: Franz Johann Joseph von Reilly
- Jahr: 1791 (Wien)
- Kontext: aus „Schauplatz der fünf Theile der Welt" (1789–1806)
- Anmutung: altkoloriert, warme Papierfarbigkeit, feine Beschriftung

## Historische Grundkarte: Arcanum Maps (XYZ Tiles)

**Arcanum Maps** (maps.arcanum.com) stellt die Habsburger Militäraufnahmen als
XYZ-Tile-Service bereit. Die `-transylvania`-spezifischen Layer liefern für
Rumänien leere Tiles — nur die `europe-*`-Layer haben tatsächliche Abdeckung.

Funktionierende Layer für Rumänien (getestet):

| Aufnahme | Zeitraum | Layer-Name |
|---|---|---|
| 1. Mil. Aufnahme | 1763–1790 | `europe-18century-firstsurvey` |
| 2. Mil. Aufnahme | 1806–1869 | `europe-19century-secondsurvey` |
| 3. Mil. Aufnahme | 1869–1887 | `europe-19century-thirdsurvey` |

Einbindung in QGIS (*Layer → Layer hinzufügen → XYZ-Tile-Layer*):

```
URL:     https://tiles.arcanum.com/mercator/europe-19century-secondsurvey/{z}/{x}/{y}
Referer: https://maps.arcanum.com
Min/Max Zoom: 5 / 14
```

Layer-Name anpassen für andere Epochen. Unter die eigenen Vektordaten legen.

> Zeitlich und geografisch perfekt zur Stil-Referenz (von Reilly 1791):
> die 1. Militäraufnahme entstand parallel im selben Jahrzehnt.

## Gestalterische TODOs

- Historische Grundkarte vorbereiten:
  - Arcanum WMS einbinden (siehe oben) statt lokaler Rasterdatei
  - Optional: Kacheln in `data/reference/historical` cachen für Offline-QField
- Farbwelt:
  - Pergament-Hintergrund, Sepia-Linien, gedeckte Akzentfarben
- Typografie:
  - Serifenschrift für Titel/Orte, dezente Sans für Metadaten
- Symbolik:
  - differenzierte Marker für `dracula_city`, `city`, `danube_delta`
- Routenvisualisierung:
  - wie historische Reiseachsen (punktiert/gestrichelt, nicht modern-neon)
- Kartenelemente:
  - Maßstab, Nordpfeil, dezente Kartusche mit Reiseroute

## Funktionale TODOs für "Fancy"

- Interaktive Etappenplanung (Tag 1..N)
- Gewichtung „Natur / Stadt / Historie"
- Export „Tagesplan" für QField-Formulare
- Optionaler Web-Viewer als zweite Oberfläche neben QGIS/QField
