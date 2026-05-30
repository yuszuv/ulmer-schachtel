# Overpass 101

A short, practical introduction to **Overpass** — the query language used by
this project to fetch rail data from OpenStreetMap (`tools/fetch_cfr_data.py`).
Goal: understand the existing query and be able to adapt it yourself.

## Background

- **OpenStreetMap (OSM)** is a free world map built from three primitives:
  **nodes** (points, e.g. a station), **ways** (lines/areas, e.g. a track),
  **relations** (groups, e.g. a train route). Every object carries **tags** —
  key-value pairs like `railway=station` or `name=Cluj Napoca`.
- **Overpass API** is a read interface for this data: send a query, get back
  exactly the objects matching your filters (instead of downloading the whole
  planet).
- **overpass-turbo** (<https://overpass-turbo.eu>) is the interactive playground:
  type a query on the left, click *Run*, see results on the map on the right.
  **Always test here first**, not in the script.

## The project query, line by line

This is the query in `tools/fetch_cfr_data.py`:

```overpassql
[out:json][timeout:120];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
node["railway"~"^(station|halt|stop)$"]["name"](area.ro);
out tags center;
```

1. **`[out:json][timeout:120];`** — global settings: return JSON, abort after
   120 s. (Every statement ends with `;`.)
2. **`area["ISO3166-1"="RO"][admin_level=2]->.ro;`** — finds Romania's country
   polygon (ISO code `RO`, admin level 2 = country) and stores it under the name
   **`.ro`**. This named store is called a *set* and can be reused as a filter.
3. **`node["railway"~"^(station|halt|stop)$"]["name"](area.ro);`** — the actual
   selection:
   - `node` → points only.
   - `["railway"~"^(station|halt|stop)$"]` → the `railway` tag must match (via
     **regex**, indicated by `~`) exactly `station`, `halt`, **or** `stop`. `^…$`
     anchors the whole value so that e.g. `crossing` cannot slip through.
   - `["name"]` → only objects that **have** a `name` tag at all (no value
     specified = "key exists").
   - `(area.ro)` → spatially restrict to the previously stored set `.ro`.
4. **`out tags center;`** — output: return the **tags** and for each object a
   representative centroid (`center`) as coordinates.

Result: all named rail stops in Romania — the raw basis from which the script
assembles the CFR magistrale and their stations.

## Filter building blocks you need

| Syntax | Meaning |
|---|---|
| `["railway"="station"]` | tag exactly equals `station` |
| `["name"]` | tag `name` exists (any value) |
| `["railway"~"halt\|stop"]` | regex: contains `halt` or `stop` |
| `["name"~"cluj",i]` | regex, `i` = case-insensitive |
| `["railway"!~"."]` | tag `railway` is absent (negation) |
| `node`, `way`, `relation`, `nwr` | object type (`nwr` = all three) |
| `(46.6,23.4,46.9,23.7)` | bounding box (south, west, north, east) |
| `(area.ro)` | within a named set |

## Useful variants to try

Count only (fast, no geometry):

```overpassql
[out:json][timeout:60];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
node["railway"="station"]["name"](area.ro);
out count;
```

A single station by **bounding box** (e.g. Cluj):

```overpassql
[out:json];
node["railway"="station"]["name"="Cluj Napoca"](46.6,23.4,46.9,23.7);
out center;
```

Train line **relations** instead of stations:

```overpassql
[out:json][timeout:120];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
relation["route"="train"](area.ro);
out tags;
```

## Etiquette & pitfalls

- **Rate limit:** The public instance is shared. Set generous `timeout` values,
  don't hammer in a loop, cache results. The script does exactly this
  (`data/raw/osm_ro_stations.json`, then `--offline`).
- **User-Agent:** When fetching directly (not via overpass-turbo), send a
  meaningful `User-Agent` header — otherwise you may get `HTTP 429/403`. The
  script sets one.
- **Names & diacritics:** OSM spellings vary (`Cluj Napoca` vs. `Cluj-Napoca`,
  station as `station` *or* `halt`/`stop`). That is exactly why the script
  fetches a broad raw dataset and matches locally.
- **Licence:** OSM data is under **ODbL** — include attribution
  ("© OpenStreetMap contributors") when redistributing. See README,
  section *Data sources & licence*.

## Further reading

- overpass-turbo (interactive): <https://overpass-turbo.eu>
- Overpass QL reference: <https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL>
- OSM tag `railway`: <https://wiki.openstreetmap.org/wiki/Key:railway>
