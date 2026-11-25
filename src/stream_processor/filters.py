"""Validation and filtering stages (generators)."""

from collections import Counter
from collections.abc import Iterable, Iterator

from stream_processor.models import EmployeeRecord

MAX_SALARY = 1_000_000.0


def validate_employees(
    rows: Iterable[dict[str, str]],
    errors: Counter[str] | None = None,
) -> Iterator[EmployeeRecord]:
    """Streaming validation: yield only correct records.

    If `errors` is given, the reasons of rejected records are counted in it.
    """
    for row in rows:
        try:
            employee_id = int(row["employee_id"])
            salary = float(row["salary"])
        except (KeyError, TypeError, ValueError):
            if errors is not None:
                errors["bad number"] += 1
            continue
        name = (row.get("name") or "").strip()
        position = (row.get("position") or "").strip()
        department = (row.get("department") or "").strip()
        if not (name and position and department):
            if errors is not None:
                errors["empty field"] += 1
            continue
        if not 0 < salary <= MAX_SALARY:
            if errors is not None:
                errors["salary out of range"] += 1
            continue
        yield EmployeeRecord(employee_id, name, position, department, salary)


def filter_by_department(
    employees: Iterable[EmployeeRecord],
    *departments: str,
) -> Iterator[EmployeeRecord]:
    """Keep employees of the given departments (all if none given)."""
    allowed = set(departments)
    for employee in employees:
        if not allowed or employee.department in allowed:
            yield employee


def filter_by_salary(
    employees: Iterable[EmployeeRecord],
    minimum: float = 0.0,
    maximum: float = float("inf"),
) -> Iterator[EmployeeRecord]:
    """Lazy filter by salary level."""
    for employee in employees:
        if minimum <= employee.salary <= maximum:
            yield employee
