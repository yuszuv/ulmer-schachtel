# Historical reference data

Reference layers for the historical map context (~1900): political boundaries,
regional divisions, and historically named cities of the former Austria-Hungary
and Kingdom of Romania.

## Files

| File | Layer name | Type | Description |
|---|---|---|---|
| `staatsgrenzen.geojson` | Grenzen 1800 | Polygon | World-level political borders ~1880–1914 (236 states). Source: [aourednik/historical-basemaps](https://github.com/aourednik/historical-basemaps), GPL-3.0. |
| `historische_regionen.geojson` | Historische Regionen | Polygon | 9 historical macro-regions around 1900. |
| `historische_regionen_attribution.json` | — | — | Data provenance for `historische_regionen.geojson`. |
| `historische_staedte.geojson` | Historische Städte | Point | 25 curated cities with multilingual names (~1900). |

## historische_regionen.geojson

**Regions covered:** Siebenbürgen, Banat, Crișana, Maramureș, Bukowina, Moldau,
Muntenia, Oltenien, Dobrudscha.

**Data source:** [Natural Earth 10m admin-1 states/provinces](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/)
— **public domain**. Region polygons are constructed by dissolving modern
administrative units into their historical region membership:

- Romanian județe (counties) → 9 regions
- Serbian Vojvodina districts → Banat (Serbian share)
- Chernivtsi Oblast (Ukraine) → Bukowina (Ukrainian share)

This gives full historical extent for cross-border regions (Banat: RO + RS;
Bukowina: RO + UA). Boundaries are approximate at the county level; regional
assignment follows standard Romanian historical geography.

**Rebuild:** `python tools/fetch_historical_regions.py`

**Property schema:**

| Field | Example |
|---|---|
| `NAME` | `Siebenbürgen` (German label) |
| `NAME_LOCAL` | `Transilvania / Ardeal / Erdély` |
| `EMPIRE` | `Österreich-Ungarn` or `Königreich Rumänien` |
| `NOTE` | Brief historical note |
| `SOURCE` | Provenance string |

**QGIS style:** `qgis/styles/historische_regionen.qml` — RuleRenderer,
2-tone fill by `EMPIRE` field, scale-gated 1:200k–1:3 Mio.

## historische_staedte.geojson

**25 curated cities** with ~1900 names in German, Hungarian, and modern Romanian.
Historical names from Meyers Konversationslexikon 1905, Brockhaus 1901,
Encyclopaedia Britannica 1911. No names are guessed or transliterated.

**Rebuild:** `python tools/build_historical_cities.py`

**Property schema:**

| Field | Example |
|---|---|
| `NAME` | `Brașov` (modern Romanian) |
| `NAME_DE` | `Kronstadt` (historical German) |
| `NAME_HU` | `Brassó` (historical Hungarian) |
| `REGION` | `Siebenbürgen` |
| `EMPIRE` | `Österreich-Ungarn` |
| `NOTE` | Brief historical note |
| `SOURCE` | Provenance string |

**QGIS style:** `qgis/styles/historische_staedte.qml` — small sepia marker,
label `NAME (NAME_DE)`, Map Tip with all names + NOTE, visible from 1:1.5 Mio.

## staatsgrenzen.geojson

World-level political boundaries ~1880–1914 (236 MultiPolygon features).
Source: [aourednik/historical-basemaps](https://github.com/aourednik/historical-basemaps)
(GPL-3.0). Properties: `NAME`, `SUBJECTO`, `BORDERPRECISION`, `PARTOF`, `ABBREVN`.

In the QGIS project this layer is loaded as **"Grenzen 1800"** and filtered to the
empires relevant to the trip (Austria Hungary, Romania, Ottoman Empire, Balkans,
Russia). See `tools/qgis_bootstrap.py` → `SUBSET_FOR`.

## Style/copyright note

All files in this directory are safe to redistribute:
- `staatsgrenzen.geojson`: GPL-3.0 (source is GPL)
- `historische_regionen.geojson`: public domain (Natural Earth)
- `historische_staedte.geojson`: hand-curated from pre-1928 encyclopaedias (public domain)
