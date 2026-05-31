```text
 _   _ _
| | | | |_ __  ___ _ _
| |_| | | '  \/ -_) '_|
 \___/|_|_|_|_\___|_|
 ___     _            _   _       _
/ __| __| |_  __ _ __| |_| |_ ___| |
\__ \/ _| ' \/ _` / _| ' \  _/ -_) |
|___/\__|_||_\__,_\__|_||_\__\___|_|

         |>>>
         |
   ______|__________________________
  / ___  ___  ___  ___  ___  ___     \
 | |_o_||_o_||_o_||_o_||_o_||_o_|     |
  \________________________________ _/
~~~~~~~~~~~~~~ Donau ~~~~~~~~~~~~~~~~~~~
```

# Ulmer Schachtel – Romania Rail Travel Planner (QGIS → QField)

> *Named after the **»Ulmer Schachtel«** — the simple flat-bottomed wooden boat
> with which emigrants travelled from Ulm downstream along the Danube to the
> Banat (Romania) in the 18th/19th century. One-way trip: at the destination the
> boat was dismantled and its timber used by the settlers to build houses.*

A lightly historical-flavoured map application for planning a rail holiday in Romania.

## Goals (Basic v1)

- Plan rail journeys with multiple route options.
- Markers for prioritised destinations:
  - Dracula towns: Brașov, Sighișoara
  - Cities: Timișoara, București
  - Danube Delta highlights: Sulina, Sfântu Gheorghe, Letea Forest
- Prepared for export to QField.

> Note: The Danube Delta highlights are **not reachable by rail**. The line ends
> at Tulcea; onward travel into the Delta is by boat.

## Directory layout

- `data/raw` – raw data (future: GTFS, OSM exports)
- `data/processed` – vector and table data used by the project
- `data/reference/historical` – reference material for the historical map style (Fancy stage)
- `qgis/reiseplan.qgz` – ready-made QGIS project (layers + styles)
- `qgis/projects` – space for your own QGIS project files (`.qgz`)
- `qgis/styles` – QGIS style files (`.qml`, incl. embedded SVG markers)
- `docs` – setup and export documentation
- `tools/reiseplan` – Python package: CLI, site builder, OSM ingest, GPKG/QField packaging
- `.github/workflows` – GitHub Actions (Pages deploy, data refresh)

## Quick start (QGIS)

0. Build the data bundle: `uv run reiseplan-cli build-gpkg`
   (creates `data/processed/reiseplan.gpkg` with all four layers; GeoJSON files
   remain the versioned source format).
1. Open QGIS (>= 3.28 recommended).
2. Create a new project and **first** set the project CRS:
   *Project → Properties → CRS → `EPSG:3844 (Stereo70)`*.
   Important: set the CRS **before** loading any layers. Otherwise QGIS adopts
   the CRS of the first layer (`EPSG:4326`, the WGS84/GPS format required by the
   GeoJSON spec) as the project CRS.
3. Load layers from `data/processed/reiseplan.gpkg` (4 layers, one file):
   - `poi_destinations`
   - `rail_stations`
   - `rail_lines` (magistrale; carry connection data from `timetable.csv` as attributes)
   - `info_markers` (ℹ "About this map" – in-app help)

   Layers are in `EPSG:4326` and are reprojected on-the-fly to `EPSG:3844` — the
   data itself is unchanged. If QGIS asks whether to switch the project CRS to match
   the layer: **decline**.
4. Apply styles (*Layer Properties → Symbology → Load Style…*, **all categories**):
   - `poi_destinations` → `qgis/styles/poi_destinations.qml`
   - `rail_lines` → `qgis/styles/rail_lines.qml`
   - `rail_stations` → `qgis/styles/rail_stations.qml`
   - `info_markers` → `qgis/styles/info_markers.qml`
5. Load a base map: *Web → QuickMapServices → OSM Standard* (plugin required).
6. Labels **and Map Tips** (HTML card on tap) come automatically from the QML files.
7. **Save the project**: *Project → Save As…* → `qgis/projects/v1.qgz`
   (`.qgz` extension required). Without a saved project, the later QField export
   will fail with an `AssertionError`.
8. *(optional, recommended)* Automate the setup from the **Python Console** with the
   helper scripts in `tools/` — run in order: `qgis_bootstrap.py` (CRS, layers,
   styles, canvas), `qgis_basemaps.py` (base maps), `qgis_setup_scales.py`
   (scale-dependent rendering + automatic base-map switching), `qgis_bookmarks.py`
   (spatial bookmarks). They reproduce steps 2–7 from code. Then save again.

Details: see [docs/01_qgis_setup.md](docs/01_qgis_setup.md).

## Quick start (CLI, via uv)

```bash
uv run reiseplan-cli list-routes
uv run reiseplan-cli overview
uv run reiseplan-cli show-route M300
uv run reiseplan-cli list-destinations --category dracula_city
uv run reiseplan-cli timetable --json | jq .   # machine-readable
```

Or as a Python module (same result):

```bash
uv run python -m reiseplan.cli overview
```

## Online map (GitHub Pages)

An **interactive website** (map + readable route/destination overview) is available
for non-QGIS users — no installation required. Open the Pages URL:

> `https://<user>.github.io/<repo>/` (appears after the first deploy under
> *Actions* or *Settings → Pages*).

