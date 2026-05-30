# CFR Rail Data: Fetch Process and Data Flow

Technical reference for `tools/fetch_cfr_data.py` — the script that fetches
Romanian railway data (CFR magistrale 200–900) from OpenStreetMap and converts
it into project-ready GeoJSON/CSV files.

The query syntax itself is explained in [docs/05_overpass_101.md](05_overpass_101.md).

---

## Context: fetch process in the overall pipeline

`fetch_cfr_data.py` sits at the **start** of the data pipeline. The files it
produces are the versioned source that all downstream steps build on. Alongside
it, `timetable.csv` is a **hand-maintained** source for real connection data —
the fetch script reads it but never writes it.

```mermaid
flowchart LR
    OSM["OpenStreetMap\nOverpass API"]
    TT["data/processed/timetable.csv\n(hand-maintained, times entered by user)"]

    subgraph fetch ["1 · Fetch + merge"]
        FP["tools/fetch_cfr_data.py"]
    end

    subgraph raw ["data/raw/"]
        R1["osm_ro_stations.json\n(raw cache, gitignored)"]
    end

    subgraph processed ["data/processed/  (versioned)"]
        P1["rail_stations.geojson"]
        P2["rail_lines.geojson\n(+ timetable fields as attributes)"]
        P3["route_stops.csv\n(stop sequence per magistrală)"]
        P4["poi_destinations.geojson\n(manually maintained)"]
        P5["info_markers.geojson\n(manually maintained)"]
    end

    subgraph bundle ["2 · Bundle"]
        CLI["reiseplan-cli build-gpkg"]
        GPKG["data/processed/reiseplan.gpkg"]
    end

    subgraph consume ["3 · Consume"]
        QGIS["QGIS: qgis/reiseplan.qgz\n(loads GeoJSON directly!)"]
        QF["QField (on device)"]
        WEB["tools/build_site.py\n→ site/index.html"]
    end

    OSM --> FP
    TT -. "read-only" .-> FP
    FP --> R1
    FP --> P1 & P2 & P3
    P1 & P2 & P3 & P4 & P5 --> CLI
    CLI --> GPKG
    GPKG --> QF
    P1 & P2 & P3 & P4 & P5 --> QGIS
    P1 & P2 & P3 & P4 & P5 --> WEB
```

> **Note:** `qgis/reiseplan.qgz` loads GeoJSON **directly** via relative paths —
> it does **not** reference the GPKG. The GPKG is exclusively the bundle for
> QField export. If you rename a GeoJSON file, update the path in the `.qgz`
> (the file is a ZIP containing `reiseplan.qgs`).

---

## Fetch flow overview

```mermaid
flowchart TD
    A[["Invocation:\ntools/fetch_cfr_data.py"]] --> B{--offline?}

    B -- no --> C["Overpass API\nhttps://overpass-api.de/api/interpreter\nPOST, timeout 180 s"]
    C --> D["Save raw JSON\ndata/raw/osm_ro_stations.json"]
    B -- yes  --> E["Read raw cache\ndata/raw/osm_ro_stations.json"]
    D --> F
    E --> F

    F["scaffold_timetable()\n→ create timetable.csv\n(only if missing, never overwrite)"]
    F --> G["Build index\nname → lon/lat\n(rank: station > halt > stop)"]

    G --> H["For each of the 8 magistrale\nM200 … M900\nresolve stops"]

    H --> I{"Coordinates\nfound?"}
    I -- no --> J["Print warning\nskip stop"]
    I -- yes  --> K["Build features\n+ merge timetable fields\n(via route_id from timetable.csv)"]

    K --> L["rail_stations.geojson\nPoint features"]
    K --> M["rail_lines.geojson\nLineString + connection attributes"]
    K --> N["route_stops.csv\nstop sequence per magistrală"]

    L --> O[["Hint:\nuv run reiseplan-cli build-gpkg"]]
    M --> O
    N --> O
```

