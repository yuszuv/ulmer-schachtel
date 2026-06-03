"""Wikidata access — batched ``wbgetentities`` lookups.

Two consumers share this module:

* ``wikivoyage.py`` resolves OSM ``wikidata`` QIDs to de.wikivoyage sitelinks
  (the article for links / travel summaries) plus the authoritative German name.
* ``fetch_natural.py`` enriches natural features with German names where OSM has
  no ``name:de`` tag.

Both needs are satisfied by a single ``wbgetentities`` call asking for the
German label and the ``dewiki`` / ``dewikivoyage`` sitelinks at once; the per
entity result is bundled in ``WikidataNames``.  The generic batching shape lives
in ``_wbgetentities``; the HTTP-JSON helper lives in ``http.py``.

Attribution
-----------
Wikidata content is CC0 — no attribution legally required, but credited in the
dataset sidecars for transparency.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

from .http import REQUEST_PAUSE_S, chunked, get_json
from .result import Err

WIKIDATA_API = "https://www.wikidata.org/w/api.php"

# wbgetentities accepts ≤ 50 ids per request.
_WIKIDATA_BATCH = 50

T = TypeVar("T")


@dataclass(frozen=True)
class WikidataNames:
    """German name sources for one Wikidata entity.

    * ``label_de``     — the entity's German label (fallback name).
    * ``wikipedia_de`` — the de.wikipedia article title (authoritative German
      exonym, e.g. "Hermannstadt" for Sibiu).
    * ``wikivoyage_de`` — the de.wikivoyage article title (links / travel info).

    Any field is ``None`` when the entity has no such label / sitelink.
    """

    label_de: str | None
    wikipedia_de: str | None
    wikivoyage_de: str | None


def _wbgetentities(
    qids: list[str],
    *,
    props: str,
    extract: Callable[[dict], T | None],
    extra_params: dict[str, str] | None = None,
) -> dict[str, T]:
    """Return ``{qid: value}`` for every QID that yields a value via ``extract``.

    Batched (≤ 50 IDs per request); ``props`` / ``extra_params`` keep each
    response payload minimal.  Failed batches are skipped with a warning — a
    missing label or sitelink is the expected outcome for many features, not a
    crash, so such QIDs simply do not appear in the result.
    """
    out: dict[str, T] = {}
    for batch in chunked(qids, _WIKIDATA_BATCH):
        result = get_json(WIKIDATA_API, {
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": props,
            "format": "json",
            **(extra_params or {}),
        })
        if isinstance(result, Err):
            print(f"  ! Wikidata batch skipped: {result.message}")
            continue
        for qid, entity in result.value.get("entities", {}).items():
            value = extract(entity)
            if value is not None:
                out[qid] = value
        time.sleep(REQUEST_PAUSE_S)
    return out


def _extract_names(entity: dict) -> WikidataNames | None:
    """Pull German label + dewiki/dewikivoyage titles from a wbgetentities entity.

    Returns ``None`` when none of the three are present, so the QID is dropped
    from the result map (nothing useful to cache).
    """
    label = entity.get("labels", {}).get("de", {}).get("value")
    sitelinks = entity.get("sitelinks", {})
    wikipedia = sitelinks.get("dewiki", {}).get("title")
    wikivoyage = sitelinks.get("dewikivoyage", {}).get("title")
    if not (label or wikipedia or wikivoyage):
        return None
    return WikidataNames(
        label_de=label or None,
        wikipedia_de=wikipedia or None,
        wikivoyage_de=wikivoyage or None,
    )


class WikidataGateway:
    """Resolves Wikidata QIDs to their German names and sitelinks."""

    def names(self, qids: list[str]) -> dict[str, WikidataNames]:
        """Return ``{qid: WikidataNames}`` for QIDs with any German name/sitelink.

        One ``wbgetentities`` call fetches the German label and both the
        ``dewiki`` and ``dewikivoyage`` sitelinks, so callers needing names
        (enrich) and callers needing the WikiVoyage article (wikivoyage) share a
        single round-trip.
        """
        return _wbgetentities(
            qids,
            props="labels|sitelinks",
            extra_params={"languages": "de", "sitefilter": "dewiki|dewikivoyage"},
            extract=_extract_names,
        )
