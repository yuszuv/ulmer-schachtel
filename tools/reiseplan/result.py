"""Maybe and Result monads — minimal functional error-handling.

Pattern 2: used in exactly two places where errors are expected and recoverable
at the *call site*:

  OverpassGateway.fetch()     → Result[dict]
      Network / JSON failures become Err(message) instead of raising deep
      inside the gateway. The application boundary in ingest.main() unpacks
      via .unwrap_or_exit(), which translates Err → SystemExit.

  StationIndex.resolve()      → Maybe[Coordinate]
      A name-lookup miss is a legitimate outcome (stop not in OSM), not an
      exception. Callers handle Nothing explicitly (skip the stop, log it).

Design rule: monads are unwrapped at the outermost layer (CLI / use-case),
never silently swallowed. This keeps inner logic exception-free while
preserving the "loud failure" behaviour at the top.

  Result[T]  Ok(value) | Err(message)   — for operations that can fail
  Maybe[T]   Some(value) | Nothing       — for values that may be absent

Both types are read-only (frozen dataclasses / singleton).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")


# ---------------------------------------------------------------------------
# Maybe
# ---------------------------------------------------------------------------

class Maybe(Generic[T]):
    """A value that is either present (Some) or absent (Nothing)."""

    def map(self, fn: Callable[[T], U]) -> "Maybe[U]":
        raise NotImplementedError

    def unwrap_or(self, default: T) -> T:
        raise NotImplementedError

    def unwrap(self) -> T:
        """Return the value or raise ValueError — only call after .is_some."""
        raise NotImplementedError

    @property
    def is_some(self) -> bool:
        raise NotImplementedError


@dataclass(frozen=True)
class Some(Maybe[T]):
    """A present value."""

    value: T

    def map(self, fn: Callable[[T], U]) -> "Some[U]":
        return Some(fn(self.value))

    def unwrap_or(self, default: T) -> T:
        return self.value

    def unwrap(self) -> T:
        return self.value

    @property
    def is_some(self) -> bool:
        return True


class _Nothing(Maybe):
    """Singleton absence — represents a missing value."""

    _instance: "_Nothing | None" = None

    def __new__(cls) -> "_Nothing":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def map(self, fn: Callable) -> "_Nothing":
        return self

    def unwrap_or(self, default):
        return default

    def unwrap(self):
        raise ValueError("Nothing.unwrap() — check .is_some before unwrapping")

    @property
    def is_some(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "Nothing"


Nothing: Maybe = _Nothing()


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

class Result(Generic[T]):
    """A computation that either succeeded (Ok) or failed (Err)."""

    def map(self, fn: Callable[[T], U]) -> "Result[U]":
        raise NotImplementedError

    def unwrap_or(self, default: T) -> T:
        raise NotImplementedError

    def unwrap_or_exit(self) -> T:
        """Return the value, or raise SystemExit with the error message."""
        raise NotImplementedError


@dataclass(frozen=True)
class Ok(Result[T]):
    """A successful result."""

    value: T

    def map(self, fn: Callable[[T], U]) -> "Ok[U]":
        return Ok(fn(self.value))

    def unwrap_or(self, default: T) -> T:
        return self.value

    def unwrap_or_exit(self) -> T:
        return self.value


@dataclass(frozen=True)
class Err(Result[T]):
    """A failed result carrying an error message."""

    message: str

    def map(self, fn: Callable) -> "Err":
        return self   # propagate the error unchanged

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_exit(self) -> T:
        raise SystemExit(self.message)
