# TYPOGRAFISCHER STYLEGUIDE: HISTORISCHE LANDKARTE

## 1. Hauptelemente (Überschriften & Titel)

Für zentrale Titel und prominente Regionsübergruppen.

* **Schriftart-Empfehlung:** `Century Schoolbook Bold`, `Times New Roman Bold` oder `Playfair Display Bold`
* **Groß-/Kleinschreibung:** Gemischt (Erster Buchstabe groß)
* **Zeichenabstand (GIMP: Laufweite):** Leicht erhöht (**+2** bis **+4**)
* **Stil:** Normal / Aufrecht
* **Anwendung:** Haupttitel ("Königreich Böhmen"), große Meeresnamen ("ADRIAT. MEER").

## 2. Territorien & Regionen (Flächenbeschriftung)

Diese Schrift zieht sich optisch über ganze Länder und liegt *hinter* den Städten.

* **Schriftart-Empfehlung:** `Garamond Italic`, `Baskerville Italic` oder `EB Garamond Italic`
* **Groß-/Kleinschreibung:** REINE VERSALIEN (NUR GROSSBUCHSTABEN)
* **Zeichenabstand (GIMP: Laufweite):** Extrem weit auseinandergezogen (**+25** bis **+40** oder mehr, je nach Platz)
* **Stil:** *Kursiv (Italic)*
* **Anwendung:** Großflächige Ländernamen ("BÖHMEN", "MÄHREN").

## 3. Hauptstädte & Urbane Zentren (Fokusbeschriftung)

Kompakte, fette Schrift, die wie ein Stempel über dem Stadtpunkt sitzt.

* **Schriftart-Empfehlung:** `Clarendon Blk BT`, `Century Expanded Bold` oder `Rockwell Bold`
* **Groß-/Kleinschreibung:** REINE VERSALIEN (NUR GROSSBUCHSTABEN)
* **Zeichenabstand (GIMP: Laufweite):** Sehr dicht (**0** bis maximal **+1**)
* **Stil:** Normal / Fett
* **Anwendung:** Wichtige Knotenpunkte und Großstädte ("WIEN", "PRAG").

## 4. Ortschaften & Dörfer (Detailbeschriftung)

Kleine, unaufdringliche Schrift ohne Schnörkel für die Masse an Datenpunkten.

* **Schriftart-Empfehlung:** `Futura Condensed Medium`, `Helvetica Neue Condensed` oder `Arial Narrow`
* **Groß-/Kleinschreibung:** Gemischt (Normaler Satz)
* **Zeichenabstand (GIMP: Laufweite):** Standard (**0** bis **-0.5**)
* **Stil:** Normal / Eng (Condensed)
* **Anwendung:** Kleinere Städte, Dörfer, Flüsse ("Třebíč", "Znojmo").

## 5. Koordinaten & Kartenrand

Technische, mathematische Beschriftungen.

* **Schriftart-Empfehlung:** `Franklin Gothic Medium`, `Univers` oder `Helvetica Regular`
* **Groß-/Kleinschreibung:** Versalien bei Buchstaben, reguläre Ziffern
* **Zeichenabstand (GIMP: Laufweite):** Standard (**0**)
* **Stil:** Normal / Aufrecht

---

## GIMP-Profi-Tipp für den "Druck-Look"

Reines digitales Schwarz (`#000000`) gab es im historischen Druck nicht.

1. Stelle deine Textfarbe auf das **Karten-Schwarz (`#1a1917`)** aus der Palette unten.
2. Setze die **Ebenen-Deckkraft** des Textes in GIMP auf ca. **92 % bis 95 %**.
3. Ändere den Ebenen-Modus von *Normal* auf **Multiplizieren**. Dadurch verschmilzt die Schrift perfekt mit den Papierstrukturen darunter.

---

## 6. Farben & Flächentöne

### 6.1 Papierton & Hintergrund

