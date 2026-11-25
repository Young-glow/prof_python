"""Sink: streaming batch export to a CSV file."""

import csv
from collections.abc import Iterable
from pathlib import Path

from stream_processor.batches import batched
from stream_processor.models import CSV_HEADER, EmployeeRecord


def export_batches(
    employees: Iterable[EmployeeRecord],
    path: Path,
    batch_size: int = 1000,
) -> int:
    """Write employees to `path` batch by batch; return the number of batches."""
    path.parent.mkdir(parents=True, exist_ok=True)
    batches = 0
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADER)
        for batch in batched(employees, batch_size):
            writer.writerows(batch)
            batches += 1
    return batches