---

## Data source and licence

| Source | Content | Licence |
|---|---|---|
| OpenStreetMap via Overpass API | Geometry and names of all named rail stops in Romania | **ODbL 1.0** |
| Wikipedia / CFR line definition | Route alignment and official line lengths (M200–M900) | — |
| `timetable.csv` | Connection data (hand-maintained from infofer.ro) | — |

> **ODbL requirement:** When distributing derived data (GeoJSON, CSV, GPKG,
> website) the attribution `© OpenStreetMap contributors` must be included.
> Short link: <https://www.openstreetmap.org/copyright>

---

## Overpass query

The script sends exactly one query to the Overpass API:

```overpassql
[out:json][timeout:120];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
node["railway"~"^(station|halt|stop)$"]["name"](area.ro);
out tags center;
```

Result: **all named rail stops in Romania** — roughly 700–900 nodes. The script
intentionally fetches this broad raw dataset and filters locally to the defined
magistrală stops. One network call, then `--offline`.

Query syntax details: [docs/05_overpass_101.md](05_overpass_101.md).

---

## Line definition (hard-coded)

The CFR magistrale and their stops are defined in the script as `Line`/`Stop`
objects. These are the canonical data — they come **not** from OSM but reflect
the official CFR line layout (Wikipedia).

| Magistrală | Route | Stops | km |
|---|---|---|---|
| M200 | Brașov – Sibiu – Arad | 7 | 500 |
| M300 | București – Brașov – Cluj-Napoca – Oradea | 8 | 647 |
| M400 | Brașov – Dej – Satu Mare | 4 | 560 |
| M500 | București – Bacău – Suceava | 7 | 488 |
| M600 | Făurei – Bârlad – Iași | 4 | 395 |
| M700 | București – Brăila – Galați | 5 | 229 |
| M800 | București – Constanța – Mangalia | 5 | 225 |
| M900 | București – Craiova – Timișoara | 5 | 533 |

Each `Stop` carries a canonical name (`name`), the city name (`city`), and
optionally a list of alternative OSM spellings (`osm_names`). This is necessary
because OSM names can diverge from German/Romanian standard names (e.g.
`Cluj Napoca` instead of `Cluj-Napoca`, or `Gara de Nord` instead of
`București Nord`).

---

## Processing steps in detail

```mermaid
sequenceDiagram
    participant CLI as fetch_cfr_data.py
    participant OA  as Overpass API
    participant FS  as Filesystem

    CLI->>CLI: argparse (--offline?)

    alt Online mode
        CLI->>OA: POST /api/interpreter (query, timeout 180 s)
        OA-->>CLI: JSON (elements[])
        CLI->>FS: write data/raw/osm_ro_stations.json
    else Offline mode
        CLI->>FS: read data/raw/osm_ro_stations.json
    end

    CLI->>FS: scaffold_timetable() – create timetable.csv (if missing)
    CLI->>FS: load_timetable() – read timetable.csv → dict{route_id → row}
    CLI->>CLI: build_index() — name → (lon, lat), rank: station=0, halt=1, stop=2

    loop for each magistrală (M200–M900)
        CLI->>CLI: resolve() – look up canonical name + all osm_names in index
        CLI->>CLI: station_id_for() – assign ST01, ST02, …
        CLI->>CLI: merge timetable fields from dict (via route_id)
        CLI->>CLI: build route_feature + stop_rows
    end

    CLI->>FS: write rail_stations.geojson
    CLI->>FS: write rail_lines.geojson  (+ timetable attributes)
    CLI->>FS: write route_stops.csv
    CLI->>CLI: hint: run build-gpkg
```

### Index building (`build_index`)

The Overpass response is converted to a dictionary `name → (lon, lat)`. When the
same name appears multiple times (OSM duplicates), the type with the highest rank
wins:

| OSM `railway` value | Rank |
|---|---|
| `station` | 0 (highest) |
| `halt` | 1 |
| `stop` | 2 |
| other | 9 |

Coordinate fallback: nodes carry `lat`/`lon` directly; ways/relations only have
`center`. The code uses an explicit `in` check (not `or`) so `lat/lon == 0.0`
is not treated as missing.

### Stop resolution (`resolve`)

For each `Stop`, all `lookup_names()` (canonical name + `osm_names` list) are
checked against the index in order. The first match wins. If no name is found,
a warning is printed and the stop is omitted from the output geometry (the rest
of the magistrală is still written, provided at least two stops resolved).

### Station deduplication

`București Nord` appears on M300, M500, M700, M800, and M900. Only **one**
`rail_stations` feature is created (ID `ST01`). Assignment of multiple lines
to the same station happens via the `route_id` field in `route_stops.csv`.

---

## Timetable: hand-maintained connection data

### Concept

`data/processed/timetable.csv` is the only file in the project that is
**maintained by hand** and **never** overwritten by a script. It contains one
row per magistrală with the simplest regular connection (e.g. the fastest IC/IR
București–Timișoara on weekdays).

The fetch process reads it and merges the fields as **attributes into
`rail_lines.geojson`** (key: `route_id`). Times then appear automatically in
QGIS (attribute table, Identify, optionally Map Tip) and on the website, as soon
as you rebuild the data once.

```mermaid
flowchart LR
    TT["timetable.csv\n(hand-maintained)"]
    FP["fetch_cfr_data.py\n--offline"]
    RL["rail_lines.geojson\nfeature.properties:\n  days, dep_time, arr_time,\n  duration, via, train, approx"]
    QGIS["QGIS\nattribute table / Map Tip"]
    WEB["Website\nconnection line per route"]

    TT --> FP --> RL --> QGIS & WEB
```

### Schema `timetable.csv`

| Column | Content | Pre-filled? |
|---|---|---|
| `route_id` | Magistrală code, e.g. `M900` | ✓ (key) |
| `from_city` | Departure city | ✓ from stop sequence |
| `to_city` | Arrival city | ✓ from stop sequence |
| `days` | e.g. `täglich`, `Mo–Fr`, `Sommer` | — |
| `dep_time` | Departure `HH:MM` | — |
| `arr_time` | Arrival `HH:MM` | — |
| `duration` | Journey duration, e.g. `5:30` | — |
| `via` | Intermediate cities (comma-separated) | ✓ from stop sequence |
| `train` | Train number/name, e.g. `IR 1822` | — |
| `approx` | Which time fields are estimates: subset of `{dep,arr}` | — |
| `notes` | Free text (seasonal note, etc.) | — |

### Workflow: entering and applying times

```bash
# 1. Open timetable.csv in an editor and fill in the times
nvim data/processed/timetable.csv

# 2. Rebuild data (no network needed):
uv run python tools/fetch_cfr_data.py --offline
# → rail_lines.geojson now carries the dep_time, arr_time, … fields

# 3. Update GPKG and website:
uv run reiseplan-cli build-gpkg
uv run python tools/build_site.py

# 4. Inspect the result:
uv run reiseplan-cli timetable
```

### Sources for timetable times

CFR does not publish an open GTFS feed. Reliable sources:
- **infofer.ro:** <https://mersultrenurilor.infofer.ro> (official CFR journey planner)
- **railplanner / Eurail:** for international IC/EC connections

The entered times are a **snapshot** (not a live feed). Timetable changes
(usually December and June) may make them stale — record the date of last
verification in the `notes` field, e.g. `Stand: Mai 2026`.

---

## Output files

All files are in `EPSG:4326` (WGS 84) and follow the schema of the other project
data.

### `data/processed/rail_stations.geojson`

GeoJSON `FeatureCollection`, geometry type `Point`.

| Field | Type | Description |
|---|---|---|
| `station_id` | String | Short ID, e.g. `ST01` |
| `name` | String | Canonical station name |
| `city` | String | Associated city |