Der Hintergrund imitiert ein leicht gealtertes Druckpapier um 1895. Litografischer Druck dieser Epoche war nicht reinweiß — das Papier hatte einen warmen, leicht gelblichen Grundton, der durch Bedruckung noch wärmer wurde.

| Element | Hex | RGB | Bemerkung |
|---|---|---|---|
| Papier-Grundton | `#f5efe0` | 245, 239, 224 | Basis für alle Flächenfüllungen |
| Papier dunkel (Falte/Rand) | `#e8dfc8` | 232, 223, 200 | Nur für Drucklayout-Hintergrund |
| Karten-Schwarz | `#1a1917` | 26, 25, 23 | Für alle Linien, Punkte, Text |

**QGIS-Hinweis:** Den Papierton als unterste Kachel (Tile-Layer oder einfarbige Maske) im Drucklayout anlegen. Nicht als Projekthintergrundfarbe — diese bleibt transparent, damit man die Daten darunter sieht.

### 6.2 Territorialfarben (Politische Flächen)

Die Flächen im Zimmermann-Atlas sind nie satt ausgemalt, sondern als zarte Lasuren über dem Papiergrundton aufgetragen. Deckkraft in QGIS immer unter 50 %, eher 25–35 %. Die Farben im Scan zeigen deutlich:

| Territorium / Typ | Hex (Füllfarbe) | Deckkraft (QGIS) | Charakter |
|---|---|---|---|
| Böhmen (helles Kernland) | `#e8dfc0` | 20–25 % | Fast ungefärbt, leichter Beige-Stich |
| Mähren / Nebenland rosa | `#e8b8a8` | 25–30 % | Warmer Lachston, Drucksatz-Rosa |
| Schlesien (Randgebiet) | `#d4c87a` | 20–25 % | Leichter Gelbton, abgesetzte Provinz |
| Österreich / Fremdes Reich | `#c8d4a0` | 25–30 % | Helles Gelbgrün, klar abgegrenzt |
| Ungarn / Großreich Ost | `#d4b870` | 25–30 % | Warmes Ocker, Habsburg-Einheit |
| Neutrales / Außengebiet | `#d8d0c0` | 15–20 % | Graubeige, tritt zurück |

**QGIS-Umsetzung:**
- Füllung: Einfache Füllung (Simple Fill)
- Randlinie der Fläche: `Keine Randlinie` — die Grenzlinien kommen als separate Layer darüber
- Renderreihenfolge: Politische Flächen ganz unten, Grenzen darüber, alles andere obenauf
- Mischungsmodus (Blending): `Multiplizieren` — dann zeigt die Fläche die Papierstruktur durch

### 6.3 Gewässerfarben

Flüsse und Seen hatten im Druckatlas ein charakteristisches helles Blaugrün — kein reines Cyan, sondern ein gekühltes Türkis mit hohem Weißanteil:

| Element | Hex | Deckkraft | Bemerkung |
|---|---|---|---|
| Flusslinie (Hauptfluss) | `#7bbccc` | 100 % | Als Linie, Stärke je nach Rang |
| Flusslinie (Nebenfluss) | `#9ecfdb` | 100 % | Dünner, heller |
| See / Stehende Gewässer | `#a8d8e8` | 60–70 % | Leicht transparent, zeigt Ufer |
| Meer / Küstengewässer | `#b8e0e8` | 50 % | Noch heller, große Fläche |
| Flussname (Text) | `#3a7a8c` | 100 % | Dunkleres Blaugrün für Lesbarkeit |

**Kartografische Anmerkung:** Im Zimmermann-Atlas verlaufen Flüsse immer in der Linienstärke mit der Fließrichtung — an der Quelle haarfein (0,1 mm), an der Mündung auf bis zu 0,5 mm anschwellend. In QGIS lässt sich das mit einer datendefinierten Breite und einem Rang-Attribut abbilden.

### 6.4 Relief & Geländedarstellung

