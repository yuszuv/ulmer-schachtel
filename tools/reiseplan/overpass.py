"""Overpass API gateway and station-name index.

Two responsibilities:

  OverpassGateway   — HTTP access to the Overpass API, returns Result[dict].
                      Network / JSON errors become Err(message) instead of
                      raising inside the gateway; the caller decides how to handle.

  StationIndex      — builds a name → Coordinate lookup from an Overpass response
                      and resolves Stop aliases, returning Maybe[Coordinate].
                      A lookup miss is Nothing (expected), not an exception.

CRS: all coordinates are WGS84 (EPSG:4326) as returned by Overpass.
GeoJSON output stays in 4326; the GPKG step reprojects to EPSG:3844 via ogr2ogr.
See tools/reiseplan/ingest.py and AGENTS.md for the full CRS rationale.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .domain import Coordinate, Stop
from .paths import ROOT
from .result import Err, Maybe, Nothing, Ok, Result, Some

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "reisefuehrer-dataintegration/0.1 (jan@sternprodukt.de)"

# Fetch all named rail stops in Romania in one request; local filtering happens
# in StationIndex.  One network call → offline rebuild via --offline flag.
OVERPASS_QUERY = """
[out:json][timeout:120];
area["ISO3166-1"="RO"][admin_level=2]->.ro;
node["railway"~"^(station|halt|stop)$"]["name"](area.ro);
out tags center;
"""

RAW_CACHE_PATH = ROOT / "data" / "raw" / "osm_ro_stations.json"

# Real track geometry per magistrală corridor (see load_or_fetch_rail).
RAIL_CACHE_PATH = ROOT / "data" / "raw" / "osm_ro_rail_ways.json"
_RAIL_REQUEST_PAUSE_S = 1.0  # politeness gap between corridor queries

# Higher-ranked types win on name collision (station beats halt beats stop).
_RAILWAY_RANK: dict[str, int] = {"station": 0, "halt": 1, "stop": 2}


def rail_ways_query(bbox: tuple[float, float, float, float]) -> str:
    """Overpass query for the running rails inside a bbox (south, west, north, east).

    ``["service"!~"."]`` keeps only ways *without* a ``service`` tag — i.e. it
    drops yards, sidings, spurs and crossovers, which would otherwise add detours
    to the routed line. ``out geom`` returns each way's full vertex list.
    """
    south, west, north, east = bbox
    return (
        "[out:json][timeout:180];\n"
        f'way["railway"="rail"]["service"!~"."]({south},{west},{north},{east});\n'
        "out geom;"
    )


# ---------------------------------------------------------------------------
# Gateway
# ---------------------------------------------------------------------------

class OverpassGateway:
    """HTTP gateway to the Overpass API.

    The Overpass query is injectable (default = the station query above) so the
    same gateway serves other use-cases — e.g. the WikiVoyage city fetch passes
    a per-county place query (see tools/reiseplan/wikivoyage.py).

    Returns Result[dict] so callers can handle failures at their own boundary
    instead of catching exceptions from deep inside urllib.
    """

    def __init__(self, url: str = OVERPASS_URL, query: str = OVERPASS_QUERY) -> None:
        self.url = url
        self.query = query

    def fetch(self) -> Result[dict]:
        """Query Overpass and return Ok(parsed_json) or Err(message)."""
        request = urllib.request.Request(
            self.url,
            data=urllib.parse.urlencode({"data": self.query}).encode("utf-8"),
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as resp:
                payload = resp.read()
        except urllib.error.HTTPError as exc:
            return Err(f"Overpass HTTP-Fehler {exc.code}: {exc.reason}")
        except urllib.error.URLError as exc:
            return Err(f"Overpass nicht erreichbar: {exc.reason}")

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            return Err(f"Overpass lieferte kein gültiges JSON: {exc}")

        if not data.get("elements"):
            return Err("Overpass-Antwort enthält keine Elemente – Abbruch.")
        return Ok(data)


def load_or_fetch(offline: bool) -> Result[dict]:
    """Return Overpass data from cache (offline) or from the API (online).

    Wraps both paths in Result so the caller (ingest.main) handles errors
    uniformly via .unwrap_or_exit().
    """
    if offline:
        if not RAW_CACHE_PATH.is_file():
            return Err(f"--offline, aber Cache fehlt: {RAW_CACHE_PATH}")
        print(f"[offline] lese Roh-Cache: {RAW_CACHE_PATH}")
        try:
            data = json.loads(RAW_CACHE_PATH.read_text(encoding="utf-8"))
            return Ok(data)
        except json.JSONDecodeError as exc:
            return Err(f"Cache-Datei kein gültiges JSON: {exc}")

    print("[online]  frage Overpass ab …")
    result = OverpassGateway().fetch()
    if isinstance(result, Ok):
        RAW_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        RAW_CACHE_PATH.write_text(
            json.dumps(result.value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            f"[online]  {len(result.value['elements'])} Bahn-Halte gecacht"
            f" → {RAW_CACHE_PATH}"
        )
    return result


def load_or_fetch_rail(
    offline: bool, corridors: dict[str, tuple[float, float, float, float]]
) -> Result[dict[str, dict]]:
    """Real rail-track geometry per magistrală, keyed by ref (e.g. ``"M300"``).

    ``corridors`` maps each ref to its bounding box (south, west, north, east),
    computed by the caller from the resolved station coordinates. One Overpass
    query per corridor (smaller, more reliable than a Romania-wide fetch) with a
    short pause between them; the combined result is cached as a single JSON so
    ``--offline`` can rebuild without the network — same model as load_or_fetch.

    Returns ``Ok({ref: overpass_json})`` or ``Err(message)`` (a failing corridor
    aborts the run loudly, consistent with Pattern 2 at the application boundary).
    """
    if offline:
        if not RAIL_CACHE_PATH.is_file():
            return Err(f"--offline, aber Gleis-Cache fehlt: {RAIL_CACHE_PATH}")
        print(f"[offline] lese Gleis-Cache: {RAIL_CACHE_PATH}")
        try:
            return Ok(json.loads(RAIL_CACHE_PATH.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            return Err(f"Gleis-Cache kein gültiges JSON: {exc}")

    print(f"[online]  frage Gleisgeometrie für {len(corridors)} Korridore ab …")
    collected: dict[str, dict] = {}
    for i, (ref, bbox) in enumerate(corridors.items()):
        if i:
            time.sleep(_RAIL_REQUEST_PAUSE_S)
        result = OverpassGateway(query=rail_ways_query(bbox)).fetch()
        if isinstance(result, Err):
            return Err(f"{ref}: {result.message}")
        ways = sum(1 for e in result.value["elements"] if e.get("type") == "way")
        print(f"[online]  {ref}: {ways} Gleis-Ways")
        collected[ref] = result.value

    RAIL_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAIL_CACHE_PATH.write_text(
        json.dumps(collected, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[online]  Gleisgeometrie gecacht → {RAIL_CACHE_PATH}")
    return Ok(collected)


# ---------------------------------------------------------------------------
# StationIndex
# ---------------------------------------------------------------------------

class StationIndex:
    """Immutable name → Coordinate lookup built from an Overpass response.

    On duplicate names the highest-ranked railway type wins
    (station > halt > stop).  Coordinates of exactly 0.0 are **valid** —
    they are kept, not treated as missing (null-island edge case).

    Usage:
        result = load_or_fetch(offline=False)
        index = StationIndex.from_overpass(result.unwrap_or_exit())
        coord = index.resolve(stop)   # Maybe[Coordinate]
        if coord.is_some:
            lon, lat = coord.unwrap().lon, coord.unwrap().lat
    """

    def __init__(self, data: dict[str, Coordinate]) -> None:
        self._data = data

    @classmethod
    def from_overpass(cls, overpass_data: dict) -> "StationIndex":
        """Build the index from a parsed Overpass JSON response."""
        best: dict[str, tuple[int, Coordinate]] = {}
        for el in overpass_data["elements"]:
            tags = el.get("tags", {})
            name = tags.get("name")
            if not name:
                continue
            center = el.get("center", {})
            # Use explicit ``in`` checks — lat/lon == 0.0 is valid and must
            # not be treated as missing, so we cannot use ``el.get("lat") or``.
            lat = el["lat"] if "lat" in el else center.get("lat")
            lon = el["lon"] if "lon" in el else center.get("lon")
            if lat is None or lon is None:
                continue
            rank = _RAILWAY_RANK.get(tags.get("railway", ""), 9)
            if name not in best or rank < best[name][0]:
                best[name] = (rank, Coordinate(lon=float(lon), lat=float(lat)))
        return cls({name: coord for name, (_, coord) in best.items()})

    def resolve(self, stop: Stop) -> Maybe[Coordinate]:
        """Look up a stop by its canonical name and aliases.

        Returns ``Some(Coordinate)`` on the first match, ``Nothing`` if no
        alias is found in the index — a legitimate outcome for stops not yet
        in OSM.
        """
        for candidate in stop.lookup_names():
            if candidate in self._data:
                return Some(self._data[candidate])
        return Nothing

    def __len__(self) -> int:
        return len(self._data)
