"""Unit tests: EmployeeService with a fake repository and mocked dependencies."""

from unittest.mock import Mock, create_autospec

import pytest

from employee_domain.adapters import MemoryNotifier
from employee_domain.container import Container
from employee_domain.exceptions import DomainError, EmployeeNotFoundError
from employee_domain.models import Department, Employee
from employee_domain.protocols import Notifier
from employee_domain.repositories import InMemoryRepository
from employee_domain.services import EmployeeService
from employee_domain.value_objects import Money


def test_find_employees_by_department(container: Container) -> None:
    service = container.employee_service()
    it_names = {e.name for e in service.find_by_department("IT")}
    assert it_names == {"Anna Koval", "Iryna Bondar", "Taras Lysenko",
                        "Dmytro Savchenko"}
    assert [e.name for e in service.find_by_department("Finance")] == ["Kateryna Moroz"]
    assert service.find_by_department("HR") == []  # empty department


def test_salary_statistics(container: Container) -> None:
    service = container.employee_service()
    assert service.average_pay().amount == pytest.approx(291_840 / 5)
    best = service.highest_paid()
    assert best is not None and best.name == "Iryna Bondar"
    assert service.total_payroll().amount == pytest.approx(291_840)


def test_statistics_of_empty_repository() -> None:
    service = EmployeeService(InMemoryRepository(), InMemoryRepository(),
                              MemoryNotifier())
    assert service.average_pay() == Money(0)
    assert service.highest_paid() is None
    assert service.total_payroll() == Money(0)


def test_hire_sends_welcome_notification(developer: Employee) -> None:
    notifier = Mock(spec=Notifier)
    departments: InMemoryRepository[Department] = InMemoryRepository()
    departments.add(Department(1, "IT"))
    service = EmployeeService(InMemoryRepository(), departments, notifier)

    result = service.hire(developer, 1)

    assert result.success and result.value is developer
    assert developer.department == "IT"
    notifier.send.assert_called_once_with(
        "user1@company.ua", "Welcome, Anna Koval! Role: Middle Developer"
    )


def test_failed_hire_does_not_notify(container: Container,
                                     employee_factory: object) -> None:
    notifier = Mock(spec=Notifier)
    service = EmployeeService(container.employees, container.departments, notifier)
    duplicate = container.employees[1]
    result = service.hire(duplicate, 1)
    assert not result and "already exists" in str(result.error)
    unknown_department = service.hire(
        container.employees[1].__class__(
            20, "Olena Kravets", duplicate.email, Money(30_000)
        ),
        99,
    )
    assert unknown_department.error == "Department with id=99 not found"
    assert 20 not in container.employees  # rolled back
    notifier.send.assert_not_called()


def test_transfer_notifies_with_exact_message(container: Container) -> None:
    notifier = Mock(spec=Notifier)
    service = EmployeeService(container.employees, container.departments, notifier)
    service.assign_department(9, 3)
    assert service.get(9).department == "HR"
    notifier.send.assert_called_once_with(
        "user9@company.ua", "You moved from Finance to HR"
    )


def test_repository_mock_return_value_none_raises() -> None:
    employees = Mock(spec=InMemoryRepository)
    employees.get.return_value = None
    service = EmployeeService(employees, Mock(spec=InMemoryRepository),
                              Mock(spec=Notifier))
    with pytest.raises(EmployeeNotFoundError, match="id=42"):
        service.assign_department(42, 1)
    employees.get.assert_called_once_with(42)


def test_repository_failure_propagates_via_side_effect() -> None:
    employees = Mock(spec=InMemoryRepository)
    employees.find.side_effect = DomainError("storage is offline")
    service = EmployeeService(employees, Mock(spec=InMemoryRepository),
                              Mock(spec=Notifier))
    with pytest.raises(DomainError, match="offline"):
        service.find_by_department("IT")
    employees.find.assert_called_once()


def test_autospec_checks_method_signature() -> None:
    notifier = create_autospec(MemoryNotifier, instance=True)
    notifier.send("hr@company.ua", "ok")
    notifier.send.assert_called_once_with("hr@company.ua", "ok")
    with pytest.raises(TypeError):
        notifier.send("only-one-argument")  # a plain Mock would accept this
