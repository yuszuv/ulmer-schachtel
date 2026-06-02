"""Wikidata access — shared JSON GET, chunking, and German-label lookup.

Two consumers share this module:

* ``wikivoyage.py`` resolves OSM ``wikidata`` QIDs to de.wikivoyage sitelinks.
* ``fetch_natural.py`` enriches natural features with German names
  (``wbgetentities`` labels) where OSM has no ``name:de`` tag.

``get_json`` and ``chunked`` are the generic HTTP-JSON / batching helpers used
across the Wikimedia APIs; they previously lived (privately) in ``wikivoyage``
and were promoted here so both fetchers reuse one implementation.

Attribution
-----------
Wikidata content is CC0 — no attribution legally required, but credited in the
dataset sidecars for transparency.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .overpass import USER_AGENT
from .result import Err, Ok, Result

WIKIDATA_API = "https://www.wikidata.org/w/api.php"

# wbgetentities accepts ≤ 50 ids per request.
_WIKIDATA_BATCH = 50
# Pause between batched API calls to be polite to public infrastructure.
_REQUEST_PAUSE_S = 0.5


def get_json(url: str, params: dict[str, str]) -> Result[dict]:
    """GET ``url?params``, parse JSON, return Ok(dict) or Err(message)."""
    full = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            payload = resp.read()
    except urllib.error.HTTPError as exc:
        return Err(f"HTTP {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        return Err(f"unreachable: {exc.reason}")
    try:
        return Ok(json.loads(payload))
    except json.JSONDecodeError as exc:
        return Err(f"invalid JSON: {exc}")


def chunked(seq: list, size: int):
    """Yield consecutive ``size``-length slices of ``seq``."""
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


class WikidataLabelGateway:
    """Resolves Wikidata QIDs to their German (``de``) label."""

    def labels(self, qids: list[str]) -> dict[str, str]:
        """Return ``{qid: german_label}`` for all QIDs that have a ``de`` label.

        Batched (≤ 50 IDs per request), ``props=labels&languages=de`` keeps the
        payload minimal.  Failed batches are skipped with a warning — a missing
        German label is expected for many features, not a crash.  QIDs without a
        ``de`` label simply do not appear in the result.
        """
        out: dict[str, str] = {}
        for batch in chunked(qids, _WIKIDATA_BATCH):
            result = get_json(WIKIDATA_API, {
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "labels",
                "languages": "de",
                "format": "json",
            })
            if isinstance(result, Err):
                print(f"  ! Wikidata batch skipped: {result.message}")
                continue
            entities = result.value.get("entities", {})
            for qid, entity in entities.items():
                label = entity.get("labels", {}).get("de", {}).get("value")
                if label:
                    out[qid] = label
            time.sleep(_REQUEST_PAUSE_S)
        return out
