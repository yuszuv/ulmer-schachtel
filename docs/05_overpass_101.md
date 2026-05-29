# Overpass 101

Kurze, praxisnahe Einführung in **Overpass** – die Abfragesprache, mit der dieses
Projekt seine Bahndaten aus OpenStreetMap holt (`tools/fetch_cfr_data.py`). Ziel:
Du verstehst den vorhandenen Query und kannst ihn selbst anpassen.

## Worum geht's?

- **OpenStreetMap (OSM)** ist eine freie Weltkarte aus drei Bausteinen:
  **nodes** (Punkte, z. B. ein Bahnhof), **ways** (Linien/Flächen, z. B. ein
  Gleis), **relations** (Gruppen, z. B. eine Zuglinie). Jedes Objekt trägt
  **Tags** – Schlüssel-Wert-Paare wie `railway=station` oder `name=Cluj Napoca`.
- **Overpass API** ist ein Lesezugriff auf diese Daten: Du schickst eine Abfrage,
  bekommst genau die Objekte zurück, die deinen Filtern entsprechen (statt den
  ganzen Planeten herunterzuladen).
- **overpass-turbo** (<https://overpass-turbo.eu>) ist die Spielwiese dazu:
  Abfrage links eintippen, *Ausführen*, Treffer rechts auf der Karte sehen.
  **Zum Entwickeln immer hier testen**, nicht im Skript.

## Der Query dieses Projekts, Zeile für Zeile

So sieht die Abfrage in `tools/fetch_cfr_data.py` aus:

```overpassql
[out:json][timeout:120];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
node["railway"~"^(station|halt|stop)$"]["name"](area.ro);
out tags center;
```

1. **`[out:json][timeout:120];`** – *Einstellungen* für die ganze Abfrage:
   Ergebnis als JSON, Abbruch nach 120 s. (Jede Anweisung endet mit `;`.)
2. **`area["ISO3166-1"="RO"][admin_level=2]->.ro;`** – sucht die Staatsfläche
   Rumäniens (ISO-Code `RO`, Verwaltungsebene 2 = Land) und legt sie unter dem
   Namen **`.ro`** ab. So eine benannte Ablage heißt *Set* und lässt sich später
   als Filter wiederverwenden.
3. **`node["railway"~"^(station|halt|stop)$"]["name"](area.ro);`** – die
   eigentliche Auswahl:
   - `node` → nur Punkte.
   - `["railway"~"^(station|halt|stop)$"]` → Tag `railway` muss (per **Regex**,
     erkennbar am `~`) genau `station`, `halt` **oder** `stop` sein. `^…$`
     verankert den ganzen Wert, damit z. B. `crossing` nicht durchrutscht.
   - `["name"]` → nur Objekte, die **überhaupt** ein `name`-Tag haben
     (ohne Wertangabe = „Schlüssel existiert").
   - `(area.ro)` → räumlich auf das vorhin abgelegte Set `.ro` einschränken.
4. **`out tags center;`** – *Ausgabe*: gib die **Tags** aus und für jedes Objekt
   einen repräsentativen Mittelpunkt (`center`) als Koordinate.

Ergebnis: alle benannten Bahn-Haltepunkte Rumäniens – die Rohbasis, aus der das
Skript anschließend die CFR-Magistralen und ihre Stationen zusammensetzt.

## Filter-Bausteine, die du brauchst

| Schreibweise | Bedeutung |
|---|---|
| `["railway"="station"]` | Tag exakt gleich `station` |
| `["name"]` | Tag `name` existiert (beliebiger Wert) |
| `["railway"~"halt\|stop"]` | Regex: enthält `halt` oder `stop` |
| `["name"~"cluj",i]` | Regex, `i` = Groß/Kleinschreibung egal |
| `["railway"!~"."]` | Tag `railway` fehlt (Negation) |
| `node`, `way`, `relation`, `nwr` | Objekttyp (`nwr` = alle drei) |
| `(46.6,23.4,46.9,23.7)` | Bounding-Box (Süd, West, Nord, Ost) |
| `(area.ro)` | innerhalb eines benannten Sets |

## Nützliche Varianten zum Ausprobieren

Nur **zählen**, wie viele Stationen es gibt (schnell, ohne Geometrie):

```overpassql
[out:json][timeout:60];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
node["railway"="station"]["name"](area.ro);
out count;
```

Ein einzelner Bahnhof per **Bounding-Box** (z. B. Cluj):

```overpassql
[out:json];
node["railway"="station"]["name"="Cluj Napoca"](46.6,23.4,46.9,23.7);
out center;
```

Strecken statt Stationen – **Zuglinien-Relationen** im Land:

```overpassql
[out:json][timeout:120];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
relation["route"="train"](area.ro);
out tags;
```

## Etikette & Stolpersteine

- **Last-Limit:** Die öffentliche Instanz ist geteilt. Großzügige `timeout`-Werte
  setzen, nicht in Schleife hämmern, Ergebnisse cachen. Das Skript tut genau das
  (`data/raw/osm_ro_stations.json`, danach `--offline`).
- **User-Agent:** Bei direktem Abruf (nicht über overpass-turbo) einen
  aussagekräftigen `User-Agent` mitschicken – sonst kommt teils `HTTP 429/403`.
  Das Skript setzt einen.
- **Namen & Diakritika:** OSM-Schreibweisen variieren (`Cluj Napoca` vs.
  `Cluj-Napoca`, Bahnhof als `station` *oder* `halt`/`stop`). Genau deshalb
  zieht das Skript einen breiten Rohdatensatz und matcht lokal.
- **Lizenz:** OSM-Daten stehen unter **ODbL** – bei Weitergabe Namensnennung
  („© OpenStreetMap-Mitwirkende") beilegen. Siehe README, Abschnitt
  *Datenquellen & Lizenz*.

## Weiterlesen

- overpass-turbo (interaktiv): <https://overpass-turbo.eu>
- Overpass-QL-Referenz: <https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL>
- OSM-Tag `railway`: <https://wiki.openstreetmap.org/wiki/Key:railway>
