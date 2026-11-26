"""Integration: config.yaml -> CSV/JSON/JSONL/YAML import -> validation -> export."""

import csv
import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pytest

from employee_importer import main as importer_main
from employee_importer.exceptions import DataImportError
from employee_importer.models import ImportStatistics
from employee_importer.readers import get_importer
from employee_importer.services import import_employees
from employee_importer.validators import TolerantPolicy, parse_employee

pytestmark = pytest.mark.integration
ALLOWED = {"IT", "Finance", "HR", "Sales"}
ConfigFactory = Callable[..., Path]


class FixedDatetime(datetime):
    """Deterministic time for summary.json."""

    @classmethod
    def now(cls, tz: object = None) -> "FixedDatetime":
        return cls(2026, 11, 26, 9, 0, 0)


def read_back(path: Path) -> list[dict[str, object]]:
    rows = [row for _, row in get_importer(path).read(path)]
    return [
        parse_employee(r, line_number=i, allowed_departments=ALLOWED).to_dict()
        for i, r in enumerate(rows, 1)
    ]


def test_full_import_export_run(
    make_config: ConfigFactory, output_format: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(importer_main, "datetime", FixedDatetime)
    config = make_config(fmt=output_format, minimum=30_000)
    out = config.parent / "out"

    exit_code = importer_main.main(["--config", str(config)])

    assert exit_code == 0
    employees = read_back(out / f"employees.{output_format}")
    names = [e["name"] for e in employees]
    assert names == ["Anna Koval", "Oleh Melnyk", "Iryna Bondar"]
    assert sum(float(str(e["salary"])) for e in employees) == pytest.approx(151_000)
    with (out / "errors.csv").open(encoding="utf-8", newline="") as file:
        errors = list(csv.DictReader(file))
    rejected = [(e["line"], e["field"]) for e in errors]
    assert rejected == [("6", "name"), ("7", "employee_id")]
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["finished_at"] == "2026-11-26T09:00:00"
    assert summary["statistics"] == {
        "total": 6, "valid": 4, "invalid": 2, "filtered_out": 1, "exported": 3,
        "errors_by_field": {"name": 1, "employee_id": 1},
    }
    log = (config.parent / "logs" / "importer.log").read_text(encoding="utf-8")
    assert "exported=3" in log and "52000" not in log  # salaries are not logged


def test_repeated_run_keeps_backup(make_config: ConfigFactory) -> None:
    config = make_config(minimum=30_000)
    assert importer_main.main(["--config", str(config)]) == 0
    first = (config.parent / "out" / "employees.json").read_text(encoding="utf-8")
    assert importer_main.main(["--config", str(config)]) == 0
    backup = config.parent / "out" / "employees.json.bak"
    assert backup.read_text(encoding="utf-8") == first


def test_strict_mode_from_environment_stops_without_output(
    make_config: ConfigFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EMPLOYEE_IMPORTER_SKIP_INVALID", "false")
    config = make_config()
    assert importer_main.main(["--config", str(config)]) == 1
    out = config.parent / "out"
    assert not (out / "employees.json").exists()
    assert not (out / "employees.json.tmp").exists()
    log = (config.parent / "logs" / "importer.log").read_text(encoding="utf-8")
    assert "Application stopped: RecordValidationError: line 6" in log


def test_missing_configuration_returns_error_code(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    assert importer_main.main(["--config", str(tmp_path / "absent.yaml")]) == 1
    assert "ConfigurationError" in caplog.text
    assert "Caused by FileNotFoundError" in caplog.text


RECORDS = [
    {"employee_id": 1, "name": "Anna Koval", "position": "Dev", "department": "IT",
     "salary": 52000},
    {"employee_id": 2, "name": "", "position": "Dev", "department": "IT",
     "salary": 40000},
    {"employee_id": 3, "name": "Iryna Bondar", "position": "Lead",
     "department": "IT", "salary": 68000},
]


@pytest.mark.parametrize("suffix", ["json", "jsonl", "yaml"])
def test_other_input_formats_give_same_result(tmp_path: Path, suffix: str) -> None:
    import yaml

    path = tmp_path / f"staff.{suffix}"
    if suffix == "json":
        path.write_text(json.dumps(RECORDS), encoding="utf-8")
    elif suffix == "jsonl":
        lines = [json.dumps(r) for r in RECORDS]
        path.write_text("\n".join(lines[:1] + [""] + lines[1:]), encoding="utf-8")
    else:
        path.write_text(yaml.safe_dump(RECORDS), encoding="utf-8")
    stats = ImportStatistics()
    employees = list(import_employees(get_importer(path), path,
                                      allowed_departments=ALLOWED,
                                      policy=TolerantPolicy(), statistics=stats))
    assert [e.employee_id for e in employees] == [1, 3]
    assert (stats.valid, stats.invalid) == (2, 1)


@pytest.mark.parametrize(
    ("name", "content", "message"),
    [
        ("broken.json", "[{", "Invalid JSON document"),
        ("object.json", '{"a": 1}', "must be an array"),
        ("broken.jsonl", '{"a": 1}\n{oops', "Invalid JSON at line 2"),
        ("broken.yaml", "- [unclosed", "Invalid YAML"),
        ("mapping.yaml", "a: 1", "must be a list"),
        ("empty.csv", "", "CSV file is empty"),
    ],
)
def test_malformed_input_files(tmp_path: Path, name: str, content: str,
                               message: str) -> None:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    with pytest.raises(DataImportError, match=message):
        list(get_importer(path).read(path))


@pytest.mark.parametrize("suffix", ["csv", "json", "jsonl", "yaml"])
def test_missing_input_file(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / f"absent.{suffix}"
    with pytest.raises(DataImportError, match="Cannot read input file") as exc_info:
        list(get_importer(path).read(path))
    assert isinstance(exc_info.value.__cause__, FileNotFoundError)
