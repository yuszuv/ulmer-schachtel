"""Tests for the HTTP retry helper — no real network.

Coverage:
  http._retryable   transient (429/5xx, URLError, TimeoutError) vs permanent (4xx)
  http.read_url     retries transient failures with backoff, re-raises otherwise
"""

from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from reiseplan import http


# ---------------------------------------------------------------------------
# _retryable classification
# ---------------------------------------------------------------------------

def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x", code, "msg", hdrs=None, fp=None)


@pytest.mark.parametrize("code", sorted(http._RETRYABLE_STATUS))
def test_retryable_server_errors(code):
    assert http._retryable(_http_error(code)) is True


@pytest.mark.parametrize("code", [400, 401, 403, 404, 410])
def test_non_retryable_client_errors(code):
    assert http._retryable(_http_error(code)) is False


def test_retryable_network_and_timeout():
    assert http._retryable(urllib.error.URLError("connection reset")) is True
    assert http._retryable(TimeoutError("slow")) is True


# ---------------------------------------------------------------------------
# read_url — retry loop
# ---------------------------------------------------------------------------

class _FakeResponse:
    """Minimal context-manager stand-in for an urlopen response."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._body


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    """Never actually sleep during backoff."""
    monkeypatch.setattr(http.time, "sleep", lambda _s: None)


def _patch_urlopen(monkeypatch, outcomes):
    """Make urlopen yield each outcome in turn (raise exceptions, return responses)."""
    it = iter(outcomes)

    def fake_urlopen(request, timeout):
        outcome = next(it)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(http.urllib.request, "urlopen", fake_urlopen)


def _request() -> urllib.request.Request:
    return urllib.request.Request("http://example.test")


def test_read_url_succeeds_first_try(monkeypatch):
    _patch_urlopen(monkeypatch, [_FakeResponse(b"ok")])
    assert http.read_url(_request(), timeout=5) == b"ok"


def test_read_url_retries_transient_then_succeeds(monkeypatch):
    _patch_urlopen(monkeypatch, [
        urllib.error.URLError("reset"),
        _http_error(503),
        _FakeResponse(b"done"),
    ])
    assert http.read_url(_request(), timeout=5, retries=3) == b"done"


def test_read_url_does_not_retry_client_error(monkeypatch):
    calls = {"n": 0}

    def fake_urlopen(request, timeout):
        calls["n"] += 1
        raise _http_error(404)

    monkeypatch.setattr(http.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(urllib.error.HTTPError):
        http.read_url(_request(), timeout=5, retries=3)
    assert calls["n"] == 1   # no retry on a permanent 404


def test_read_url_reraises_after_exhausting_retries(monkeypatch):
    _patch_urlopen(monkeypatch, [urllib.error.URLError("down")] * 4)
    with pytest.raises(urllib.error.URLError):
        http.read_url(_request(), timeout=5, retries=3)
