"""Lazy pipeline: source -> clean -> parse -> validate -> transform -> filter."""

from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path

from stream_processor.filters import (
    filter_by_department,
    filter_by_salary,
    validate_employees,
)
from stream_processor.models import EmployeeRecord
from stream_processor.parsers import parse_csv_rows
from stream_processor.readers import clean_lines, read_lines, read_many
from stream_processor.transformations import normalize_names

stage_log: list[str] = []


def logged(name: str, items: Iterable[EmployeeRecord]) -> Iterator[EmployeeRecord]:
    """Pass records through unchanged and remember how many went through."""
    count = 0
    for item in items:
        count += 1
        yield item
    stage_log.append(f"{name}: {count} records")


def build_pipeline(
    paths: Path | list[Path],
    departments: tuple[str, ...] = (),
    min_salary: float = 0.0,
    max_salary: float = float("inf"),
    errors: Counter[str] | None = None,
) -> Iterator[EmployeeRecord]:
    """Create the lazy pipeline. Nothing is read until it is consumed."""
    lines = read_many(paths) if isinstance(paths, list) else read_lines(paths)
    rows = parse_csv_rows(clean_lines(lines))
    valid = logged("validated", validate_employees(rows, errors))
    normalized = normalize_names(valid)
    by_department = filter_by_department(normalized, *departments)
    return logged("selected", filter_by_salary(by_department, min_salary, max_salary))


def find_first(
    employees: Iterable[EmployeeRecord],
    minimum_salary: float,
) -> EmployeeRecord | None:
    """Lazy search with early termination."""
    return next((e for e in employees if e.salary >= minimum_salary), None)
