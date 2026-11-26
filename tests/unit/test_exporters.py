"""Unit tests: exporters, JSON encoder and error report (paths found by coverage)."""

import csv
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from employee_importer.exceptions import DataExportError, UnsupportedFormatError
from employee_importer.exporters import (
    CsvExporter,
    EmployeeJSONEncoder,
    JsonExporter,
    get_exporter,
    write_error_report,
    write_summary,
)
from employee_importer.models import Employee, InvalidRecord


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Path("out") / "employees.json", "out/employees.json"),
        (datetime(2026, 11, 26, 9, 30), "2026-11-26T09:30:00"),
        (date(2026, 11, 26), "2026-11-26"),
        (Decimal("52000.50"), 52000.5),
        (frozenset({"IT", "HR"}), ["HR", "IT"]),
    ],
    ids=["path", "datetime", "date", "decimal", "frozenset"],
)
def test_custom_json_encoder(value: object, expected: object) -> None:
    assert json.loads(json.dumps(value, cls=EmployeeJSONEncoder)) == expected


def test_unsupported_value_in_summary_is_chained(tmp_path: Path) -> None:
    with pytest.raises(DataExportError, match="not serializable") as exc_info:
        write_summary({"bad": object()}, tmp_path / "summary.json")
    assert isinstance(exc_info.value.__cause__, TypeError)
    assert not (tmp_path / "summary.json").exists()


def test_empty_export_gives_valid_files(tmp_path: Path) -> None:
    assert JsonExporter().export([], tmp_path / "e.json") == 0
    assert json.loads((tmp_path / "e.json").read_text(encoding="utf-8")) == []
    assert CsvExporter().export([], tmp_path / "e.csv") == 0
    header = (tmp_path / "e.csv").read_text(encoding="utf-8").strip()
    assert header == "employee_id,name,position,department,salary"


def test_error_report_has_no_salary_column(tmp_path: Path) -> None:
    records = [InvalidRecord(5, "salary", "Salary must be >= 0", "9")]
    assert write_error_report(records, tmp_path / "errors.csv") == 1
    with (tmp_path / "errors.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows == [{"line": "5", "employee_id": "9", "field": "salary",
                     "error": "Salary must be >= 0"}]


def test_unknown_export_format() -> None:
    with pytest.raises(UnsupportedFormatError, match="xml") as exc_info:
        get_exporter("xml")
    assert exc_info.value.format == "xml"
    assert isinstance(exc_info.value.__cause__, KeyError)


def test_backup_flag_is_passed_to_exporter(tmp_path: Path) -> None:
    target = tmp_path / "e.csv"
    exporter = get_exporter("CSV", backup=True)
    employee = Employee(1, "Anna Koval", "Dev", "IT", 52_000.0)
    exporter.export([employee], target)
    exporter.export([], target)
    assert "Anna Koval" in (tmp_path / "e.csv.bak").read_text(encoding="utf-8")
