"""Small generic helpers: TypeVar, constrained TypeVar and Result[T]."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
Number = TypeVar("Number", int, float)  # constrained TypeVar


def first(items: Sequence[T]) -> T | None:
    """Keeps the link between input and output type."""
    return items[0] if items else None


def clamp(value: Number, low: Number, high: Number) -> Number:
    """Works for int and float, but never mixes them."""
    return max(low, min(value, high))


@dataclass(frozen=True)
class Result(Generic[T]):
    """Outcome of a service operation: value or error message."""

    value: T | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __bool__(self) -> bool:
        return self.success
