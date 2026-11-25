"""Tests of laboratory work 5 (reliable import/export)."""

import json
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from employee_importer.config import load_config
from employee_importer.exceptions import (
    ConfigurationError,
    DataExportError,
    DataImportError,
    RecordValidationError,
    UnsupportedFormatError,
)
from employee_importer.exporters import JsonExporter, get_exporter
from employee_importer.logging_config import SensitiveDataFilter
from employee_importer.models import Employee, ImportStatistics, InvalidRecord
from employee_importer.readers import CsvImporter, JsonImporter, get_importer
from employee_importer.services import filter_by_min_salary, import_employees
from employee_importer.validators import StrictPolicy, TolerantPolicy, parse_employee

ROOT = Path(__file__).resolve().parents[1]
STAFF = ROOT / "data" / "staff.csv"
ALLOWED = {"IT", "Finance", "HR", "Sales"}
CONFIG = """version: 1
input: {path: data.csv}
output: {path: out/result.json, format: json}
processing:
  minimum_salary: %s
  skip_invalid: true
  allowed_departments: [IT, HR]
logging: {level: INFO, path: logs/app.log}
"""


def write_config(tmp_path: Path, minimum: str = "30000") -> Path:
    (tmp_path / "data.csv").write_text("employee_id\n", encoding="utf-8")
    path = tmp_path / "config.yaml"
    path.write_text(CONFIG % minimum, encoding="utf-8")
    return path


def test_load_config_and_env_override(tmp_path: Path) -> None:
    config = load_config(write_config(tmp_path), env={})
    assert config.processing.minimum_salary == 30000
    assert config.output.path == tmp_path / "out" / "result.json"
    overridden = load_config(
        write_config(tmp_path),
        env={"EMPLOYEE_IMPORTER_SKIP_INVALID": "false",
             "EMPLOYEE_IMPORTER_MIN_SALARY": "100"},
    )
    assert overridden.processing.skip_invalid is False
    assert overridden.processing.minimum_salary == 100


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("version: 1\ninput: [unclosed", "Invalid YAML"),
        ("version: 1\noutput: {path: x.json}\n", "Missing configuration key: input"),
        (CONFIG % "-5", "minimum_salary must be >= 0"),
        (CONFIG.replace("version: 1", "version: 2") % "0", "Unsupported"),
    ],
)
def test_invalid_configuration(tmp_path: Path, text: str, message: str) -> None:
    (tmp_path / "data.csv").write_text("employee_id\n", encoding="utf-8")
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ConfigurationError, match=message):
        load_config(path, env={})


def test_missing_config_keeps_cause(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError) as info:
        load_config(tmp_path / "absent.yaml", env={})
    assert isinstance(info.value.__cause__, FileNotFoundError)


def test_parse_employee_valid_and_chained_error() -> None:
    row = {"employee_id": "7", "name": " anna  koval ", "position": "Dev",
           "department": "IT", "salary": "52000"}
    employee = parse_employee(row, line_number=2, allowed_departments=ALLOWED)
    assert employee == Employee(7, "Anna Koval", "Dev", "IT", 52000.0)
    with pytest.raises(RecordValidationError) as info:
        parse_employee({**row, "salary": "wrong"}, line_number=3,
                       allowed_departments=ALLOWED)
    assert info.value.field == "salary" and info.value.line_number == 3
    assert isinstance(info.value.__cause__, ValueError)
    assert "wrong" not in str(info.value)  # salary value is not leaked


def test_tolerant_import_statistics_and_filter() -> None:
    stats, rejected = ImportStatistics(), []
    employees = import_employees(CsvImporter(), STAFF, allowed_departments=ALLOWED,
                                 policy=TolerantPolicy(), statistics=stats,
                                 rejected=rejected)
    selected = list(filter_by_min_salary(employees, 30000, stats))
    assert (stats.total, stats.valid, stats.invalid) == (14, 8, 6)
    assert stats.filtered_out == 1 and len(selected) == 7
    assert {r.field for r in rejected} == {"name", "employee_id", "salary",
                                          "department", "position"}


def test_strict_import_stops_on_first_error() -> None:
    stats = ImportStatistics()
    employees = import_employees(CsvImporter(), STAFF, allowed_departments=ALLOWED,
                                 policy=StrictPolicy(), statistics=stats)
    with pytest.raises(RecordValidationError) as info:
        list(employees)
    assert info.value.line_number == 5 and stats.valid == 3


def test_atomic_export_keeps_previous_output(tmp_path: Path) -> None:
    target = tmp_path / "employees.json"
    JsonExporter().export([Employee(1, "Anna Koval", "Dev", "IT", 1.0)], target)
    before = target.read_text(encoding="utf-8")

    def broken() -> Iterator[Employee]:
        yield Employee(2, "Oleh Melnyk", "Acc", "Finance", 2.0)
        raise OSError("disk is full")

    with pytest.raises(DataExportError) as info:
        JsonExporter().export(broken(), target)
    assert isinstance(info.value.__cause__, OSError)
    assert target.read_text(encoding="utf-8") == before
    assert not (tmp_path / "employees.json.tmp").exists()


@pytest.mark.parametrize("fmt", ["json", "jsonl", "csv"])
def test_export_round_trip(tmp_path: Path, fmt: str) -> None:
    people = [Employee(1, "Anna Koval", "Dev", "IT", 52000.0),
              Employee(2, "Oleh Melnyk", "Accountant", "Finance", 31000.0)]
    path = tmp_path / f"result.{fmt}"
    assert get_exporter(fmt).export(people, path) == 2
    rows = [row for _, row in get_importer(path).read(path)]
    restored = [parse_employee(r, line_number=1, allowed_departments=ALLOWED)
                for r in rows]
    assert restored == people


def test_import_errors_are_chained(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("[{", encoding="utf-8")
    with pytest.raises(DataImportError) as info:
        list(JsonImporter().read(broken))
    assert isinstance(info.value.__cause__, json.JSONDecodeError)
    with pytest.raises(UnsupportedFormatError):
        get_importer(tmp_path / "data.xlsx")
    with pytest.raises(DataImportError):
        list(CsvImporter().read(tmp_path / "missing.csv"))


def test_export_error_for_bad_directory(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")
    with pytest.raises(DataExportError):
        JsonExporter().export([], blocker / "out.json")


def test_salary_is_masked_in_logs() -> None:
    record = logging.LogRecord("t", logging.INFO, __file__, 1,
                               "row id=%s salary=%s", ("5", "41000"), None)
    SensitiveDataFilter().filter(record)
    assert record.getMessage() == "row id=5 salary=***"


def test_invalid_record_has_no_salary_field() -> None:
    assert "salary" not in InvalidRecord.__slots__
