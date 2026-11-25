"""Data sources: streaming readers that never load the whole file."""

from collections.abc import Iterable, Iterator
from itertools import chain, count
from pathlib import Path


def read_lines(path: Path) -> Iterator[str]:
    """Yield the lines of a file one by one (streaming reader)."""
    with path.open("r", encoding="utf-8", newline="") as file:
        yield from file


def read_many(paths: Iterable[Path]) -> Iterator[str]:
    """Read several files as one stream (itertools.chain).

    The header line of every file except the first one is skipped.
    """
    streams = []
    for number, path in enumerate(paths):
        lines = read_lines(path)
        if number > 0:
            next(lines, None)  # skip repeated header
        streams.append(lines)
    yield from chain.from_iterable(streams)


def clean_lines(lines: Iterable[str]) -> Iterator[str]:
    """Strip whitespace and drop empty lines and comments."""
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            yield line


def employee_ids(start: int = 1) -> Iterator[int]:
    """Infinite generator of ids; must be limited with islice()."""
    yield from count(start)