Der Zimmermann-Atlas nutzt keine Höhenraster, sondern eine Kombination aus:
1. Bodenkolorit (leichter Gelbbraunton in Hochlagen)
2. Schraffur (Böschungsschraffur, in der Vorlage gut sichtbar als feine Federzüge)

Für eine digitale Annäherung:

| Element | Hex | Deckkraft | Methode |
|---|---|---|---|
| Tiefland-Grundton | `#f5efe0` | Vollton | Papierfarbe = kein Auftrag |
| Mittelgebirge (200–600 m) | `#e8d8a8` | 30–40 % | Hillshade-Overlay |
| Hochgebirge (>600 m) | `#d4c080` | 40–50 % | Hillshade-Overlay |
| Schraffur-Simulation | `#8c7850` | 15–25 % | Nur bei Druck: Pattern-Overlay |

---

## 7. Grenzen & Linien

### Allgemeines Prinzip

Im Atlas-Scan sind vier klar unterscheidbare Grenzebenen sichtbar. Die Hierarchie folgt politischer Bedeutung, nicht kartografischer Willkür: Je mächtiger die Grenze, desto breiter und farbkräftiger die Linie.

### 7.1 Grenztypen im Detail

| Ebene | Typ | Farbe (Hex) | Linienstärke | Stil | QGIS Layer-Eigenschaften |
|---|---|---|---|---|---|
| **Staatsgrenze** (Reichsgrenze) | Durchgehend | `#c83228` | 0,6–0,8 mm | Solid, Außenlinie leicht aufgedickt | Einfache Linie, kein Abstand |
| **Landesgrenze** (Böhmen/Mähren) | Durchgehend | `#d46820` | 0,4–0,5 mm | Solid, etwas dünner als Staatsgrenze | Einfache Linie |
| **Bezirks-/Kreisgrenze** | Gestrichelt | `#7850a0` | 0,2–0,25 mm | Strich–Lücke = 2:1 | Gestrichelt: `4;2` (mm) |
| **Gemeindegemarkung** | Fein gepunktet | `#606060` | 0,1 mm | Punkt–Lücke = 1:3 | Gepunktet: `1;3` (mm) |

**QGIS-Umsetzung Staatsgrenze (Beispiel):**
- Symbol: Liniensymbol (Line Symbol)
- Symbol-Ebene 1 (unten): Einfache Linie, Breite `0,9 mm`, Farbe `#d46820`, Mischungsmodus Normal
- Symbol-Ebene 2 (oben): Einfache Linie, Breite `0,5 mm`, Farbe `#c83228`, Versatz `0 mm`
- Ergebnis: Farbiger Kern mit leichtem Lichtsaum — wie im Druckoriginal

**QGIS-Umsetzung Bezirksgrenze:**
- Strichmuster (Dash Pattern): Länge `3,0 mm`, Lücke `1,5 mm`
- Farbe: `#7850a0`
- Stärke: `0,22 mm`
- Linienende: Abgerundet (Round Cap)

### 7.2 Küsten- & Gewässerrand

Die Küstenlinie ist im Original keine eigene Linie, sondern der Übergang vom Land- zum Wasserflächenlayer. Trotzdem empfiehlt sich für den QGIS-Layer:

- Landfläche Außenrand (gegen Küste): `0,25 mm`, `#5a8090`, leicht blaugrau
- Keine separate Küstenlinie als Linienlayer anlegen — der Kontrast entsteht durch die Flächenfarben

---

## 8. Punkt-Symbole & Marker

### 8.1 Stadttyp-Hierarchie

Im Zimmermann-Atlas sind die Stadtmarker simpel und klar: ausgefüllte schwarze Kreise in drei Größen, für Hauptstädte ein zusätzlicher äußerer Ring.

