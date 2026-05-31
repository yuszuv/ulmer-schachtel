#!/usr/bin/env python3
"""Fetch and build historische_regionen.geojson for the Ulmer Schachtel map.

Data source
-----------
Natural Earth 10m admin-1 states/provinces (public domain):
https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-1-states-provinces/

Approach
--------
Historical region boundaries are constructed by dissolving modern administrative
units (Romanian județe, Serbian districts, Ukrainian oblasts) into their
corresponding historical regions as they existed around 1900.  While precise
1900-era boundaries differ slightly from today's, this gives a well-documented,
reproducible approximation that is correct at the regional level.

For the full historical extent, cross-border regions (Banat, Bukowina) include
the relevant Serbian and Ukrainian administrative units.

Output
------
  data/reference/historical/historische_regionen.geojson   (EPSG:4326)
  data/reference/historical/historische_regionen_attribution.json

Usage
-----
  python tools/fetch_historical_regions.py

Requires: ogr2ogr (GDAL) on $PATH. No third-party Python packages needed.
"""

from __future__ import annotations

import datetime
import io
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "reference" / "historical"
OUT_FILE = OUT_DIR / "historische_regionen.geojson"
ATTR_FILE = OUT_DIR / "historische_regionen_attribution.json"

NE_URL = (
    "https://naciscdn.org/naturalearth/10m/cultural/"
    "ne_10m_admin_1_states_provinces.zip"
)
USER_AGENT = "UlmerSchachtelMap/1.0 (jan@sternprodukt.de)"

# ---------------------------------------------------------------------------
# Region definitions
# ---------------------------------------------------------------------------
# Each entry: name_de → config dict.
# "units" is a list of (iso_a2, list-of-name-field-values-in-NE-data).
# The "name" field (not name_en) of Natural Earth is used for matching because
# it is the primary key in the shapefile index and avoids SQLite encoding edge
# cases with diacritics.

