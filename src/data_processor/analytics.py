"""Aggregation, sorting and statistics."""

from collections.abc import Callable, Iterable
from typing import Any

from data_processor.data import Employee
from data_processor.decorators import log_operation, measure_time
from data_processor.processors import group_by


@measure_time
def calculate_average_salary(employees: list[Employee]) -> float:
    """Average salary (generator expression, no temporary list).  O(n)."""
    if not employees:
        return 0.0
    return sum(float(e["salary"]) for e in employees) / len(employees)


def calculate_payroll(employees: Iterable[Employee]) -> float:
    """Total payroll fund.  O(n)."""
    return sum(float(employee["salary"]) for employee in employees)


@log_operation("max with lambda")
def find_highest_paid(employees: list[Employee]) -> Employee | None:
    """Employee with the maximum salary.  O(n)."""
    if not employees:
        return None
    return max(employees, key=lambda employee: float(employee["salary"]))


def average_salary_by_department(employees: list[Employee]) -> dict[str, float]:
    """Average salary of every department (dict comprehension)."""
    return {
        department: calculate_average_salary(members)
        for department, members in group_by(employees, "department").items()
    }


def sort_items(
    employees: Iterable[Employee],
    *fields: str,
    reverse: bool = False,
) -> list[Employee]:
    """Universal sort by one or several fields (*args).  O(n log n)."""
    return sorted(
        employees,
        key=lambda employee: tuple(employee[field] for field in fields),
        reverse=reverse,
    )


def average(*values: float) -> float:
    """Average of any number of values (*args)."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def create_record(**fields: Any) -> Employee:
    """Create an employee record from keyword arguments (**kwargs)."""
    return dict(fields)


def salary_range(employees: list[Employee]) -> tuple[float, float]:
    """Return (minimum, maximum) salary as a tuple."""
    salaries = [float(employee["salary"]) for employee in employees]
    return (min(salaries), max(salaries)) if salaries else (0.0, 0.0)


def build_summary(employees: list[Employee]) -> dict[str, Any]:
    """Export summary: all key statistics in one dict."""
    best = find_highest_paid(employees)
    low, high = salary_range(employees)
    return {
        "employees": len(employees),
        "departments": sorted({str(e["department"]) for e in employees}),
        "payroll": calculate_payroll(employees),
        "average_salary": round(calculate_average_salary(employees), 2),
        "min_salary": low,
        "max_salary": high,
        "highest_paid": best["name"] if best else None,
    }


def pipeline(
    employees: list[Employee],
    *steps: Callable[[list[Employee]], list[Employee]],
) -> list[Employee]:
    """Apply processing steps one after another (pipeline processing)."""
    result = employees
    for step in steps:
        result = step(result)
    return result
