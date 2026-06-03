# Natural Features Layer — Mountain Ridges & Landscape Labels

> **Architecture note (2026-06):** The natural-feature pipeline now runs on
> the generic thematic-layer infrastructure (Pattern 4).  `fetch_natural.py`
> is a thin wrapper around `thematic.run(themes.natural.SPEC, …)`.  The fetch
> logic, tile grid, Wikidata cache, and GeoJSON outputs are unchanged —
> `--offline` rebuilds remain byte-identical to prior runs.  See
> `docs/data-and-layers/thematic-layers.md` for the full pipeline design.

Historical-atlas style mountain ridges, peaks, and landscape labels
overlaid on the map canvas. The visual goal is the *zimmermann.jpg*
"Donau-Staaten" atlas (1:5 Mio, ca. 1940): letter-spaced, brown names
that follow ridge lines.

## Data sources

**Geometry & tags:** OpenStreetMap via Overpass API.
**© OpenStreetMap contributors, ODbL 1.0.**
<https://www.openstreetmap.org/copyright>

**German names:** de.wikipedia titles + Wikidata `wbgetentities` labels. **CC0.**
<https://www.wikidata.org>

## Fetch

```
uv run reiseplan-natural                 # online fetch + cache + Wikidata enrich
uv run reiseplan-natural --offline       # rebuild from raw caches (no network)
uv run reiseplan-natural --min-ele 1500  # default: peaks ≥ 1500 m only
uv run reiseplan-natural --no-enrich     # skip Wikidata, name_de from OSM only
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
| `data/processed/natural_attribution.json` | — | ODbL sidecar | — |

Properties per feature:
- **Peaks**: `name`, `name_de`, `name_de_src`, `wikidata`, `natural`, `place`, `ele`, `importance` (1 = Major, 2 = Significant, 3 = Minor, 4 = Local), `osm_id`, `osm_type`.
- **Ridges**: `name`, `name_de`, `name_de_src`, `wikidata`, `natural`, `place`, `length_deg`, `importance` (1 = Major, 2 = Significant, 3 = Minor), `osm_id`, `osm_type`.
- **Landscape Labels**: `name`, `name_de`, `name_de_src`, `wikidata`, `natural`, `place`, `importance` (1 = Major, 2 = Minor), `osm_id`, `osm_type`.

## German name enrichment (Wikipedia / Wikidata)

The QGIS labels use `coalesce("name_de", "name")` — the **German** name wins
when present. OSM, however, carries very few `name:de` tags. Where a feature
has a `wikidata` QID, the fetch resolves its German name via a single Wikidata
`wbgetentities` call (`props=labels|sitelinks`, `languages=de`,
`sitefilter=dewiki|dewikivoyage`, **CC0**) that returns both the de.**wikipedia**
article title and the German label at once. This fills in atlas exonyms such as
*Karpaten* / *Siebenbürgen* that OSM stores only under the local name.

Priority and provenance (per feature):

| field | meaning |
|---|---|
| `name_de` | German name — **only set when it differs from `name`** (an identical value adds nothing to `coalesce`) |
| `name_de_src` | `osm` (from `name:de`) · `wikipedia` (de.wikipedia title) · `wikidata` (QID label) · `null` |
| `wikidata` | the OSM `wikidata` QID, kept for verifiability (`null` if absent) |

Priority: **OSM `name:de` > de.wikipedia title > Wikidata `de` label.** The
de.wikipedia article title is the authoritative German exonym (e.g.
*Hermannstadt*); a trailing disambiguator like *(Stadt)* is stripped. No machine
translation or transliteration is done — only verifiable sources.

Resolved names are cached in two committed, additive maps beside each other:
`data/raw/wikidata_de_labels.json` (`{QID: label}`) and
`data/raw/wikidata_de_wikipedia.json` (`{QID: dewiki-title | null}`, where `null`
means "checked, no German article"). Neither matches the gitignored `osm_*.json`
pattern. `--offline` reproduces the German names without network access (it
degrades to the cached label if the Wikipedia cache is not yet populated). Skip
the lookup entirely with `--no-enrich` (`name_de` then comes from OSM `name:de`
only).

## OSM coverage note

Most range names appear as point nodes in `landscape_labels.geojson`.
Many of the Slavic/English OSM names were resolved to German exonyms via
Wikidata (e.g. *Dinarsko gorje → Dinarisches Gebirge*,
*Eastern Alps → Ostalpen*, *Banat Mountains → Banater Gebirge*).

The very large arc names — **Karpaten** and **Siebenbürgen** — are stored
in OSM as *relations* only, so they have no point node and do **not** appear
in `landscape_labels.geojson`. For these, draw hand-made label lines
(see [curved-labels.md](curved-labels.md)):

- Create `data/label_lines_relief.gpkg` (LineString, EPSG:4326, field `label`)
- Draw one gentle left-to-right arc per range name
- Style invisible, labels Curved, brown, letter-spaced

## QGIS Styling guide

### Layer group

Add all layers to a group **"Relief / Landschaft"** in the layer tree
(below "Historisch", above "Weltkarte").

### natural_ridges — curved brown names

1. **Symbology:** Simple Line → Pen style: No Pen (invisible carrier)
2. **Labels → Single labels → Value:** scale-dependent `CASE` expression:
   ```sql
   CASE 
     WHEN "importance" = 1 OR 
          (@map_scale <= 1500000 AND "importance" = 2) OR 
          (@map_scale <= 750000 AND "importance" = 3) 
     THEN coalesce("name_de", "name") 
     ELSE NULL 
   END
   ```
3. **Placement → Mode:** Curved
   - Max curved angle inner / outer: **25° / 25°**
   - Allow upside-down: *never*
   - Placement: On line, distance 0
4. **Text:** font matching other layers; size ≈ 6.5; color `107,79,42`
   (brown as in existing labels at `reiseplan.qgs:2138`); increase
   Letter spacing for the spaced-out atlas look
5. **Buffer:** white, 0.6 mm
6. **Scale visibility:** show only in the project's typical map range
   (e.g. maxScale ≈ 6 000 000)

### mountain_peaks — spot heights

1. **Symbology:** Rule-based renderer with four rules for different importance levels to avoid clutter:
   - **Major Peaks (Imp 1):** filter `"importance" = 1`, visible scale `1:3 000 000` to `0`
   - **Significant Peaks (Imp 2):** filter `"importance" = 2`, visible scale `1:1 500 000` to `0`
   - **Minor Peaks (Imp 3):** filter `"importance" = 3`, visible scale `1:750 000` to `0`
   - **Local Peaks (Imp 4):** filter `"importance" = 4`, visible scale `1:300 000` to `0`
   Symbol: small brown triangle marker (▲), size 1.6 mm
2. **Labels:** scale-dependent expression:
   ```sql
   CASE 
     WHEN "importance" = 1 OR 
          (@map_scale <= 1500000 AND "importance" = 2) OR 
          (@map_scale <= 750000 AND "importance" = 3) OR 
          (@map_scale <= 300000 AND "importance" = 4) 
     THEN coalesce("name_de", "name") || 
          CASE WHEN "ele" IS NOT NULL THEN '\n' || to_string("ele") || ' m' ELSE '' END 
     ELSE NULL 
   END
   ```
   German name on top (when available), elevation below in small numerals.
3. **Scale visibility:** 1:3 000 000 to 0 (entire layer scale gate)

### landscape_labels — spaced range names

1. **Symbology:** no marker (invisible)
2. **Labels:** scale-dependent expression:
   ```sql
   CASE 
     WHEN "importance" = 1 OR 
          (@map_scale <= 3000000 AND "importance" = 2) 
     THEN upper(coalesce("name_de", "name")) 
     ELSE NULL 
   END
   ```
   Placement: free/horizontal; increase Letter spacing significantly (atlas "Sperrung" effect); same brown `107,79,42`
3. **Scale visibility:** 1:10 000 000 to 800 000

### hand-drawn lines (label_lines_relief.gpkg)

Follow [curved-labels.md](curved-labels.md) steps 1–5.
Styled identically to `natural_ridges` but with larger font (the
iconic range names span more space).  Names needed as hand-drawn arcs
(not present as OSM nodes):

- Karpaten (the great Carpathian arc)
- Südkarpaten / Transsilvanische Alpen
- Siebenbürgen (Transylvania region)

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
