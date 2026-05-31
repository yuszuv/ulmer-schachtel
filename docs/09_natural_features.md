# Natural Features Layer — Gebirge & Landschaftszüge

Historical-atlas style mountain ridges, peaks, and landscape labels
overlaid on the map canvas. The visual goal is the *zimmermann.jpg*
"Donau-Staaten" atlas (1:5 Mio, ca. 1940): letter-spaced, brown names
that follow ridge lines.

## Data source

OpenStreetMap via Overpass API. **© OpenStreetMap contributors, ODbL 1.0.**
<https://www.openstreetmap.org/copyright>

## Fetch

```
uv run reiseplan-natural                 # online fetch + cache
uv run reiseplan-natural --offline       # rebuild from raw cache (no network)
uv run reiseplan-natural --min-ele 1500  # default: peaks ≥ 1500 m only
```

The k.u.k. bounding box is too large for a single Overpass call.
The script tiles the region into 4 ° × 4 ° cells and issues **two
separate requests per tile** (ridge ways + point nodes) to avoid
per-query timeouts in the dense Alps. 18 tiles × 2 calls = 36 requests;
allow ~25 minutes for the first online run. Results are cached in
`data/raw/osm_natural_features.json`; subsequent offline rebuilds take
seconds.

Some Alpine tiles may return 504 from the Overpass server under heavy
load. Failed tiles are skipped with a `[SKIP]` warning and logged in
the cache metadata (`skipped_queries`). Re-run later to fill gaps;
the script deduplicates across runs via OSM id + type.

## Output files

| File | Geometry | Content | QGIS label |
|---|---|---|---|
| `data/processed/natural_ridges.geojson` | LineString | `natural=ridge` ways | **Curved** (placement=3) |
| `data/processed/mountain_peaks.geojson` | Point | `natural=peak` nodes (ele filtered) | straight, spot-height style |
| `data/processed/landscape_labels.geojson` | Point | `natural=mountain_range`, `natural=valley` nodes | straight, spaced |
| `data/processed/natural_features_attribution.json` | — | ODbL sidecar | — |

Properties per feature: `name`, `name_de`, `natural`, `place`,
`ele` (peaks), `osm_id`, `osm_type`.

## OSM coverage note

The big iconic range names (**Karpaten**, **Alpen**, **Siebenbürgen**,
**Beskiden**, **Ostalpen** …) are stored in OSM as *relations*, not as
point nodes — so they do **not** appear in `landscape_labels.geojson`.
For these, draw hand-made label lines (see
[08_curved_labels.md](08_curved_labels.md)):

- Create `data/label_lines_relief.gpkg` (LineString, EPSG:4326, field `label`)
- Draw one gentle left-to-right arc per range name
- Style invisible, labels Curved, brown, letter-spaced

## QGIS Styling guide

### Layer group

Add all layers to a group **"Relief / Landschaft"** in the layer tree
(below "Historisch", above "Weltkarte").

### natural_ridges — curved brown names

1. **Symbology:** Simple Line → Pen style: No Pen (invisible carrier)
2. **Labels → Single labels → Value:** `coalesce("name_de", "name")`
3. **Placement → Mode:** Curved
   - Max curved angle inner / outer: **20° / 20°**
   - Allow upside-down: *never*
   - Placement: On line, distance 0
4. **Text:** font matching other layers; size ≈ 7; color `107,79,42`
   (brown as in existing labels at `reiseplan.qgs:2138`); increase
   Letter spacing for the spaced-out atlas look
5. **Buffer:** white, 0.6 mm
6. **Scale visibility:** show only in the project's typical map range
   (e.g. maxScale ≈ 6 000 000)

Reference: the existing curved-label layer at `qgis/reiseplan.qgs:2186`
uses `placement="3"` — copy that block's `<labeling>` XML if needed.

### mountain_peaks — spot heights

1. **Symbology:** small brown triangle marker (▲), size 1.5–2 mm
2. **Labels:** expression `"name" || '\n' || "ele"` — name on top,
   elevation on bottom in small numerals
3. **Scale visibility:** only show prominent peaks at small scales
   (consider a scale-dependent rule to hide below, say, 2200 m when
   zoomed out)

### landscape_labels — spaced range names

1. **Symbology:** no marker (invisible)
2. **Labels:** `coalesce("name_de", "name")`; placement: free/horizontal;
   increase Letter spacing significantly (atlas "Sperrung" effect);
   same brown `107,79,42`
3. **Scale visibility:** same range as ridges

### hand-drawn lines (label_lines_relief.gpkg)

Follow [08_curved_labels.md](08_curved_labels.md) steps 1–5.
Styled identically to `natural_ridges` but with larger font (the
iconic range names span more space).  Suggested names to draw:

- Karpaten (the great Carpathian arc)
- Südkarpaten / Transsilvanische Alpen
- Siebenbürgen (Transylvania region)
- Ostalpen (Eastern Alps)
- Beskiden (northern arc)
- Dinarische Alpen / Dinarides

## QField packaging

After adding the layers in QGIS and saving `reiseplan.qgs`, the three
GeoJSON layers are already registered in `tools/reiseplan/packaging.py`
(`LAYERS` list, entries `natural_ridges`, `mountain_peaks`,
`landscape_labels`). The hand-drawn GeoPackage needs its own entry:

```python
_Layer("label_lines_relief",
       "data/label_lines_relief.gpkg", "label_lines_relief",
       "../data/label_lines_relief.gpkg|layername=label_lines_relief"),
```

Run `uv run python tools/export_qfield.py` to rebuild the QField bundle.
