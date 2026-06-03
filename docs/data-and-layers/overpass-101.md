# Overpass 101

A practical introduction to **Overpass** — the query language this project uses
to fetch rail data from OpenStreetMap. Goal: understand the two existing queries
and be able to adapt them yourself.

## Background

**OpenStreetMap (OSM)** stores the world as three primitives:

| Primitive | What it is | Rail example |
|---|---|---|
| **Node** | A point in space | A station (`railway=station`) |
| **Way** | An ordered list of nodes | A track segment (`railway=rail`) |
| **Relation** | A group of the above | A train route (`route=train`) |

Every primitive carries **tags** — key-value pairs like `railway=station` or
`name=Cluj-Napoca`.

**Overpass API** is a read-only query interface for this data: send a query, get
back exactly the objects matching your filters (instead of downloading the whole
planet).

**overpass-turbo** (<https://overpass-turbo.eu>) is the interactive playground:
type a query on the left, click *Run*, see results on the map on the right.
Always test here before modifying the Python scripts.

---

## Query 1 — Station nodes (`uv run reiseplan-fetch`)

`tools/reiseplan/overpass.py` — constant `OVERPASS_QUERY`:

```overpassql
[out:json][timeout:120];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
node["railway"~"^(station|halt|stop)$"]["name"](area.ro);
out tags center;
```

Line by line:

1. **`[out:json][timeout:120];`** — global settings: return JSON, abort after
   120 s. Every statement ends with `;`.
2. **`area["ISO3166-1"="RO"][admin_level=2]->.ro;`** — finds Romania's country
   polygon (ISO code `RO`, `admin_level=2` = country boundary) and stores it in
   the named set **`.ro`** for reuse as a spatial filter.
3. **`node["railway"~"^(station|halt|stop)$"]["name"](area.ro);`**
   - `node` — points only.
   - `["railway"~"^(station|halt|stop)$"]` — the `railway` tag must match
     (`~` = regex) exactly `station`, `halt`, or `stop`. The `^…$` anchors
     prevent partial matches (e.g. `level_crossing` can't slip through).
   - `["name"]` — only objects that *have* a `name` tag (no value = "key
     exists"). Stops without a name are useless for matching.
   - `(area.ro)` — restrict spatially to the Romania set.
4. **`out tags center;`** — output the tags and a representative centroid
   coordinate for each node (`center` because some stations are mapped as
   ways/relations, not bare nodes — Overpass computes the centroid for those).

**Result:** all named rail stops in Romania → `data/raw/osm_ro_stations.json`.

---

## Query 2 — Rail track ways (`uv run reiseplan-fetch`)

`tools/reiseplan/overpass.py` — function `rail_ways_query(bbox)`:

```overpassql
[out:json][timeout:180];
way["railway"="rail"]["service"!~"."](south,west,north,east);
out geom;
```

This is called *once per magistrală* with the bounding box of that line's
stations (padded ~0.25°). Line by line:

1. **`way["railway"="rail"]`** — *ways* (track segments) tagged as mainline
   rail. Nodes are useless here; we want the actual line geometry.
2. **`["service"!~"."]`** — drop ways that *have* any `service` tag. The
   `service` tag on rail marks sidings, yards, and spurs. `!~"."` is the
   Overpass idiom for "tag is absent": the regex `.` matches any non-empty value,
   so negating it means the tag must not exist at all. Without this filter the
   router would happily take a detour through a marshalling yard.
3. **`(south,west,north,east)`** — bounding box, in degrees. The corridor is the
   station bbox of the magistrală plus a buffer so the curving real alignment is
   captured even where it strays beyond the straight station-to-station envelope.
4. **`out geom;`** — output each way's *full vertex list* (not just a centroid).
   This is what `RailNetwork.from_overpass()` expects: `way.geometry` =
   `[{lon, lat}, …]` gives the exact track shape.

**Result:** one Overpass JSON per magistrała → combined in
`data/raw/osm_ro_rail_ways.json`.

---

## Syntax reference

| Syntax | Meaning |
|---|---|
| `["key"="value"]` | tag exactly equals `value` |
| `["key"]` | tag `key` exists (any value) |
| `["key"!~"."]` | tag `key` is absent |
| `["key"~"a\|b"]` | regex: value contains `a` or `b` |
| `["key"~"^a$",i]` | regex, `i` = case-insensitive |
| `node` / `way` / `relation` / `nwr` | object type (`nwr` = all three) |
| `(S,W,N,E)` | bounding box (south, west, north, east, in degrees) |
| `(area.name)` | spatially within a named set |
| `out tags;` | properties only (no coordinates) |
| `out center;` | properties + centroid (for ways/relations) |
| `out geom;` | properties + **full** vertex list (for ways) |
| `out count;` | count only (fast sanity check) |

---

## Useful queries to try in overpass-turbo

**How many named stations are in Romania?** (fast count, no geometry)

```overpassql
[out:json][timeout:60];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
node["railway"="station"]["name"](area.ro);
out count;
```

**A single station by bounding box** (e.g. find Cluj-Napoca):

```overpassql
[out:json];
node["railway"="station"](46.6,23.4,46.9,23.7);
out tags center;
```

**The rail track around Sighișoara** (to visualise what Query 2 retrieves):

```overpassql
[out:json];
way["railway"="rail"]["service"!~"."](46.1,24.6,46.3,25.1);
out geom;
```

**Train route relations** (the OSM approach to modelling entire lines — the
project uses its own catalog instead because CFR ref tags are inconsistent):

```overpassql
[out:json][timeout:120];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
relation["route"="train"](area.ro);
out tags;
```

---

## Etiquette & pitfalls

- **Rate limit:** The public instance at `overpass-api.de` is shared. The
  project sets `timeout`, sends one query per corridor (not per station), and
  caches the result (`data/raw/osm_ro_*.json`) so subsequent runs use
  `--offline`. Don't add a loop without caching.
- **User-Agent:** Always include a meaningful `User-Agent` header when hitting
  Overpass directly from code (not via overpass-turbo) — otherwise the server
  may respond with `HTTP 429`. The project gateway sets one.
- **Names & diacritics:** OSM spellings are inconsistent (`Cluj Napoca` vs.
  `Cluj-Napoca`; station mapped as `station` *or* `halt`/`stop`). That is why
  Query 1 fetches the full Romania dataset and matches locally with aliases
  (`Stop.osm_names` in `catalog.py`), rather than querying by name.
- **`out geom` vs. `out center`:** `out center` is fine for station nodes
  (you only want one coordinate). For track geometry you *need* `out geom` —
  `out center` would collapse the whole way to a single point.
- **Licence:** OSM data is **ODbL**. Include `© OpenStreetMap contributors`
  whenever you redistribute derived data (GeoJSON, GPKG, website). See README
  → *Data sources & licence*.

---

## Further reading

- overpass-turbo (interactive): <https://overpass-turbo.eu>
- Overpass QL reference: <https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL>
- OSM tag `railway`: <https://wiki.openstreetmap.org/wiki/Key:railway>
- OSM tag `service` on railways: <https://wiki.openstreetmap.org/wiki/Key:service>
