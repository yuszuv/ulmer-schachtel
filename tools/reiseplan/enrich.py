"""German-name enrichment — shared by all thematic fetchers.

German names come, in priority order, from:
  1. OSM ``name:de``      — hand-curated, local; always wins when present.
  2. de.wikipedia title   — authoritative German exonym (e.g. "Hermannstadt").
  3. Wikidata ``de`` label — fallback when there is no German Wikipedia article.

The Wikidata/Wikipedia lookups are cached in two additive files next to each
other (``cache_path`` is the label file; the Wikipedia file sits beside it):
  - ``wikidata_de_labels.json``    qid → German label
  - ``wikidata_de_wikipedia.json`` qid → de.wikipedia title, or ``null`` ("checked,
    no article") so a QID without an article is not re-fetched every run.
Both are committed (CC0, small, required for deterministic ``--offline`` rebuilds)
and additive across themes: each fetch only requests QIDs not seen before.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .wikidata import WikidataGateway, WikidataNames

# Trailing "(…)" disambiguator on a Wikipedia title — dropped to get a clean name.
_DISAMBIGUATOR = re.compile(r"\s*\([^()]*\)\s*$")

# The Wikipedia-title cache lives beside the label cache passed by the caller.
_WIKIPEDIA_CACHE_NAME = "wikidata_de_wikipedia.json"


def _clean_title(title: str | None) -> str | None:
    """Strip a trailing parenthetical disambiguator from a Wikipedia title.

    ``"Bistrița (Stadt)"`` → ``"Bistrița"``.  Returns ``None`` for empty input or
    a title that is nothing but a disambiguator.
    """
    if not title:
        return None
    return _DISAMBIGUATOR.sub("", title).strip() or None


def resolve_name_de(
    name: str | None,
    tags: dict,
    wikidata: dict[str, WikidataNames],
) -> tuple[str | None, str | None]:
    """Return ``(name_de, source)`` for a feature.

    Priority: OSM ``name:de`` > de.wikipedia title > Wikidata ``de`` label.  The
    German name is only returned when it differs from ``name`` — an identical
    value adds nothing to ``coalesce("name_de","name")`` and would only bloat the
    GeoJSON.  ``source`` is ``"osm"`` / ``"wikipedia"`` / ``"wikidata"`` / ``None``.
    """
    osm_de = tags.get("name:de")
    if osm_de:
        return (osm_de, "osm") if osm_de != name else (None, None)

    qid = tags.get("wikidata")
    if qid:
        entity = wikidata.get(qid)
        if entity:
            wiki = _clean_title(entity.wikipedia_de)
            if wiki and wiki != name:
                return wiki, "wikipedia"
            if entity.label_de and entity.label_de != name:
                return entity.label_de, "wikidata"
    return None, None


def _qids_needing_labels(elements: list[dict]) -> list[str]:
    """Distinct ``wikidata`` QIDs of named elements that lack an OSM ``name:de``.

    Only these need a Wikidata lookup; features with an existing OSM German name
    already have the better (hand-curated, local) value.  Sorted for
    deterministic request batching and reproducible cache diffs.
    """
    qids: set[str] = set()
    for el in elements:
        tags = el.get("tags", {})
        if not tags.get("name") or tags.get("name:de"):
            continue
        qid = tags.get("wikidata")
        if qid:
            qids.add(qid)
    return sorted(qids)


def _load_cache(path: Path) -> dict:
    """Load a JSON cache file, returning ``{}`` on absence or corruption."""
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"[wikidata] Cache beschädigt, wird neu aufgebaut: {path}")
        return {}


def _write_cache(path: Path, data: dict) -> None:
    """Write a JSON cache file, keys sorted for reproducible diffs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def german_names(
    elements: list[dict],
    offline: bool,
    cache_path: Path,
) -> dict[str, WikidataNames]:
    """Return a ``{qid: WikidataNames}`` map, fetching missing names from Wikidata.

    The Wikipedia cache is the source of truth for "already fetched": a QID is a
    key there (value possibly ``null``) once looked up, so QIDs without a German
    article are not re-requested.  Offline mode never hits the network — it uses
    whatever the committed caches hold and warns about any gaps.

    Only hands back entries for QIDs needed by this particular element list, so
    callers get a focused map rather than the full (potentially large) cache.
    """
    needed = _qids_needing_labels(elements)
    wiki_path = cache_path.with_name(_WIKIPEDIA_CACHE_NAME)

    labels: dict[str, str] = _load_cache(cache_path)
    wikipedia: dict[str, str | None] = _load_cache(wiki_path)

    missing = [q for q in needed if q not in wikipedia]

    if missing and offline:
        print(f"[wikidata] offline: {len(missing)} QIDs ohne Cache-Eintrag (übersprungen)")
    elif missing:
        print(f"[wikidata] {len(needed)} QIDs benötigt, {len(missing)} neu von Wikidata holen …")
        fetched = WikidataGateway().names(missing)
        for qid in missing:
            entry = fetched.get(qid)
            # Always mark the QID as checked in the Wikipedia cache (null = no
            # article) so it is not re-fetched; only store a label when present.
            wikipedia[qid] = entry.wikipedia_de if entry else None
            if entry and entry.label_de:
                labels[qid] = entry.label_de
        _write_cache(cache_path, labels)
        _write_cache(wiki_path, wikipedia)
        resolved = sum(1 for q in missing if wikipedia.get(q) or labels.get(q))
        print(f"[wikidata] {resolved} Namen geholt → {cache_path.name} / {wiki_path.name}")
    else:
        print(f"[wikidata] {len(needed)} QIDs benötigt, alle im Cache")

    return {
        q: WikidataNames(
            label_de=labels.get(q),
            wikipedia_de=wikipedia.get(q),
            wikivoyage_de=None,
        )
        for q in needed
        if q in labels or q in wikipedia
    }
