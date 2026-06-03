"""Shared HTTP/JSON access for the external-data fetchers.

Every fetcher in this package talks to a public API (Overpass, Wikidata,
de.wikivoyage).  The generic plumbing they all need — a polite User-Agent, a
JSON-GET that returns ``Result`` instead of raising, request batching, and a
politeness pause — lives here so the gateways stay thin and consistent.

Overpass-specific POST logic lives in ``overpass.py`` (it builds on the same
``USER_AGENT``); this module is the API-agnostic base.

Returning ``Result[dict]`` keeps network / JSON failures out of the inner
logic: callers unwrap at their own boundary instead of catching urllib errors
deep in a gateway.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .result import Err, Ok, Result

USER_AGENT = "reisefuehrer-dataintegration/0.1 (jan@sternprodukt.de)"

# Politeness pause (seconds) between batched calls to public infrastructure.
REQUEST_PAUSE_S = 0.5

# Transient-failure retry: public APIs (Overpass, Wikidata, MediaWiki) routinely
# return 429/5xx under load or drop connections.  A single such blip should not
# abort a whole multi-batch pipeline, so reads are retried with exponential
# backoff before the error is finally surfaced as an Err to the caller.
MAX_RETRIES = 3
RETRY_BACKOFF_S = 1.0
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _retryable(exc: Exception) -> bool:
    """True if ``exc`` is a transient failure worth retrying.

    Server overload / rate-limit (HTTP 429, 5xx) and plain network errors
    (``URLError`` without a status, socket ``TimeoutError``) are transient.  A
    4xx other than 429 is a permanent client error — never retried.
    """
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in _RETRYABLE_STATUS
    return isinstance(exc, (urllib.error.URLError, TimeoutError))


def read_url(request: urllib.request.Request, *, timeout: int,
             retries: int = MAX_RETRIES) -> bytes:
    """Open ``request`` and return the body, retrying transient failures.

    Retries ``_retryable`` errors with exponential backoff
    (``RETRY_BACKOFF_S * 2**attempt``); re-raises the last exception once the
    retries are exhausted or for a non-retryable error.  Callers keep their own
    ``except`` block to translate that final exception into a domain ``Err``.
    Note ``HTTPError`` subclasses ``URLError``, so the ``except`` catches both;
    ``_retryable`` decides which actually warrants another attempt.
    """
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt >= retries or not _retryable(exc):
                raise
            delay = RETRY_BACKOFF_S * 2 ** attempt
            print(f"  ↻ retry {attempt + 1}/{retries} nach {delay:.0f}s ({exc})")
            time.sleep(delay)
    raise AssertionError("unreachable")  # loop either returns or raises


def get_json(url: str, params: dict[str, str]) -> Result[dict]:
    """GET ``url?params``, parse JSON, return Ok(dict) or Err(message)."""
    full = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
    try:
        payload = read_url(request, timeout=60)
    except urllib.error.HTTPError as exc:
        return Err(f"HTTP {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        return Err(f"unreachable: {exc.reason}")
    except TimeoutError as exc:
        return Err(f"timeout: {exc}")
    try:
        return Ok(json.loads(payload))
    except json.JSONDecodeError as exc:
        return Err(f"invalid JSON: {exc}")


def chunked(seq: list, size: int):
    """Yield consecutive ``size``-length slices of ``seq`` (API batching)."""
    for i in range(0, len(seq), size):
        yield seq[i:i + size]
