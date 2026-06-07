"""Tests for the design-token parser in reiseplan.web.

Verifies that load_tokens() correctly reads the vendored colors_and_type.css,
resolves var(--x) aliases, and that the palette derivation matches expected
upstream token names.  No network access; uses the file at vendor/muris-atlas/.
"""

import pytest
from pathlib import Path
from reiseplan.web import (
    CATEGORY_TOKEN,
    TOKENS_CSS,
    VENDOR_DIR,
    load_tokens,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _skip_if_no_vendor() -> None:
    if not VENDOR_DIR.is_dir():
        pytest.skip("vendor/muris-atlas/ not present; run reiseplan-vendor-design first")


# ---------------------------------------------------------------------------
# Token parsing
# ---------------------------------------------------------------------------

def test_load_tokens_returns_dict():
    _skip_if_no_vendor()
    tokens = load_tokens()
    assert isinstance(tokens, dict)
    assert len(tokens) > 10, "Expected at least 10 token entries"


def test_load_tokens_paper():
    _skip_if_no_vendor()
    tokens = load_tokens()
    assert tokens["paper"] == "#f4e7d1", f"got {tokens.get('paper')!r}"


def test_load_tokens_hansa_rot():
    _skip_if_no_vendor()
    tokens = load_tokens()
    assert tokens["hansa-rot"] == "#e2566f", f"got {tokens.get('hansa-rot')!r}"


def test_load_tokens_ink():
    _skip_if_no_vendor()
    tokens = load_tokens()
    assert tokens["ink"] == "#3a2a26", f"got {tokens.get('ink')!r}"


def test_load_tokens_resolves_alias():
    """--bg is defined as var(--paper); resolved value must be the concrete hex."""
    _skip_if_no_vendor()
    tokens = load_tokens()
    # --bg: var(--paper) → should resolve to the paper hex, not the alias string
    assert tokens.get("bg") == tokens.get("paper"), (
        f"--bg alias not resolved: bg={tokens.get('bg')!r}, paper={tokens.get('paper')!r}"
    )


# ---------------------------------------------------------------------------
# Category token mapping
# ---------------------------------------------------------------------------

def test_category_tokens_present():
    _skip_if_no_vendor()
    tokens = load_tokens()
    for cat, tok in CATEGORY_TOKEN.items():
        assert tok in tokens, (
            f"CATEGORY_TOKEN[{cat!r}] = {tok!r} not found in vendor tokens"
        )


def test_dracula_city_maps_to_hansa_rot_hi():
    assert CATEGORY_TOKEN["dracula_city"] == "hansa-rot-hi"


def test_city_maps_to_ink():
    assert CATEGORY_TOKEN["city"] == "ink"


def test_danube_delta_maps_to_ink_soft():
    assert CATEGORY_TOKEN["danube_delta"] == "ink-soft"


# ---------------------------------------------------------------------------
# Vendor file existence
# ---------------------------------------------------------------------------

def test_vendor_css_exists():
    _skip_if_no_vendor()
    assert TOKENS_CSS.is_file(), f"Missing: {TOKENS_CSS}"


def test_vendor_tokens_json_exists():
    _skip_if_no_vendor()
    import json
    tokens_json = VENDOR_DIR / "figma" / "tokens.json"
    assert tokens_json.is_file(), f"Missing: {tokens_json}"
    data = json.loads(tokens_json.read_text())
    assert isinstance(data, dict)
