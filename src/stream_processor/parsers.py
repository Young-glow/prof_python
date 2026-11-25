"""Parsing stage: CSV lines -> dictionaries."""

import csv
from collections.abc import Iterable, Iterator


def parse_csv_rows(lines: Iterable[str]) -> Iterator[dict[str, str]]:
    """Lazily parse CSV lines (the first line is the header)."""
    yield from csv.DictReader(lines)
