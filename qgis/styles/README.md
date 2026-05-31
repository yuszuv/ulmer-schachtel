# QGIS Styles – Ulmer Schachtel

Dieses Verzeichnis enthält die Symbologie-Dateien (`.qml`) für die
eigenen Vektor-Layer des Projekts, plus die SVG-Quell-Icons.

## Überblick

| Datei | Layer | Verwaltet durch |
|---|---|---|
| `poi_destinations.qml` | Reiseziele (POIs) | Generator (s.u.) |
| `rail_stations.qml` | Bahnhöfe | Generator (s.u.) |
| `rail_lines.qml` | Strecken / Magistralen | Handgepflegt |
| `rail_gaps.qml` | Ungeroutete Streckenlücken („Ghost") | Handgepflegt |
| `wikivoyage_cities.qml` | WikiVoyage-Städte | Handgepflegt |
| `info_markers.qml` | ℹ-Marker (Legende) | Handgepflegt |
| `grenzen.qml` | Historische Grenzen 1800 (AT-Ungarn/Regat) | Handgepflegt |
| `historische_regionen.qml` | Historische Regionen (~1900, 9 Bezirke) | Handgepflegt |
| `historische_staedte.qml` | Historische Städte (25 Städte, DE/HU/RO) | Handgepflegt |
| `icons/` | SVG-Quellen für POI + Bahnhof | Handgepflegt |
| `build_marker_styles.py` | Generator für die ersten zwei | — |

## Generierte vs. handgepflegte Styles

**Generiert** (`build_marker_styles.py`): `poi_destinations.qml` und
`rail_stations.qml`. Diese beiden nutzen SVG-Icons, die base64-direkt in die
QML eingebettet werden (→ keine Pfadabhängigkeit, QField-sicher). Nach jeder
Änderung an einem Icon neu ausführen:

```bash
python qgis/styles/build_marker_styles.py
```

Die erzeugten Dateien **nicht manuell bearbeiten** — Änderungen werden beim
nächsten Generieren überschrieben. Stattdessen `build_marker_styles.py` anpassen.

**Handgepflegt**: `rail_lines.qml` (zweischichtige Eisenbahn-Signatur) und
`info_markers.qml` (ℹ-Marker mit statischer Legende) — diese direkt bearbeiten.

## Warum SVGs base64-einbetten?

QField (auf dem Handy) kennt die lokale Verzeichnisstruktur des Desktops
nicht. Wenn ein Style einen SVG-Pfad wie `qgis/styles/icons/poi_city.svg`
enthält, ist dieser Icon auf dem Gerät nicht auffindbar → leerer Marker.

Durch Base64-Einbettung (`name="base64:…"`) ist der Icon direkt in der QML
gespeichert — keine externe Datei nötig, kein Pfad-Problem.

## Die „All Categories"-Falle

Beim Laden eines QML in QGIS erscheint eine Dropdown-Box. Wählst du nur
„Symbology", werden **Beschriftungen** (Labeling) und **Map Tips** nicht
geladen — auch wenn sie in der QML vorhanden sind.

**Immer „All Categories" wählen.**

## Map Tips

Map Tips sind HTML-Karten, die in QGIS und QField beim Antippen eines Features
erscheinen (Identify-Werkzeug / Finger-Tap). Alle vier Layer haben einen Map
Tip:

| Layer | Inhalt |
|---|---|
| `poi_destinations` | Name, Kategorie, Priorität, Notizen |
| `rail_stations` | Bahnhofsname, Stadt |
| `rail_lines` | Strecke, Abfahrt/Ankunft, Zug, Via, Tage |
| `info_markers` | Titel + Freitext (Legende / Nutzungshinweise) |

Syntax im HTML: `[% "feldname" %]` — QGIS ersetzt das beim Anzeigen durch den
Attributwert. Leere Felder bei `rail_lines` zeigen „–" dank `coalesce()`.

## Maßstabsabhängige Sichtbarkeit

Alle vier QML tragen seit der Maßstabs-Überarbeitung **Label-Maßstabsgrenzen**
(`scaleVisibility="1"` + `scaleMax`), damit Beschriftungen bei Weitzoom nicht
zu einem Cluster verschmelzen:

| Layer | Labels ab |
|---|---|
| `poi_destinations` | 1:3 000 000 |
| `rail_stations` | 1:1 500 000 |
| `rail_lines` (M-Codes) | 1:6 000 000 |
| `info_markers` (ℹ) | 1:8 000 000 |
| `grenzen` (Ländernamen) | 1:2 000 000 … 1:15 000 000 |

`poi_destinations` nutzt zusätzlich einen **RuleRenderer**: pro Kategorie eine
Regel mit `scalemaxdenom`, sodass wichtige POIs (Dracula-/Großstädte, ab 1:6 Mio)
früher erscheinen als sekundäre (Donaudelta, ab 1:3 Mio).

`grenzen` ist ebenfalls **RuleRenderer**, aber narrativ statt nach Maßstab: drei
Regeln (Österreich-Ungarn getönt · Königreich Rumänien getönt · Balkan-Nachbarn
gestrichelt). Die Geometrie ist per **Layer-Maßstab** auf 1:800k … 1:20 Mio
begrenzt, die Labels zusätzlich auf 1:2 Mio … 1:15 Mio.

Die **Layer-Maßstäbe** (Marker-Geometrie von `rail_stations`/`info_markers` aus-
blenden, Grenzen-Band) und die **Basemap-Bänder** sind keine QML-Kategorie, sondern
Projekt-Eigenschaften — sie werden von `tools/qgis_setup_scales.py` gesetzt. Details:
[docs/01_qgis_setup.md](../../docs/01_qgis_setup.md#helper-scripts-python-console).

## Styles in das Projekt einbetten

Styles reisen **nicht als separate Dateien** nach QField — sie müssen ins
`.qgz` eingebettet sein. Das passiert automatisch beim Speichern des Projekts
in QGIS, aber erst **nachdem** die Styles geladen wurden.

Workflow nach Änderungen:
1. `build_marker_styles.py` ausführen (falls generierte Styles betroffen).
2. In QGIS: Layer-Properties → Style → Load Style → **All Categories**.
3. Projekt speichern (`reiseplan.qgz`).
4. `build-qfield` ausführen → kopiert das aktualisierte `.qgz` ins QField-Paket.

## Farbpalette (muted sepia)

| Rolle | Hex | RGB |
|---|---|---|
| Karte Hintergrund | `#f3ecd5` | — |
| Routen-Linien (Label) | `#6b4f2a` | 107, 79, 42 |
| Bahnhofs-Label | `#344a5e` | 52, 73, 94 |
| ℹ-Marker | `#2f6b6b` | 47, 107, 107 |
| POI-Label | `#6b4f2a` | 107, 79, 42 |

POI-Kategorien: `dracula_city` dunkelrot/Kreis · `city` sepia/Quadrat ·
`danube_delta` türkis/Dreieck.

### Erweiterung: Story-Ebene „Grenzen 1800"

`grenzen.qml` erzählt die Reise-Story (Siebenbürgen = Österreich-Ungarn vs.
Königreich Rumänien) und braucht dafür einen Farb**kontrast**, den die Kern-Palette
nicht hergibt. Label-Text (`#6b4f2a`) und Halo (`#f3ecd5`) nutzen die Palette; die
getönten Flächen sind bewusste, sepia-verwandte Erweiterungen:

| Rolle | Hex | RGB |
|---|---|---|
| AT-Ungarn Füllung | `#c8a96e` @ 30 % | 200, 169, 110 |
| AT-Ungarn Outline | `#6b4f2a` | 107, 79, 42 *(Palette)* |
| Rumänien Füllung | `#8faf7a` @ 30 % | 143, 175, 122 |
| Rumänien Outline | `#4a6b35` | 74, 107, 53 |
| Nachbarn Outline (dash) | `#9c7a5a` | 156, 122, 90 |

Das Rumänien-Grün ist Absicht (historische Atlas-Konvention AT-Ungarn-Gelb vs.
Rumänien-Grün) — die einzige Nicht-Sepia-Farbe und nur dieser Story-Ebene vorbehalten.
