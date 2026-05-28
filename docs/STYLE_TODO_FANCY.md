# TODO: Fancy Reiseplaner im historischen Stil

## Ziel fuer spaetere Ausbaustufe

Ein visuell deutlich aufgewerteter Reiseplaner mit historischem Kartencharakter, orientiert an spaet-18.-Jahrhundert-Kartenaesthetik.

## Stil-Referenz (festgehalten)

Referenzseite:
`https://www.vintage-maps.com/de/antike-landkarten/europa/rumaenien-moldawien/von-reilly-rumaenien-moldawien-temescher-banat-temeswar-timisoara::12254`

Wichtige Merkmale laut Seiteninhalt:

- Karte: "Das Temeschvarer Bannat."
- Kartograph: Franz Johann Joseph von Reilly
- Jahr: 1791 (Wien)
- Kontext: aus "Schauplatz der fuenf Theile der Welt" (1789-1806)
- Anmutung: altkoloriert, warme Papierfarbigkeit, feine Beschriftung

## Gestalterische TODOs

- Historische Grundkarte vorbereiten:
- georeferenzierte Rastergrundlage in `data/reference/historical`
- Farbwelt:
- Pergament-Hintergrund, Sepia-Linien, gedeckte Akzentfarben
- Typografie:
- Serifenschrift fuer Titel/Orte, dezente Sans fuer Metadaten
- Symbolik:
- differenzierte Marker fuer `dracula_city`, `city`, `danube_delta`
- Routenvisualisierung:
- wie historische Reiseachsen (punktiert/gestrichelt, nicht modern-neon)
- Kartenelemente:
- Maßstab, Nordpfeil, dezente Kartusche mit Reiseroute

## Funktionale TODOs fuer "Fancy"

- Interaktive Etappenplanung (Tag 1..N)
- Gewichtung "Natur / Stadt / Historie"
- Export "Tagesplan" fuer QField-Formulare
- Optionaler Web-Viewer als zweite Oberflaeche neben QGIS/QField