| Stadttyp | Form | Außendurchmesser | Füllung | Rand | QGIS Symbol |
|---|---|---|---|---|---|
| **Hauptstadt** (Wien, Prag) | Kreis mit Ring | 4,0 mm (Ring: 6,0 mm) | `#1a1917` | 0,6 mm, `#1a1917` | Einfacher Marker + zweiter Kreis-Layer |
| **Provinzhauptstadt** (Brünn) | Ausgefüllter Kreis | 3,0 mm | `#1a1917` | kein | Einfacher Marker |
| **Kreisstadt / Großstadt** | Ausgefüllter Kreis | 2,0 mm | `#1a1917` | kein | Einfacher Marker |
| **Mittelstadt** | Ausgefüllter Kreis | 1,5 mm | `#1a1917` | kein | Einfacher Marker |
| **Kleinstadt / Markt** | Kleiner Kreis | 1,0 mm | `#1a1917` | kein | Einfacher Marker |
| **Dorf / Weiler** | Punkt | 0,6 mm | `#1a1917` | kein | Einfacher Marker |

**QGIS-Umsetzung Hauptstadt-Marker:**
- Symbol: Zwei übereinanderliegende Marker-Ebenen
- Ebene 1 (unten): Kreis, Größe `6,0 mm`, Füllung keine, Randlinie `0,6 mm`, Farbe `#1a1917`
- Ebene 2 (oben): Kreis, Größe `3,5 mm`, Füllung `#1a1917`, keine Randlinie
- Renderreihenfolge: Marker über allen Flächenlayern, unter Beschriftungen

**QGIS-Expression für datengetriebene Marker-Größe:**

```qgis-expression
CASE
  WHEN "population" > 500000 THEN 4.0
  WHEN "population" > 100000 THEN 3.0
  WHEN "population" > 50000  THEN 2.0
  WHEN "population" > 10000  THEN 1.5
  WHEN "population" > 2000   THEN 1.0
  ELSE 0.6
END
```

### 8.2 Sonstige Punkt-Symbole

| Symbol | Form | Größe | Farbe | Anwendung |
|---|---|---|---|---|
| Festung / Burg | Quadrat (45° gedreht) | 2,0 mm | `#1a1917` | Historische Festungen |
| Kloster | Kreuz | 2,0 mm | `#1a1917` | Bedeutende Klöster |
| Bergpass | Dreieck | 1,5 mm | `#5a4830` | Gebirgspässe |
| Hafen | Anker-Piktogramm | 2,5 mm | `#3a7a8c` | Küstenhäfen |

---

## 9. Infrastruktur-Symbole

### 9.1 Eisenbahnlinien

Eisenbahnen sind im Zimmermann-Atlas als dünne schwarze Linie mit kurzen, regelmäßigen Querstrichen dargestellt — das klassische "Bahnschwellen-Muster", das seit Mitte des 19. Jahrhunderts kartografisch einheitlich ist.

| Typ | Hauptlinie | Querstrich | Abstand | Farbe |
|---|---|---|---|---|
| **Hauptbahn** (Magistrale) | 0,3 mm | Länge 1,5 mm, Breite 0,3 mm | alle 2,0 mm | `#1a1917` |
| **Nebenbahn** | 0,2 mm | Länge 1,0 mm, Breite 0,2 mm | alle 2,5 mm | `#1a1917` |
| **Schmalspurbahn** | 0,15 mm, gestrichelt | ohne Querstrich | — | `#3a3830` |

**QGIS-Umsetzung Hauptbahn (Bahnschwellen-Linie):**

Das klassische Bahnschwellen-Symbol in QGIS braucht zwei Symbol-Ebenen:

- Symbol-Ebene 1 (Hauptlinie): Einfache Linie, Breite `0,25 mm`, Farbe `#1a1917`
- Symbol-Ebene 2 (Querstrich): Marker-Linie (Marker Line), Symbol = Einfache Linie (90° gedreht), Breite `0,25 mm`, Länge `1,5 mm`, Abstand (Interval) `2,0 mm`, Versatz `0 mm`, Rotation `90°`

