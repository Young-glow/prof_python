"""Experiment 4: the same scenario with a Mock repository and with a fake one."""

from unittest.mock import MagicMock, Mock

from employee_domain.adapters import MemoryNotifier
from employee_domain.models import Department, Developer
from employee_domain.repositories import InMemoryRepository
from employee_domain.services import EmployeeService
from employee_domain.value_objects import Email, Money


def make_developer() -> Developer:
    return Developer(1, "Anna Koval", Email("anna@company.ua"), Money(52_000))


def test_hire_with_mock_repository() -> None:
    employees = Mock(spec=InMemoryRepository)
    departments = MagicMock(spec=InMemoryRepository)
    employees.get.side_effect = [None, make_developer()]  # before/after add
    it = Department(1, "IT")
    departments.get.return_value = it
    departments.__iter__.return_value = iter([it])
    service = EmployeeService(employees, departments, MemoryNotifier())

    assert service.hire(make_developer(), 1)
    employees.add.assert_called_once()          # interaction is checked,
    departments.get.assert_called_once_with(1)  # but we had to script internals


def test_hire_with_fake_repository() -> None:
    employees: InMemoryRepository[Developer] = InMemoryRepository()
    departments: InMemoryRepository[Department] = InMemoryRepository()
    departments.add(Department(1, "IT"))
    service = EmployeeService(
        employees, departments, MemoryNotifier()  # type: ignore[arg-type]
    )

    assert service.hire(make_developer(), 1)
    assert [e.name for e in service.find_by_department("IT")] == ["Anna Koval"]
    assert 1 in departments[1]                  # final state is checked