REGIONS: list[dict] = [
    {
        "NAME": "Siebenbürgen",
        "NAME_LOCAL": "Transilvania / Ardeal / Erdély",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Um 1900 Transleithanisches Ungarn; 1918 an Rumänien. "
            "Die CFR-Reise durchquert das Herz Siebenbürgens."
        ),
        "units": [
            ("RO", ["Alba", "Bistrita-Nasaud", "Brasov", "Cluj", "Covasna",
                    "Harghita", "Hunedoara", "Mures", "Sibiu"]),
        ],
    },
    {
        "NAME": "Banat",
        "NAME_LOCAL": "Banat / Bánság / Банат",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Um 1900 zwischen Österreich-Ungarn (RO-Anteil), Serbien "
            "und einem Zipfel Ungarns aufgeteilt."
        ),
        "units": [
            ("RO", ["Timis", "Caras-Severin"]),
            ("RS", ["Severno-Banatski", "Srednje-Banatski", "Južno-Banatski"]),
        ],
    },
    {
        "NAME": "Crișana",
        "NAME_LOCAL": "Crișana / Körösvidék / Partium",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Um 1900 zum Königreich Ungarn (Transleithanien). "
            "Arad und Großwardein (Oradea) sind die Hauptstädte."
        ),
        "units": [
            ("RO", ["Arad", "Bihor", "Salaj"]),
        ],
    },
    {
        "NAME": "Maramureș",
        "NAME_LOCAL": "Maramureș / Máramaros",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Um 1900 nördlichster Teil des Königreichs Ungarn. "
            "Reich an Salz und Holz; Sathmar (Satu Mare) am Südrand."
        ),
        "units": [
            ("RO", ["Maramures", "Satu Mare"]),
        ],
    },
    {
        "NAME": "Bukowina",
        "NAME_LOCAL": "Bucovina / Буковина",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Um 1900 habsburgisches Kronland; 1918 geteilt zwischen Rumänien "
            "(Süden) und der Ukraine (Norden, heute Oblast Czernowitz)."
        ),
        "units": [
            ("RO", ["Suceava"]),
            ("UA", ["Chernivtsi"]),
        ],
    },
    {
        "NAME": "Moldau",
        "NAME_LOCAL": "Moldova / Principatul Moldovei",
        "EMPIRE": "Königreich Rumänien",
        "NOTE": (
            "Historisches Fürstentum Moldau; seit 1859 mit der Walachei "
            "vereint zum Königreich Rumänien (1881)."
        ),
        "units": [
            ("RO", ["Bacau", "Botosani", "Iasi", "Neamt",
                    "Vaslui", "Vrancea", "Galati"]),
        ],
    },
    {
        "NAME": "Muntenia",
        "NAME_LOCAL": "Muntenia / Valahia Mare / Große Walachei",
        "EMPIRE": "Königreich Rumänien",
        "NOTE": (
            "Kernland des Königreichs Rumänien mit der Hauptstadt Bukarest. "
            "Vereint 1859 mit der Moldau zum Fürstentum Rumänien."
        ),
        "units": [
            ("RO", ["Arges", "Braila", "Buzau", "Calarasi", "Dâmbovita",
                    "Giurgiu", "Ialomita", "Ilfov", "Prahova", "Teleorman",
                    "Bucharest"]),
        ],
    },
    {
        "NAME": "Oltenien",
        "NAME_LOCAL": "Oltenia / Valahia Mică / Kleine Walachei",
        "EMPIRE": "Königreich Rumänien",
        "NOTE": (
            "Westliche Walachei jenseits des Olt; Craiova ist die "
            "historische Hauptstadt."
        ),
        "units": [
            ("RO", ["Dolj", "Gorj", "Mehedinti", "Olt", "Vâlcea"]),
        ],
    },
    {
        "NAME": "Dobrudscha",
        "NAME_LOCAL": "Dobrogea / Добруджа",
        "EMPIRE": "Königreich Rumänien",
        "NOTE": (
            "1878 nach dem Russisch-Türkischen Krieg an Rumänien abgetreten; "
            "zuvor osmanische Provinz. Zugang zum Schwarzen Meer."
        ),
        "units": [
            ("RO", ["Constanta", "Tulcea"]),
        ],
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def download_ne(url: str, tmp_dir: str) -> str:
    """Download Natural Earth zip, extract SHP to tmp_dir, return .shp path."""
    print(f"Downloading Natural Earth admin-1 …")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    data = urllib.request.urlopen(req, timeout=120).read()
    print(f"  {len(data) // 1024} kB received")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(tmp_dir)
    shp_files = [f for f in os.listdir(tmp_dir) if f.endswith(".shp")]
    if not shp_files:
        sys.exit("No .shp found in downloaded zip")
    return os.path.join(tmp_dir, shp_files[0])


def dissolve_region(shp: str, region: dict) -> dict | None:
    """Dissolve the admin units for one historical region into a GeoJSON feature.

    Uses ogr2ogr's SQLite dialect with ST_Union + UNION ALL so units from
    different countries (iso_a2) are combined in a single dissolve.
    """
    name = region["NAME"]
    units = region["units"]

    # Build subquery parts: one SELECT per (country, name-list) pair.
    parts = []
    for iso, names in units:
        name_list = ", ".join(f"'{n}'" for n in names)
        parts.append(
            f"SELECT geometry as geom "
            f"FROM ne_10m_admin_1_states_provinces "
            f"WHERE iso_a2 = '{iso}' AND name IN ({name_list})"
        )

    union_all = "\nUNION ALL\n".join(parts)
    sql = (
        f"SELECT ST_Union(geom) as geometry, "
        f"'{name}' as NAME "
        f"FROM (\n{union_all}\n)"
    )

    result = subprocess.run(
        [
            "ogr2ogr", "-f", "GeoJSON", "/dev/stdout", shp,
            "-dialect", "SQLite", "-sql", sql,
            "-lco", "RFC7946=YES", "-t_srs", "EPSG:4326",
        ],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ⚠ ogr2ogr failed for {name!r}: {result.stderr[:200]}")
        return None

    try:
        fc = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  ⚠ JSON parse error for {name!r}")
        return None

    feats = fc.get("features", [])
    if not feats:
        print(f"  ⚠ No geometry produced for {name!r} — check unit name spelling")
        return None

    # Replace the minimal properties from SQL with the full region metadata.
    feat = feats[0]
    feat["properties"] = {
        "NAME":       region["NAME"],
        "NAME_LOCAL": region["NAME_LOCAL"],
        "EMPIRE":     region["EMPIRE"],
        "NOTE":       region["NOTE"],
        "SOURCE":     "Natural Earth 10m admin-1 (public domain) dissolved by region",
    }
    return feat


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        shp = download_ne(NE_URL, tmp)

        features = []
        for region in REGIONS:
            print(f"Processing {region['NAME']} …")
            feat = dissolve_region(shp, region)
            if feat is not None:
                features.append(feat)
                geom_type = feat["geometry"]["type"]
                print(f"  → {geom_type}")
            else:
                print(f"  → SKIPPED")

    # Sort deterministically by NAME for stable diffs.
    features.sort(key=lambda f: f["properties"]["NAME"])

    fc = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }

    OUT_FILE.write_text(json.dumps(fc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {len(features)} regions → {OUT_FILE}")

    # Attribution sidecar.
    attribution = {
        "generated": datetime.date.today().isoformat(),
        "source": "Natural Earth 10m admin-1 states/provinces",
        "url": NE_URL,
        "license": "Public Domain — https://www.naturalearthdata.com/about/terms-of-use/",
        "methodology": (
            "Modern administrative units (Romanian județe, Serbian districts, "
            "Ukrainian oblasts) dissolved into historical regions as they existed "
            "around 1900 using ogr2ogr SQLite ST_Union. Boundaries are approximate "
            "at the county level; regional assignment follows standard historical "
            "geography (Wikipedia 'Historical regions of Romania', Encyclopaedia "
            "Britannica entries per region)."
        ),
        "regions": [
            {"name": r["NAME"], "empire": r["EMPIRE"],
             "units": {iso: names for iso, names in r["units"]}}
            for r in REGIONS
        ],
    }
    ATTR_FILE.write_text(json.dumps(attribution, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    print(f"Wrote attribution → {ATTR_FILE}")


if __name__ == "__main__":
    main()
