import pytest

from employee_manager.exceptions import InvalidEmployeeDataError
from employee_manager.models import Employee
from employee_manager.services import (
    calculate_average_salary,
    calculate_payroll,
    filter_by_department,
    find_highest_paid,
    payroll_by_department,
    search_employees,
    sort_by_salary,
)


@pytest.fixture
def employees() -> list[Employee]:
    return [
        Employee("Anna Koval", "Developer", "IT", 45000),
        Employee("Oleh Melnyk", "Accountant", "Finance", 30000),
        Employee("Iryna Bondar", "Team Lead", "IT", 60000),
    ]


def test_filter_by_department(employees: list[Employee]) -> None:
    assert len(filter_by_department(employees, "it")) == 2


def test_average_salary(employees: list[Employee]) -> None:
    assert calculate_average_salary(employees) == 45000
    assert calculate_average_salary([]) == 0.0


def test_highest_paid(employees: list[Employee]) -> None:
    best = find_highest_paid(employees)
    assert best is not None
    assert best.name == "Iryna Bondar"
    assert find_highest_paid([]) is None


def test_payroll(employees: list[Employee]) -> None:
    assert calculate_payroll(employees) == 135000
    assert payroll_by_department(employees) == {
        "IT": 105000,
        "Finance": 30000,
    }


def test_search_and_sort(employees: list[Employee]) -> None:
    found = search_employees(employees, department="IT", min_salary=50000)
    assert [e.name for e in found] == ["Iryna Bondar"]
    assert sort_by_salary(employees)[0].salary == 60000


def test_validation() -> None:
    with pytest.raises(InvalidEmployeeDataError):
        Employee("", "Developer", "IT", 40000)
    with pytest.raises(InvalidEmployeeDataError):
        Employee("Test", "Developer", "IT", 100)