### `data/processed/rail_lines.geojson`

GeoJSON `FeatureCollection`, geometry type `LineString`
(vertices = resolved stops in sequence order).

| Field | Type | Description |
|---|---|---|
| `route_id` | String | Magistrală code, e.g. `M300` |
| `route_name` | String | Display name, e.g. `M300 · București – … – Oradea` |
| `from_city` | String | Departure city |
| `to_city` | String | Arrival city |
| `tags` | String | Comma-separated topic tags |
| `line_ref` | String | Same as `route_id` |
| `length_km` | Integer | Official line length (Wikipedia) |
| `days` | String | e.g. `täglich` (from `timetable.csv`, empty until entered) |
| `dep_time` | String | Departure time `HH:MM` |
| `arr_time` | String | Arrival time `HH:MM` |
| `duration` | String | Journey duration, e.g. `5:30` |
| `via` | String | Intermediate cities (pre-filled from stop sequence) |
| `train` | String | Train number/name |
| `approx` | String | Which times are estimates: subset of `{dep,arr}` |

### `data/processed/route_stops.csv`

Stop sequences per magistrală, one row per stop. No time columns — for times see
`timetable.csv`.

| Column | Description |
|---|---|
| `route_id` | Magistrală code |
| `sequence` | Order (1 = first stop) |
| `station` | Canonical station name |
| `city` | Associated city |
| `trip_hint` | Qualitative role: `Start (...)`, `Ziel (...)`, `Halt / Umstieg (...)` |

### `data/raw/osm_ro_stations.json`

Raw cache of the Overpass response. Not versioned (`.gitignore`), overwritten on
each online run. Enables `--offline` operation without a new network request.

---

## Usage

```bash
# Query Overpass, cache, and build all output files:
uv run python tools/fetch_cfr_data.py

# Rebuild from existing raw cache only (no network),
# e.g. after entering times in timetable.csv:
uv run python tools/fetch_cfr_data.py --offline
```

Then update the GPKG bundle for QGIS/QField:

```bash
uv run reiseplan-cli build-gpkg
```

### Dependencies

The script uses only the **Python standard library**
(`urllib`, `json`, `csv`, `pathlib`, `dataclasses`, `argparse`) — no additional
packages needed, no `uv`/`pip install` required. The `uv run` prefix is optional;
`python tools/fetch_cfr_data.py` works equally well.

---

## CI: automatic data refresh

Workflow: `.github/workflows/refresh-data.yml`

```mermaid
flowchart LR
    A["GitHub Actions\nmanual trigger"] --> B["python tools/fetch_cfr_data.py\n(online mode)"]
    B --> C["data/processed/*.geojson\ndata/processed/*.csv\nupdated"]
    C --> D["Open pull request\n(branch data/overpass-refresh)"]
    D --> E{Merge?}
    E -- yes --> F["pages.yml: rebuild website\nand deploy to GitHub Pages"]
    E -- no --> G["Discard"]
```

The refresh runs **only on manual trigger** (Actions → "Bahndaten aktualisieren
(Overpass)" → *Run workflow*). A weekly `cron` is commented out in the workflow
and can be enabled if needed.

> **Note:** The CI refresh fetches new OSM geometry but does not touch
> `timetable.csv` — entered times are preserved when the PR is merged, as long as
> `timetable.csv` was not manually modified.

After the PR is merged, `pages.yml` rebuilds the online map automatically.
Details: [docs/04_web_pages.md](04_web_pages.md).

---

## Further reading

- Overpass query syntax explained: [docs/05_overpass_101.md](05_overpass_101.md)
- Online map and GitHub Pages: [docs/04_web_pages.md](04_web_pages.md)
- Overpass Turbo (interactive): <https://overpass-turbo.eu>
- ODbL licence text: <https://opendatacommons.org/licenses/odbl/>
