"""Validation of external rows and the policies for invalid records."""

from __future__ import annotations

import logging
import re
from collections.abc import Collection, Mapping
from typing import Any, Protocol

from employee_importer.exceptions import RecordValidationError
from employee_importer.models import Employee

logger = logging.getLogger(__name__)

NAME_PATTERN = re.compile(r"^[A-Za-zА-Яа-яІіЇїЄєҐґ'’ -]{2,60}$")


def _text(row: Mapping[str, Any], field: str, line_number: int) -> str:
    try:
        value = str(row[field]).strip()
    except KeyError as error:
        raise RecordValidationError(
            f"Missing column '{field}'", line_number=line_number, field=field
        ) from error
    if not value or value.lower() == "none":
        raise RecordValidationError(
            f"{field.capitalize()} is empty", line_number=line_number, field=field
        )
    return value


def parse_employee(
    row: Mapping[str, Any],
    *,
    line_number: int,
    allowed_departments: Collection[str],
) -> Employee:
    """Convert an external row into a domain object or raise RecordValidationError."""
    try:
        employee_id = int(row["employee_id"])
    except (KeyError, TypeError, ValueError) as error:
        raise RecordValidationError(
            "Employee ID must be an integer",
            line_number=line_number,
            field="employee_id",
        ) from error
    if employee_id <= 0:
        raise RecordValidationError(
            "Employee ID must be positive",
            line_number=line_number,
            field="employee_id",
        )

    name = _text(row, "name", line_number)
    if not NAME_PATTERN.fullmatch(name):
        raise RecordValidationError(
            "Name contains invalid characters", line_number=line_number, field="name"
        )
    position = _text(row, "position", line_number)
    department = _text(row, "department", line_number)
    if department not in allowed_departments:
        raise RecordValidationError(
            f"Department '{department}' is not allowed",
            line_number=line_number,
            field="department",
        )

    try:
        salary = float(row["salary"])
    except (KeyError, TypeError, ValueError) as error:
        # the raw value is deliberately not included: salary data is sensitive
        raise RecordValidationError(
            "Salary must be a number", line_number=line_number, field="salary"
        ) from error
    if salary < 0:
        raise RecordValidationError(
            "Salary must be >= 0", line_number=line_number, field="salary"
        )
    clean_name = " ".join(name.split()).title()
    return Employee(employee_id, clean_name, position, department, salary)


class ValidationPolicy(Protocol):
    """Decides what to do with an invalid record."""

    name: str

    def handle(self, error: RecordValidationError) -> None:
        """Return to skip the record, raise to stop the import."""


class StrictPolicy:
    """The first invalid record stops the import."""

    name = "strict"

    def handle(self, error: RecordValidationError) -> None:
        logger.error("Invalid record, import stopped (%s)", error)
        raise error


class TolerantPolicy:
    """Invalid records are logged, counted and skipped."""

    name = "tolerant"

    def handle(self, error: RecordValidationError) -> None:
        logger.warning("Invalid record skipped (%s)", error)


def policy_for(skip_invalid: bool) -> ValidationPolicy:
    return TolerantPolicy() if skip_invalid else StrictPolicy()
