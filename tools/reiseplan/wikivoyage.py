#!/usr/bin/env python3
"""WikiVoyage city ingest — cities of Romania's historical regions.

Fetches cities (``place=city|town``) per historical region and keeps only those
that have an article on **de.wikivoyage.org**.  The German WikiVoyage edition is
therefore both the data source and the filter: no German article → city excluded.

Pipeline (three stages, stdlib only, Result[T] at network boundaries)
----------------------------------------------------------------------
1. **Overpass** — one request per historical region via ``ISO3166-2`` county
   areas (see ``regions.py``); returns ``name``, ``name:de``, ``wikidata`` and
   coordinates.  The spatial join ("which city belongs to which region") is done
   inside Overpass — no point-in-polygon needed.  Reuses ``OverpassGateway``.
2. **Wikidata** — one ``wbgetentities`` call (``WikidataGateway.names``) resolves
   an OSM ``wikidata`` QID to its de.wikivoyage article title (for the link /
   summary), its de.wikipedia title and its German label (for the name).
3. **de.wikivoyage MediaWiki API** — ``prop=extracts`` returns the intro summary;
   falls back to ``name:de`` / ``name`` when no QID sitelink is found.

The German display name follows the shared priority OSM ``name:de`` >
de.wikipedia title > Wikidata label (see ``enrich.resolve_name_de``); WikiVoyage
supplies only the article URL and summary.

Output (EPSG:4326)
------------------
  data/processed/wikivoyage_cities.geojson   one point per city with a German article
  data/raw/osm_ro_cities.json                raw Overpass cache

Attribution (required when redistributing)
-------------------------------------------
* Geometry / tags: OpenStreetMap via Overpass API.
  © OpenStreetMap contributors, ODbL 1.0.
* Summaries / links: Wikivoyage / Wikidata.
  Texts CC BY-SA 3.0; Wikidata CC0.

Usage
-----
  uv run reiseplan-cli fetch-wikivoyage            # fetch online + cache
  uv run reiseplan-cli fetch-wikivoyage --offline  # rebuild from cache
"""

from __future__ import annotations

import json
import time
import urllib.parse
from pathlib import Path

from . import geo
from .enrich import resolve_name_de
from .http import REQUEST_PAUSE_S, chunked, get_json
from .paths import ROOT
from .regions import HISTORICAL_REGIONS
from .repository import feature_collection, write_json
from .result import Err, Ok, Result
from .wikidata import WikidataGateway, WikidataNames

WIKIVOYAGE_API = "https://de.wikivoyage.org/w/api.php"
WIKIVOYAGE_WIKI = "https://de.wikivoyage.org/wiki/"

RAW_CACHE_PATH = ROOT / "data" / "raw" / "osm_ro_cities.json"
OUT_PATH = ROOT / "data" / "processed" / "wikivoyage_cities.geojson"

# MediaWiki extracts accept ≤ 20 titles per request.
_EXTRACT_BATCH = 20
# Trim intro so GeoJSON / map-tip stays compact.
_SUMMARY_MAXLEN = 600


# ---------------------------------------------------------------------------
# Stage 1: Overpass — places per historical region
# ---------------------------------------------------------------------------

def build_region_query(iso_codes: tuple[str, ...]) -> str:
    """Return an Overpass-QL query for all named cities/towns in the given counties.

    The county areas are unioned into a single set so one request covers the
    whole region (one round-trip per region, not per county).  ``out tags center``
    returns tags plus coordinates; ``center`` is the fallback for the rare
    way/relation-mapped settlements (mirrors the StationIndex pattern).
    """
    areas = " ".join(f'area["ISO3166-2"="{code}"];' for code in iso_codes)
    return (
        "[out:json][timeout:180];\n"
        f"({areas})->.region;\n"
        'node["place"~"^(city|town)$"]["name"](area.region);\n'
        "out tags center;\n"
    )


