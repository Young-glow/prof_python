"""Exporters behind one Protocol; every exporter writes atomically."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from employee_importer.exceptions import DataExportError, UnsupportedFormatError
from employee_importer.files import AtomicWriter, atomic_write_text
from employee_importer.models import FIELDS, Employee, InvalidRecord


class EmployeeJSONEncoder(json.JSONEncoder):
    """Custom encoder for values that json cannot serialize by default."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Path):
            return o.as_posix()
        if isinstance(o, datetime | date):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, frozenset | set):
            return sorted(o)
        return super().default(o)


class Exporter(Protocol):
    def export(self, employees: Iterable[Employee], path: Path) -> int: ...


class JsonExporter:
    """Streaming JSON array: objects are written one by one, not via a list."""

    def __init__(self, backup: bool = False) -> None:
        self.backup = backup

    def export(self, employees: Iterable[Employee], path: Path) -> int:
        count = 0
        with AtomicWriter(path, backup=self.backup) as file:
            file.write("[")
            for employee in employees:
                file.write(",\n  " if count else "\n  ")
                json.dump(employee.to_dict(), file, ensure_ascii=False)
                count += 1
            file.write("\n]\n" if count else "]\n")
        return count


class JsonLinesExporter:
    def __init__(self, backup: bool = False) -> None:
        self.backup = backup

    def export(self, employees: Iterable[Employee], path: Path) -> int:
        count = 0
        with AtomicWriter(path, backup=self.backup) as file:
            for employee in employees:
                file.write(json.dumps(employee.to_dict(), ensure_ascii=False) + "\n")
                count += 1
        return count


class CsvExporter:
    def __init__(self, backup: bool = False) -> None:
        self.backup = backup

    def export(self, employees: Iterable[Employee], path: Path) -> int:
        count = 0
        with AtomicWriter(path, backup=self.backup, newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(FIELDS))
            writer.writeheader()
            for employee in employees:
                writer.writerow(employee.to_dict())
                count += 1
        return count


EXPORTERS: dict[str, type[JsonExporter | JsonLinesExporter | CsvExporter]] = {
    "json": JsonExporter,
    "jsonl": JsonLinesExporter,
    "csv": CsvExporter,
}


def get_exporter(fmt: str, *, backup: bool = False) -> Exporter:
    try:
        return EXPORTERS[fmt.lower()](backup=backup)
    except KeyError as error:
        raise UnsupportedFormatError(fmt) from error


def write_error_report(records: Iterable[InvalidRecord], path: Path) -> int:
    """Separate CSV with rejected rows (without salary values)."""
    count = 0
    with AtomicWriter(path, newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["line", "employee_id", "field", "error"])
        for record in records:
            writer.writerow(
                [record.line_number, record.employee_id, record.field, record.message]
            )
            count += 1
    return count


def write_summary(summary: dict[str, Any], path: Path) -> None:
    try:
        text = json.dumps(
            summary, cls=EmployeeJSONEncoder, ensure_ascii=False, indent=2
        )
    except TypeError as error:
        raise DataExportError("Summary is not serializable") from error
    atomic_write_text(path, text + "\n")

