"""Custom iterator class and a recursive generator."""

from collections.abc import Iterable, Iterator
from typing import Any


class SalaryRange:
    """Iterable of salary levels: start, start + step, ... < stop.

    Every call of iter() returns a new independent iterator,
    so the object can be iterated many times.
    """

    def __init__(self, start: float, stop: float, step: float) -> None:
        if step <= 0:
            raise ValueError("step must be positive")
        self.start = start
        self.stop = stop
        self.step = step

    def __iter__(self) -> "SalaryRangeIterator":
        return SalaryRangeIterator(self.start, self.stop, self.step)


class SalaryRangeIterator:
    """Iterator over salary levels (one-shot object)."""

    def __init__(self, start: float, stop: float, step: float) -> None:
        self.current = start
        self.stop = stop
        self.step = step

    def __iter__(self) -> "SalaryRangeIterator":
        return self

    def __next__(self) -> float:
        if self.current >= self.stop:
            raise StopIteration
        value = self.current
        self.current += self.step
        return value


def flatten(values: Iterable[Any]) -> Iterator[Any]:
    """Recursive generator: flatten nested lists with yield from."""
    for value in values:
        if isinstance(value, list):
            yield from flatten(value)
        else:
            yield value
