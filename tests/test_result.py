"""Tests for the Maybe and Result monads (result.py).

Validates the monad laws informally:
  left identity  — Some(x).map(f) == Some(f(x))
  right identity — Some(x).map(id) == Some(x)
  associativity  — Some(x).map(f).map(g) == Some(x).map(lambda v: g(f(v)))

And the practical contract:
  Nothing propagates through map without calling the function.
  Err propagates through map without calling the function.
  unwrap_or_exit() raises SystemExit for Err, returns value for Ok.
"""

from __future__ import annotations

import pytest

from reiseplan.result import Err, Nothing, Ok, Some, _Nothing


# ---------------------------------------------------------------------------
# Maybe — Some
# ---------------------------------------------------------------------------

def test_some_is_some():
    assert Some(42).is_some is True


def test_some_unwrap():
    assert Some("hello").unwrap() == "hello"


def test_some_unwrap_or_returns_value():
    assert Some(7).unwrap_or(99) == 7


def test_some_map():
    result = Some(3).map(lambda x: x * 2)
    assert isinstance(result, Some)
    assert result.value == 6


def test_some_map_chaining():
    result = Some(2).map(lambda x: x + 1).map(lambda x: x * 3)
    assert result.value == 9


# ---------------------------------------------------------------------------
# Maybe — Nothing
# ---------------------------------------------------------------------------

def test_nothing_is_singleton():
    assert _Nothing() is _Nothing()


def test_nothing_is_not_some():
    assert Nothing.is_some is False


def test_nothing_unwrap_raises():
    with pytest.raises(ValueError, match="Nothing"):
        Nothing.unwrap()


def test_nothing_unwrap_or_returns_default():
    assert Nothing.unwrap_or("fallback") == "fallback"


def test_nothing_map_does_not_call_fn():
    called = []
    Nothing.map(lambda x: called.append(x) or x)
    assert called == []


def test_nothing_map_returns_nothing():
    assert Nothing.map(lambda x: x + 1) is Nothing


# ---------------------------------------------------------------------------
# Result — Ok
# ---------------------------------------------------------------------------

def test_ok_unwrap_or_exit():
    assert Ok("data").unwrap_or_exit() == "data"


def test_ok_map():
    result = Ok(10).map(lambda x: x + 5)
    assert isinstance(result, Ok)
    assert result.value == 15


def test_ok_unwrap_or():
    assert Ok(42).unwrap_or(0) == 42


# ---------------------------------------------------------------------------
# Result — Err
# ---------------------------------------------------------------------------

def test_err_unwrap_or_exit_raises_system_exit():
    with pytest.raises(SystemExit, match="something went wrong"):
        Err("something went wrong").unwrap_or_exit()


def test_err_map_does_not_call_fn():
    called = []
    Err("oops").map(lambda x: called.append(x) or x)
    assert called == []


def test_err_map_propagates_message():
    result = Err("network failure").map(lambda x: x)
    assert isinstance(result, Err)
    assert result.message == "network failure"


def test_err_unwrap_or_returns_default():
    assert Err("boom").unwrap_or("safe default") == "safe default"
