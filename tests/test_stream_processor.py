from collections import Counter
from collections.abc import Iterator
from itertools import islice
from pathlib import Path

import pytest

from stream_processor.analytics import (
    calculate_statistics,
    count_by_level,
    running_payroll,
    salary_differences,
    take_until_payroll,
)
from stream_processor.batches import batched
from stream_processor.export import export_batches
from stream_processor.filters import (
    filter_by_department,
    filter_by_salary,
    validate_employees,
)
from stream_processor.iterators import SalaryRange, flatten
from stream_processor.models import EmployeeRecord
from stream_processor.parsers import parse_csv_rows
from stream_processor.readers import clean_lines, employee_ids, read_lines, read_many
from stream_processor.transformations import normalize_names

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "employees.csv"


def valid_records() -> Iterator[EmployeeRecord]:
    return normalize_names(validate_employees(parse_csv_rows(clean_lines(read_lines(SAMPLE)))))


def test_readers_are_lazy_and_one_shot() -> None:
    lines = read_lines(SAMPLE)
    assert iter(lines) is lines
    assert next(lines).startswith("employee_id")
    assert sum(1 for _ in lines) == 16
    assert list(lines) == []


def test_read_many_skips_repeated_header() -> None:
    rows = list(parse_csv_rows(clean_lines(read_many([SAMPLE, SAMPLE]))))
    assert len(rows) == 32


def test_validation_counts_errors() -> None:
    errors: Counter[str] = Counter()
    records = list(validate_employees(parse_csv_rows(read_lines(SAMPLE)), errors))
    assert len(records) == 13
    assert errors == Counter({"bad number": 1, "empty field": 1, "salary out of range": 1})


def test_lazy_exception_appears_on_consumption() -> None:
    def to_int(values: list[str]) -> Iterator[int]:
        for value in values:
            yield int(value)

    numbers = to_int(["1", "x"])  # no error yet
    assert next(numbers) == 1
    with pytest.raises(ValueError):
        next(numbers)


def test_filters_and_transformation() -> None:
    it = list(filter_by_department(valid_records(), "IT"))
    assert [e.employee_id for e in it] == [1, 3, 6, 8, 12]
    assert it[0].name == "Anna Koval"
    rich = list(filter_by_salary(valid_records(), 50000))
    assert {e.employee_id for e in rich} == {1, 3, 8}
    assert len(list(filter_by_department(valid_records()))) == 13


def test_statistics() -> None:
    stats = calculate_statistics(valid_records())
    assert stats.count == 13
    assert stats.payroll == 539000
    assert round(stats.average_salary, 2) == 41461.54
    assert stats.highest_paid is not None and stats.highest_paid.name == "Iryna Bondar"
    assert stats.departments["IT"] == 5 and stats.departments["Marketing"] == 1
    assert calculate_statistics([]).average_salary == 0.0


def test_itertools_tools() -> None:
    assert list(islice(running_payroll(valid_records()), 3)) == [52000, 83000, 151000]
    assert list(islice(salary_differences(valid_records()), 2)) == [-21000, 37000]
    assert count_by_level(valid_records()) == {"high": 3, "low": 3, "medium": 7}
    assert take_until_payroll(valid_records(), 100000) == [52000, 83000]


def test_batches() -> None:
    sizes = [len(batch) for batch in batched(range(10), 4)]
    assert sizes == [4, 4, 2]
    with pytest.raises(ValueError):
        next(batched(range(3), 0))


def test_export(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    assert export_batches(valid_records(), out, batch_size=5) == 3
    assert len(list(read_lines(out))) == 14


def test_custom_iterator_and_flatten() -> None:
    levels = SalaryRange(10000, 40000, 10000)
    assert list(levels) == [10000, 20000, 30000]
    assert list(levels) == [10000, 20000, 30000]  # iterable is reusable
    iterator = iter(levels)
    assert iter(iterator) is iterator
    assert list(iterator) == [10000, 20000, 30000] and list(iterator) == []
    assert list(flatten([1, [2, [3, [4]]], 5])) == [1, 2, 3, 4, 5]
    assert list(islice(employee_ids(100), 3)) == [100, 101, 102]
