"""Batch processing."""

from collections.abc import Iterable, Iterator
from itertools import islice
from typing import TypeVar

T = TypeVar("T")


def batched(items: Iterable[T], batch_size: int) -> Iterator[list[T]]:
    """Split a stream into lists of `batch_size` items (the last may be shorter).

    Only the current batch is kept in memory.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    iterator = iter(items)
    while batch := list(islice(iterator, batch_size)):
        yield batch