def load_or_fetch_places(offline: bool) -> Result[dict[str, dict]]:
    """Return Overpass responses keyed by region — from cache (offline) or API.

    Online: one request per region, full result cached as
    ``{region: overpass_response}``.  A single failing request returns Err and
    aborts — writing a half-built dataset would silently corrupt the GeoJSON.
    """
    if offline:
        if not RAW_CACHE_PATH.is_file():
            return Err(f"--offline but cache is missing: {RAW_CACHE_PATH}")
        print(f"[offline] reading raw cache: {RAW_CACHE_PATH}")
        try:
            return Ok(json.loads(RAW_CACHE_PATH.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            return Err(f"cache file is not valid JSON: {exc}")

    from .overpass import OverpassGateway

    by_region: dict[str, dict] = {}
    for region, codes in HISTORICAL_REGIONS.items():
        print(f"[online]  Overpass · {region} ({len(codes)} counties) …")
        result = OverpassGateway(query=build_region_query(codes)).fetch()
        if isinstance(result, Err):
            return Err(f"{region}: {result.message}")
        by_region[region] = result.value
        time.sleep(REQUEST_PAUSE_S)

    RAW_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_CACHE_PATH.write_text(
        json.dumps(by_region, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    total = sum(len(r.get("elements", [])) for r in by_region.values())
    print(f"[online]  {total} places cached → {RAW_CACHE_PATH}")
    return Ok(by_region)


def parse_places(by_region: dict[str, dict]) -> list[dict]:
    """Flatten Overpass responses into a list of place records.

    Each record: ``{name, name_de, region, kind, population, wikidata, lon, lat}``.
    Deduplication is by Wikidata QID (when present) or ``(name, region)`` — the
    same city does not appear in disjoint region areas, but node+relation
    duplicates are merged this way.
    """
    seen: set[str] = set()
    places: list[dict] = []
    for region, response in by_region.items():
        for el in response.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name")
            if not name:
                continue
            center = el.get("center", {})
            # Explicit ``in`` checks — lat/lon == 0.0 is valid (mirrors overpass.py).
            lat = el["lat"] if "lat" in el else center.get("lat")
            lon = el["lon"] if "lon" in el else center.get("lon")
            if lat is None or lon is None:
                continue

            wikidata = tags.get("wikidata")
            key = wikidata or f"{name}@{region}"
            if key in seen:
                continue
            seen.add(key)

            places.append({
                "name": name,
                "name_de": tags.get("name:de"),
                "region": region,
                "kind": tags.get("place"),
                "population": geo.parse_population(tags.get("population", "")),
                "wikidata": wikidata,
                "lon": float(lon),
                "lat": float(lat),
            })
    return places


# ---------------------------------------------------------------------------
# Stage 2: Wikidata QID → de.wikivoyage article title
# ---------------------------------------------------------------------------
#
# Resolved via ``wikidata.WikidataGateway.names`` (dewikivoyage sitelink) — see
# ``_resolve_titles`` below.


# ---------------------------------------------------------------------------
# Stage 3: de.wikivoyage article → intro extract
# ---------------------------------------------------------------------------

class WikivoyageGateway:
    """Fetches intro summaries from de.wikivoyage and checks article existence."""

    def extracts(self, titles: list[str]) -> dict[str, str]:
        """Return ``{requested_title: summary}`` for titles that exist.

        Batched (≤ 20 titles per request, limit of the ``extracts`` extension).
        ``redirects=1`` follows redirects; the ``normalized``/``redirects``
        mapping in the response is chained back to the originally requested title
        so the caller can look up its records.  Missing articles simply do not
        appear in the result.
        """
        out: dict[str, str] = {}
        for batch in chunked(titles, _EXTRACT_BATCH):
            result = get_json(WIKIVOYAGE_API, {
                "action": "query",
                "prop": "extracts",
                "exintro": "1",
                "explaintext": "1",
                "redirects": "1",
                "titles": "|".join(batch),
                "format": "json",
            })
            if isinstance(result, Err):
                print(f"  ! WikiVoyage batch skipped: {result.message}")
                continue
            query = result.value.get("query", {})
            resolved_to_requested = _requested_title_map(query, batch)
            for page in query.get("pages", {}).values():
                if "missing" in page:
                    continue
                extract = (page.get("extract") or "").strip()
                if not extract:
                    continue
                requested = resolved_to_requested.get(page["title"], page["title"])
                out[requested] = _trim_summary(extract)
            time.sleep(REQUEST_PAUSE_S)
        return out


def _requested_title_map(query: dict, requested: list[str]) -> dict[str, str]:
    """Map each page's final title back to the originally requested title.

    MediaWiki reports normalisation and redirects as separate lists; both are
    followed to a fixed point so a multi-hop chain (``A → B → C``) maps the final
    ``page["title"]`` back to what was asked for.  A ``seen`` guard breaks any
    cyclic redirect rather than looping forever.
    """
    norm = {n["from"]: n["to"] for n in query.get("normalized", [])}
    redir = {r["from"]: r["to"] for r in query.get("redirects", [])}
    result: dict[str, str] = {}
    for req in requested:
        final = norm.get(req, req)
        seen = {final}
        while final in redir:
            final = redir[final]
            if final in seen:
                break  # cyclic redirect — stop following
            seen.add(final)
        result[final] = req
    return result


def _trim_summary(text: str) -> str:
    """Collapse whitespace and trim to ``_SUMMARY_MAXLEN`` characters."""
    collapsed = " ".join(text.split())
    if len(collapsed) <= _SUMMARY_MAXLEN:
        return collapsed
    return collapsed[:_SUMMARY_MAXLEN].rstrip() + " …"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _resolve_titles(
    places: list[dict], names: dict[str, WikidataNames]
) -> dict[int, str]:
    """Map each place (by index) to its de.wikivoyage article title.

    Primary path: Wikidata QID → ``dewikivoyage`` sitelink (exact match — the
    article carries the WikiVoyage links and travel summary).
    Fallback: German OSM name (``name:de``) or plain ``name`` — checked against
    actual article existence in stage 3; cities without an article are dropped.
    """
    titles: dict[int, str] = {}
    for i, place in enumerate(places):
        qid = place.get("wikidata")
        entity = names.get(qid) if qid else None
        if entity and entity.wikivoyage_de:
            titles[i] = entity.wikivoyage_de
        else:
            titles[i] = place.get("name_de") or place["name"]
    return titles


def _to_feature(
    place: dict, title: str, summary: str, names: dict[str, WikidataNames]
) -> dict:
    """Build a GeoJSON Point feature for a city that has a German WikiVoyage article.

    The German name follows the shared priority (OSM ``name:de`` > de.wikipedia
    title > Wikidata label) via ``resolve_name_de``; WikiVoyage itself only
    supplies the article URL and summary, not the name.
    """
    props = {
        "name": place["name"],
        "region": place["region"],
        "wikivoyage_url": WIKIVOYAGE_WIKI + urllib.parse.quote(title.replace(" ", "_")),
        "summary": summary,
    }
    name_de, _ = resolve_name_de(
        place["name"],
        {"name:de": place.get("name_de"), "wikidata": place.get("wikidata")},
        names,
    )
    if name_de:
        props["name_de"] = name_de
    if place.get("kind"):
        props["kind"] = place["kind"]
    if place.get("population") is not None:
        props["population"] = place["population"]
    if place.get("wikidata"):
        props["wikidata"] = place["wikidata"]
    return {
        "type": "Feature",
        "properties": props,
        "geometry": {"type": "Point", "coordinates": [place["lon"], place["lat"]]},
    }


def run(offline: bool = False) -> None:
    """End-to-end: Overpass → Wikidata → de.wikivoyage → GeoJSON."""
    by_region = load_or_fetch_places(offline).unwrap_or_exit()
    places = parse_places(by_region)
    print(f"[index]   {len(places)} places from Overpass across {len(by_region)} regions.")

    qids = [p["wikidata"] for p in places if p.get("wikidata")]
    names = WikidataGateway().names(qids) if qids else {}

    titles = _resolve_titles(places, names)
    summaries = WikivoyageGateway().extracts(sorted(set(titles.values())))

    features: list[dict] = []
    per_region: dict[str, int] = {}
    for i, place in enumerate(places):
        title = titles[i]
        if title not in summaries:
            continue  # no German WikiVoyage article → excluded (the "only" filter)
        features.append(_to_feature(place, title, summaries[title], names))
        per_region[place["region"]] = per_region.get(place["region"], 0) + 1

    write_json(OUT_PATH, feature_collection("wikivoyage_cities", features))

    skipped = len(places) - len(features)
    print(f"  → {OUT_PATH.relative_to(ROOT)} ({len(features)} cities with German article)")
    for region in HISTORICAL_REGIONS:
        if per_region.get(region):
            print(f"      · {region}: {per_region[region]}")
    print(f"  ({skipped} places skipped — no German WikiVoyage article)")
    print("[done]    Rebuild style? → python qgis/styles/build_marker_styles.py")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Rebuild from data/raw/osm_ro_cities.json only (no network).",
    )
    run(parser.parse_args().offline)


if __name__ == "__main__":
    main()
