"""Tests for the Command-Registry (cli.py).

Verifies that:
- All expected commands are registered in REGISTRY.
- build_parser() produces a working ArgumentParser.
- --json flag is present on data-inspection commands and absent on build commands.
- Positional / optional arguments are wired up correctly.
"""

from __future__ import annotations

import pytest

from reiseplan.cli import REGISTRY, build_parser

# Commands that should exist after module import.
_EXPECTED_COMMANDS = {
    "list-routes",
    "list-categories",
    "list-destinations",
    "overview",
    "timetable",
    "show-route",
    "fetch-wikivoyage",
    "build-gpkg",
    "build-qfield",
}

# Commands that support --json.
_JSON_COMMANDS = {
    "list-routes", "list-categories", "list-destinations",
    "overview", "timetable", "show-route",
}

# Commands without --json.
_BUILD_COMMANDS = {"build-gpkg", "build-qfield"}


# ---------------------------------------------------------------------------
# Registry contents
# ---------------------------------------------------------------------------

def test_all_expected_commands_registered():
    registered = {spec.name for spec in REGISTRY}
    assert _EXPECTED_COMMANDS <= registered


def test_json_commands_have_flag():
    for spec in REGISTRY:
        if spec.name in _JSON_COMMANDS:
            assert spec.has_json, f"{spec.name} should have --json"


def test_build_commands_have_no_json_flag():
    for spec in REGISTRY:
        if spec.name in _BUILD_COMMANDS:
            assert not spec.has_json, f"{spec.name} should NOT have --json"


def test_show_route_has_route_id_arg():
    spec = next(s for s in REGISTRY if s.name == "show-route")
    arg_flags = [a.flags for a in spec.args]
    assert ["route_id"] in arg_flags


def test_list_destinations_has_category_arg():
    spec = next(s for s in REGISTRY if s.name == "list-destinations")
    arg_flags = [a.flags for a in spec.args]
    assert ["--category"] in arg_flags


def test_build_qfield_has_out_arg():
    spec = next(s for s in REGISTRY if s.name == "build-qfield")
    arg_flags = [a.flags for a in spec.args]
    assert ["--out"] in arg_flags


# ---------------------------------------------------------------------------
# Parser functionality
# ---------------------------------------------------------------------------

def test_parser_builds_without_error():
    parser = build_parser()
    assert parser is not None


def test_parser_list_routes_json():
    parser = build_parser()
    args = parser.parse_args(["list-routes", "--json"])
    assert args.json is True


def test_parser_show_route_positional():
    parser = build_parser()
    args = parser.parse_args(["show-route", "M300"])
    assert args.route_id == "M300"


def test_parser_list_destinations_category():
    parser = build_parser()
    args = parser.parse_args(["list-destinations", "--category", "dracula_city"])
    assert args.category == "dracula_city"


def test_parser_build_qfield_out():
    parser = build_parser()
    args = parser.parse_args(["build-qfield", "--out", "/tmp/test"])
    assert args.out == "/tmp/test"


def test_parser_build_qfield_no_json():
    """build-qfield must not accept --json."""
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["build-qfield", "--json"])
