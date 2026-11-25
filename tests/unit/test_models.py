"""Unit tests: Employee hierarchy and Department."""

from collections.abc import Callable

import pytest

from employee_domain.exceptions import (
    DepartmentError,
    EmployeeNotFoundError,
    ValidationError,
)
from employee_domain.models import Department, Developer, Employee, Manager
from employee_domain.value_objects import DeveloperLevel, Email, Money

EmployeeFactory = Callable[..., Employee]


def test_employee_creation(developer: Employee) -> None:
    assert developer.id == 1
    assert developer.name == "Anna Koval"
    assert developer.salary == Money(52_000)
    assert developer.department is None


def test_abstract_employee_cannot_be_created() -> None:
    with pytest.raises(TypeError, match="abstract"):
        Employee(1, "Anna", Email("a@b.ua"), Money(9000))  # type: ignore[abstract]


@pytest.mark.parametrize(
    "salary",
    [pytest.param(8_000, id="minimum"), pytest.param(8_000.01, id="just-above"),
     pytest.param(250_000, id="large")],
)
def test_salary_on_and_above_minimum_is_accepted(
    employee_factory: EmployeeFactory, salary: float
) -> None:
    assert employee_factory(salary=salary).salary.amount == pytest.approx(salary)


@pytest.mark.parametrize(
    "salary",
    [pytest.param(7_999.99, id="just-below"), pytest.param(0, id="zero"),
     pytest.param(100, id="tiny")],
)
def test_salary_below_minimum_raises_validation_error(
    employee_factory: EmployeeFactory, salary: float
) -> None:
    with pytest.raises(ValidationError, match="at least") as exc_info:
        employee_factory(salary=salary)
    assert "8 000.00 UAH" in str(exc_info.value)


@pytest.mark.parametrize(
    ("name", "message"),
    [("   ", "empty"), ("A" * 51, "too long")],
    ids=["blank", "51-chars"],
)
def test_invalid_name(
    employee_factory: EmployeeFactory, name: str, message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        employee_factory(name=name)


def test_name_is_stripped_and_50_chars_allowed(
    employee_factory: EmployeeFactory,
) -> None:
    assert employee_factory(name="  Anna Koval ").name == "Anna Koval"
    assert len(employee_factory(name="A" * 50).name) == 50


@pytest.mark.parametrize(
    ("percent", "expected"),
    [(0.01, 52_005.2), (10, 57_200), (50, 78_000)],
    ids=["min", "typical", "max"],
)
def test_raise_salary_boundaries(
    developer: Employee, percent: float, expected: float
) -> None:
    developer.raise_salary(percent)
    assert developer.salary.amount == pytest.approx(expected)


@pytest.mark.parametrize("percent", [0, -5, 50.01])
def test_raise_salary_out_of_range(developer: Employee, percent: float) -> None:
    with pytest.raises(ValidationError, match="Raise must be"):
        developer.raise_salary(percent)
    assert developer.salary == Money(52_000)  # state did not change


def test_monthly_pay_is_polymorphic(
    manager: Manager, employee_factory: EmployeeFactory
) -> None:
    senior = employee_factory(employee_id=8, salary=61_000, level=DeveloperLevel.SENIOR)
    junior = employee_factory(employee_id=6, salary=38_000, level=DeveloperLevel.JUNIOR)
    assert manager.monthly_pay().amount == pytest.approx(78_200)
    assert senior.monthly_pay().amount == pytest.approx(68_000)
    assert junior.monthly_pay() == junior.salary
    assert isinstance(senior, Developer) and senior.role == "Senior Developer"


def test_employees_are_equal_by_id(employee_factory: EmployeeFactory) -> None:
    first = employee_factory(employee_id=7, name="Anna")
    same_id = employee_factory(employee_id=7, name="Other", salary=9_000)
    assert first == same_id
    assert len({first, same_id}) == 1


def test_assign_employee_to_department(developer: Employee) -> None:
    department = Department(1, "IT")
    department.add(developer)
    assert developer.department == "IT"
    assert len(department) == 1
    assert 1 in department and developer in department
    assert department[1] is developer


def test_employee_cannot_be_in_two_departments(developer: Employee) -> None:
    Department(1, "IT").add(developer)
    with pytest.raises(DepartmentError, match="already works in IT"):
        Department(2, "Finance").add(developer)


def test_empty_department() -> None:
    department = Department(9, "Legal")
    assert len(department) == 0
    assert list(department) == []
    assert department.payroll == Money(0)
    assert department.head is None
    with pytest.raises(EmployeeNotFoundError) as exc_info:
        department[1]
    assert exc_info.value.employee_id == 1


def test_department_payroll_and_head(staff: list[Employee], manager: Manager) -> None:
    department = Department(1, "IT")
    for employee in (staff[0], staff[2]):
        department.add(employee)
    department.assign_head(manager)
    assert department.head is manager
    assert manager.team_size == 2
    assert department.payroll.amount == pytest.approx(55_000 + 78_200 + 38_000)


def test_removing_head_clears_it(staff: list[Employee], manager: Manager) -> None:
    department = Department(1, "IT")
    department.add(staff[0])
    department.assign_head(manager)
    removed = department.remove(manager.id)
    assert removed is manager
    assert department.head is None and manager.department is None
    with pytest.raises(EmployeeNotFoundError):
        department.remove(manager.id)
