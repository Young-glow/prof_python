"""Transformation stage."""

from collections.abc import Iterable, Iterator

from stream_processor.models import EmployeeRecord


def normalize_names(employees: Iterable[EmployeeRecord]) -> Iterator[EmployeeRecord]:
    """Normalize names: 'anna koval' -> 'Anna Koval'."""
    for employee in employees:
        yield employee._replace(name=" ".join(employee.name.split()).title())


def salary_level(salary: float) -> str:
    """Salary level of an employee."""
    if salary < 30000:
        return "low"
    if salary < 50000:
        return "medium"
    return "high"
