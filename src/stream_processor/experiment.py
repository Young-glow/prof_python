"""Eager vs lazy experiment: time, peak memory, time to first result."""

import csv
import tracemalloc
from collections.abc import Callable
from pathlib import Path
from time import perf_counter
from typing import Any

from stream_processor.analytics import calculate_statistics
from stream_processor.filters import validate_employees
from stream_processor.generate import dataset
from stream_processor.models import EmployeeRecord
from stream_processor.pipeline import build_pipeline, find_first
from stream_processor.transformations import normalize_names

SIZES: tuple[int, ...] = (10_000, 100_000, 500_000)


def eager_average(path: Path) -> float:
    """Eager version: every stage builds a full list in memory."""
    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    valid = list(validate_employees(rows))
    normalized = list(normalize_names(valid))
    return calculate_statistics(normalized).average_salary


def lazy_average(path: Path) -> float:
    """Lazy version: records flow through the pipeline one by one."""
    return calculate_statistics(build_pipeline(path)).average_salary


def eager_first(path: Path, minimum: float) -> EmployeeRecord | None:
    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    matching = [e for e in normalize_names(validate_employees(rows)) if e.salary >= minimum]
    return matching[0] if matching else None


def lazy_first(path: Path, minimum: float) -> EmployeeRecord | None:
    return find_first(build_pipeline(path), minimum)


def measure(function: Callable[..., Any], *args: Any) -> tuple[Any, float, int]:
    """Return (result, elapsed seconds, peak memory in bytes)."""
    tracemalloc.start()
    start = perf_counter()
    result = function(*args)
    elapsed = perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def run_experiment(sizes: tuple[int, ...] = SIZES) -> list[dict[str, float]]:
    rows = []
    for size in sizes:
        path = dataset(size)
        eager_result, eager_time, eager_peak = measure(eager_average, path)
        lazy_result, lazy_time, lazy_peak = measure(lazy_average, path)
        assert abs(eager_result - lazy_result) < 1e-6
        _, eager_first_time, _ = measure(eager_first, path, 0)
        _, lazy_first_time, _ = measure(lazy_first, path, 0)
        rows.append({
            "records": size,
            "eager_time": eager_time,
            "lazy_time": lazy_time,
            "eager_peak_mb": eager_peak / 2**20,
            "lazy_peak_mb": lazy_peak / 2**20,
            "eager_first": eager_first_time,
            "lazy_first": lazy_first_time,
        })
    return rows


def print_experiment() -> None:
    print("Eager vs lazy: average salary over the whole file")
    print(f"{'records':>8} {'eager, s':>9} {'lazy, s':>8} {'eager MB':>9} "
          f"{'lazy MB':>8} {'1st eager, s':>13} {'1st lazy, s':>12}")
    for row in run_experiment():
        print(f"{row['records']:8.0f} {row['eager_time']:9.3f} {row['lazy_time']:8.3f} "
              f"{row['eager_peak_mb']:9.2f} {row['lazy_peak_mb']:8.3f} "
              f"{row['eager_first']:13.3f} {row['lazy_first']:12.5f}")


def print_early_termination(size: int = 1_000_000, minimum: float = 119_990.0) -> None:
    """Find the first employee with a very high salary in a 1 000 000 file."""
    path = dataset(size)
    print(f"Early termination: first employee with salary >= {minimum:.0f} "
          f"in {size} records")
    for label, function in (("eager", eager_first), ("lazy", lazy_first)):
        found, elapsed, peak = measure(function, path, minimum)
        employee_id = found.employee_id if found else None
        print(f"{label:6} id={employee_id}  time={elapsed:.4f} s  "
              f"peak={peak / 2**20:.2f} MB")