Alternativ per QGIS-Linienmuster-Füllung (für erfahrene Nutzer):
- Linientyp: Gestricheltes Muster
- Muster: `0.25;1.75` (Strich: 0,25 mm, Lücke: 1,75 mm)
- Überlagert mit Querstrich-Marker alle 2 mm

### 9.2 Straßen

| Typ | Hex | Linienstärke | Stil | Bemerkung |
|---|---|---|---|---|
| **Heerstraße / Reichsstraße** | `#c87840` | 0,3 mm | Durchgehend | Warmes Orange-Braun, wie im Scan |
| **Landstraße** | `#b89060` | 0,2 mm | Durchgehend | Etwas blasser |
| **Fahrweg / Pfad** | `#9a7850` | 0,15 mm | Gestrichelt `2;1` | Nur bei großem Maßstab |

**Kartografische Anmerkung:** Der auffällige orange-braune Straßenton im Scan ist kein Zufall. Heerstraßen wurden in deutschen Atlanten dieser Epoche systematisch in Rostbraun/Orange gedruckt — das unterscheidet sie sowohl von Eisenbahnen (schwarz) als auch von Grenzen (rot/violett) und schafft eine dritte Farbebene ohne Verwechslungsgefahr.

### 9.3 Wasserwege & Fähren

| Typ | Hex | Linienstärke | Stil |
|---|---|---|---|
| Schiffbarer Kanal | `#7bbccc` | 0,3 mm | Durchgehend, breiter als Nebenfluss |
| Fähre | `#7bbccc` | 0,15 mm | Gestrichelt `1;1` |
| Brücke | `#1a1917` | 0,4 mm | Kurze Querlinie über Flusslinie |

---

## 10. Legende & Kartenrahmen

### 10.1 Legendenaufbau

Die Legende im Zimmermann-Atlas ist kompakt, ohne Schnörkel, in eine Ecke gesetzt — typischerweise oben rechts oder unten rechts. Sie hat einen dünnen Linienrahmen (kein Doppelrahmen, kein Schatten) und zeigt nur das Minimum an Erklärungen.

**Inhalt und Reihenfolge (historisch korrekt):**
1. Titel: "Erläuterungen" oder "Zeichenerklärung" — kursive Serifenschrift, ca. 8 pt
2. Grenzlinien (mit kurzen Linienbeispielen, ca. 15 mm lang)
3. Stadtmarker (punktförmige Beispiele mit Typbezeichnung)
4. Eisenbahn / Straße (Linienmuster-Beispiel)
5. Maßstab (als Strichskala, keine Zahl alleine)

**Legendenrahmen:**
- Randlinie: `0,3 mm`, `#1a1917`
- Innenabstand (Padding): 3–4 mm
- Hintergrundfarbe: `#f5efe0` (Papiergrundton), Deckkraft 90 %
- Kein Schatten, keine Abrundung

**QGIS Drucklayout (Print Layout):**
- Legende einfügen: Menü `Hinzufügen > Legende`
- Schriftart Legendentitel: Garamond Italic, 9 pt
- Schriftart Einträge: Garamond Regular, 8 pt
- Symbol-Breite: 15 mm, Symbol-Höhe: 4 mm
- Spaltenabstand: 4 mm
- Hintergrund aktivieren, Farbe `#f5efe0`

### 10.2 Maßstabsbalken

| Parameter | Wert |
|---|---|
| Stil | Einfacher Strichbalken (kein gefüllter Balken) |
| Segmente | 4–5 Segmente |
| Beschriftung | Nur Endwerte (z. B. "0" und "100 km") |
| Schrift | Franklin Gothic / Helvetica, 7 pt, `#1a1917` |
| Einheit | km (km, nicht Meilen) |
| Balkenlänge | 40–60 mm im Druck |