Build and open locally:

```bash
uv run reiseplan-site             # generates site/index.html (self-contained)
xdg-open site/index.html          # or open the file directly in a browser
```

The site is built and published automatically by GitHub Actions
(workflow `.github/workflows/pages.yml`) on every push to `main` that touches
data or the build script. **One-time setup:** *Settings → Pages → Source = "GitHub
Actions"*. Fresh rail data can be fetched on demand — run the
*"Bahndaten aktualisieren (Overpass)"* workflow under *Actions*; it opens a PR
with the data diff. Details: [docs/04_web_pages.md](docs/04_web_pages.md).

## Data sources & licence

Rail data (stations and routes) is based on the **CFR magistrale 200–900**
("Căile Ferate Române main lines") and fetched from **OpenStreetMap** via the
Overpass API:

```bash
uv run reiseplan-fetch            # query OSM, cache, build GeoJSON
uv run reiseplan-fetch --offline  # rebuild from data/raw cache only
```

> Map data © **OpenStreetMap contributors**, licensed under the
> [Open Database License (ODbL)](https://www.openstreetmap.org/copyright).
> This attribution must be included when redistributing derived data.

CFR does not publish an open timetable feed. `route_stops.csv` therefore contains
only the **stop sequence** per magistrală (order + role), no times. Real connections
(dep/arr/days/via) are **hand-maintained** in `data/processed/timetable.csv` —
one row per magistrală; the fetch script only creates this file as a scaffold
template when it is missing and never overwrites entered times. On the next
`fetch …` run, times are merged as attributes into `rail_lines.geojson`.
Authoritative times: <https://mersultrenurilor.infofer.ro>.
CLI overview: `uv run reiseplan-cli timetable`.

How the Overpass query works and how to customise it:
[docs/05_overpass_101.md](docs/05_overpass_101.md).

## Further reading

- QGIS setup: [docs/01_qgis_setup.md](docs/01_qgis_setup.md)
- QField export: [docs/02_qfield_export.md](docs/02_qfield_export.md)
- CLI reference: [docs/03_cli_reference.md](docs/03_cli_reference.md)
- Online map / GitHub Pages: [docs/04_web_pages.md](docs/04_web_pages.md)
- Overpass 101 (rail data from OSM): [docs/05_overpass_101.md](docs/05_overpass_101.md)
- CFR fetch process and data flow: [docs/06_cfr_data_fetch.md](docs/06_cfr_data_fetch.md)
- Fancy style TODO: [docs/STYLE_TODO_FANCY.md](docs/STYLE_TODO_FANCY.md)
