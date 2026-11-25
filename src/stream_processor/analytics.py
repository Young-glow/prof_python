"""Aggregation stage: statistics in one pass over the stream."""

from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from itertools import accumulate, groupby, pairwise, takewhile

from stream_processor.models import EmployeeRecord
from stream_processor.transformations import salary_level


@dataclass
class SalaryStatistics:
    """Result of the streaming aggregation."""

    count: int = 0
    payroll: float = 0.0
    highest_paid: EmployeeRecord | None = None
    departments: Counter[str] = field(default_factory=Counter)

    @property
    def average_salary(self) -> float:
        return self.payroll / self.count if self.count else 0.0


def calculate_statistics(employees: Iterable[EmployeeRecord]) -> SalaryStatistics:
    """Streaming average salary, payroll fund, highest paid employee and
    Counter by department, all in one pass with O(1) memory per record."""
    stats = SalaryStatistics()
    for employee in employees:
        stats.count += 1
        stats.payroll += employee.salary
        stats.departments[employee.department] += 1
        if stats.highest_paid is None or employee.salary > stats.highest_paid.salary:
            stats.highest_paid = employee
    return stats


def running_payroll(employees: Iterable[EmployeeRecord]) -> Iterator[float]:
    """Accumulated payroll after every employee (itertools.accumulate)."""
    return accumulate(employee.salary for employee in employees)


def salary_differences(employees: Iterable[EmployeeRecord]) -> Iterator[float]:
    """Difference between salaries of neighbouring employees (pairwise)."""
    return (
        current.salary - previous.salary
        for previous, current in pairwise(employees)
    )


def count_by_level(employees: Iterable[EmployeeRecord]) -> dict[str, int]:
    """Count employees by salary level with itertools.groupby.

    groupby joins only neighbouring equal keys, so the data is sorted first.
    """
    ordered = sorted(employees, key=lambda employee: salary_level(employee.salary))
    return {
        level: sum(1 for _ in group)
        for level, group in groupby(
            ordered, key=lambda employee: salary_level(employee.salary)
        )
    }


def take_until_payroll(
    employees: Iterable[EmployeeRecord],
    limit: float,
) -> list[float]:
    """Running payroll values while they do not exceed `limit` (takewhile)."""
    return list(takewhile(lambda total: total <= limit, running_payroll(employees)))