**QGIS Drucklayout:**
- `Hinzufügen > Maßstabsbalken`
- Stil: `Einfache Linie` (nicht Kastensystem)
- Farbe: `#1a1917`
- Schriftart: gleiche wie Koordinaten-Beschriftung (Abschnitt 5)

### 10.3 Kartenrahmen

Der Zimmermann-Atlas hat einen charakteristischen doppelten Rahmen: ein dünner Innenrahmen, ein etwas dickerer Außenrahmen, dazwischen ein schmaler weißer Streifen von ca. 1–1,5 mm.

| Element | Linienstärke | Farbe | Abstand |
|---|---|---|---|
| Innenrahmen | 0,25 mm | `#1a1917` | direkt an Kartenkante |
| Zwischenraum | — | `#f5efe0` | 1,5 mm breit |
| Außenrahmen | 0,6 mm | `#1a1917` | außen |

**QGIS Drucklayout:**
- Kartenrahmen-Eigenschaften: `Rahmen` aktivieren
- Für den Doppelrahmen: Zwei übereinanderliegende Rechteck-Elemente (`Hinzufügen > Form > Rechteck`) als Hilfsrahmen oder den Kartenrand per SVG-Vorlage einfügen

### 10.4 Koordinatengitter (Gradnetz)

| Parameter | Wert |
|---|---|
| Typ | Linien-Gitter (kein Kreuz-Gitter) |
| Intervall | 1° oder 30' Breite/Länge |
| Linienstärke | 0,1 mm |
| Linienfarbe | `#9a9080` (warmes Grau) |
| Randticklänge | 2 mm |
| Koordinatenschrift | Franklin Gothic, 7 pt, `#1a1917` |
| Format | Grad/Minuten: `15°30'` (nicht Dezimalgrad) |

**QGIS Drucklayout:**
- Karte auswählen > `Eigenschaften > Gitter`
- Typ: `Linien`
- CRS für Gitter: EPSG:4326 (geographische Koordinaten) — auch wenn Projekt-CRS anders ist
- Rahmenbeschriftung: `Alle Seiten`, Stil `Außen`

### 10.5 Nordpfeil

**Empfehlung: Keinen Nordpfeil verwenden.**

Das entspricht dem historischen Vorbild: Atlasblätter dieser Epoche hatten keinen Nordpfeil, weil sie stets genordet (Norden oben) und im Kontext eines Buchatlas eindeutig orientiert waren. Ein moderner Nordpfeil würde den historischen Charakter stören.

Wenn unbedingt gewünscht: Einfache Pfeilform ohne Zierrat, schwarz (`#1a1917`), klein (8–10 mm), in eine Ecke gesetzt — nie mitten auf der Karte.

---

## ZUSAMMENFASSUNG: Farb-Palette auf einen Blick

| Name | Hex | Verwendung |
|---|---|---|
| Karten-Schwarz | `#1a1917` | Alle Linien, Text, Marker |
| Papier-Grundton | `#f5efe0` | Hintergrund, Legende |
| Staatsgrenze Rot | `#c83228` | Reichsaußengrenze |
| Landesgrenze Orange | `#d46820` | Provinzgrenzen |
| Bezirksgrenze Violett | `#7850a0` | Kreise/Bezirke |
| Wasser Blaugrün | `#7bbccc` | Flüsse, Hauptgewässer |
| Wasser Hell | `#b8e0e8` | Seen, Meer |
| Straße Rostbraun | `#c87840` | Heerstraßen |
| Böhmen Beige | `#e8dfc0` | Territorialfläche |
| Mähren Rosa | `#e8b8a8` | Territorialfläche |
| Schlesien Gelb | `#d4c87a` | Territorialfläche |
| Österreich Grüngelb | `#c8d4a0` | Territorialfläche |

Die Zimmermann-Palette des Originals in QGIS-kompatibles GPalette-Format ist in der Datei `zimmermann.gpl` abgelegt (GIMP-Paletten-Format, importierbar in QGIS über `Einstellungen > Stilmanager`).
