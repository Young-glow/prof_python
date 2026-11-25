"""Streaming import pipeline: read -> validate -> policy -> filter."""

from __future__ import annotations

import logging
from collections.abc import Collection, Iterable, Iterator
from pathlib import Path

from employee_importer.exceptions import RecordValidationError
from employee_importer.models import Employee, ImportStatistics, InvalidRecord
from employee_importer.readers import Importer
from employee_importer.validators import ValidationPolicy, parse_employee

logger = logging.getLogger(__name__)


def import_employees(
    importer: Importer,
    path: Path,
    *,
    allowed_departments: Collection[str],
    policy: ValidationPolicy,
    statistics: ImportStatistics,
    rejected: list[InvalidRecord] | None = None,
) -> Iterator[Employee]:
    """Yield valid employees one by one; invalid ones go to the policy."""
    for line_number, row in importer.read(path):
        statistics.total += 1
        try:
            employee = parse_employee(
                row, line_number=line_number, allowed_departments=allowed_departments
            )
        except RecordValidationError as error:
            statistics.invalid += 1
            statistics.errors_by_field[error.field or "?"] += 1
            if rejected is not None:
                rejected.append(
                    InvalidRecord(
                        line_number,
                        error.field or "?",
                        str(error.args[0]),
                        str(row.get("employee_id", "")),
                    )
                )
            policy.handle(error)  # strict -> raises, tolerant -> continue
            continue
        statistics.valid += 1
        yield employee


def filter_by_min_salary(
    employees: Iterable[Employee], minimum_salary: float, statistics: ImportStatistics
) -> Iterator[Employee]:
    for employee in employees:
        if employee.salary >= minimum_salary:
            yield employee
        else:
            statistics.filtered_out += 1
            logger.info(
                "Employee #%s filtered out: salary below the configured minimum",
                employee.employee_id,
            )
