"""Tests of laboratory work 4 (OOP model and services)."""

import pytest

from employee_domain.adapters import JsonReportExporter, MemoryNotifier
from employee_domain.container import Container
from employee_domain.dto import employee_from_payload
from employee_domain.exceptions import ValidationError
from employee_domain.generics import clamp, first
from employee_domain.models import Department, Developer, Manager
from employee_domain.policies import ManagerOnlyBonus, NoBonus, PercentageBonus
from employee_domain.protocols import BonusPolicy, ReportExporter
from employee_domain.repositories import InMemoryRepository
from employee_domain.seed import DEPARTMENTS, PAYLOADS
from employee_domain.value_objects import DeveloperLevel, Email, Money


def make_container(policy: BonusPolicy | None = None) -> Container:
    container = Container(notifier=MemoryNotifier())
    if policy is not None:
        container.bonus_policy = policy
    for dep_id, name in DEPARTMENTS.items():
        container.departments.add(Department(dep_id, name))
    service = container.employee_service()
    by_name = {name: dep_id for dep_id, name in DEPARTMENTS.items()}
    for payload in PAYLOADS:
        result = service.hire(employee_from_payload(payload),
                              by_name[payload["department"]])
        assert result.success
    return container


def test_money_is_immutable_value_object() -> None:
    money = Money(100)
    with pytest.raises(AttributeError):
        money.amount = 5  # type: ignore[misc]
    assert Money(100) == money
    assert str(Money(1500) + Money(250.5)) == "1 750.50 UAH"
    with pytest.raises(ValidationError):
        Money(-1)
    with pytest.raises(ValidationError):
        Money(1, "UAH") + Money(1, "USD")


def test_salary_property_validates() -> None:
    dev = Developer(1, "Anna", Email("a@b.ua"), Money(20000))
    with pytest.raises(ValidationError):
        dev.salary = Money(100)
    dev.raise_salary(10)
    assert dev.salary == Money(22000)


def test_inheritance_and_polymorphism() -> None:
    manager = Manager(2, "Iryna", Email("i@b.ua"), Money(60000), bonus_percent=10)
    senior = Developer(3, "Dmytro", Email("d@b.ua"), Money(60000),
                       DeveloperLevel.SENIOR)
    assert manager.monthly_pay() == Money(66000)
    assert senior.monthly_pay() == Money(67000)
    assert max([manager, senior]) is senior  # __lt__ + total_ordering


def test_department_collection_dunders() -> None:
    department = Department(1, "IT")
    dev = Developer(1, "Anna", Email("a@b.ua"), Money(20000))
    department.add(dev)
    assert len(department) == 1
    assert 1 in department and dev in department
    assert department[1] is dev
    assert list(department) == [dev]
    assert dev.department == "IT"


def test_generic_repository() -> None:
    repo: InMemoryRepository[Department] = InMemoryRepository()
    repo.add(Department(1, "IT"))
    assert repo.get(1) is not None and len(repo) == 1
    assert repo.remove(1) and repo.get(1) is None


def test_service_statistics() -> None:
    service = make_container().employee_service()
    assert len(service.find_by_department("IT")) == 5
    best = service.highest_paid()
    assert best is not None and best.name == "Iryna Bondar"
    assert service.total_payroll() == Money(419160.0)


def test_transfer_between_departments_notifies() -> None:
    container = make_container()
    service = container.employee_service()
    service.assign_department(5, 1)
    assert service.get(5).department == "IT"
    assert 5 not in container.departments[2]
    assert isinstance(container.notifier, MemoryNotifier)
    assert "moved from Finance to IT" in container.notifier.messages[-1][1]


def test_hire_duplicate_returns_error_result() -> None:
    service = make_container().employee_service()
    result = service.hire(employee_from_payload(PAYLOADS[0]), 1)
    assert not result and result.error is not None


@pytest.mark.parametrize(
    ("policy", "expected"),
    [(NoBonus(), 385000.0), (PercentageBonus(10), 423500.0),
     (ManagerOnlyBonus(Money(5000)), 400000.0)],
)
def test_bonus_strategies(policy: BonusPolicy, expected: float) -> None:
    container = make_container(policy)
    payroll = container.payroll_service()
    records = payroll.build(container.employees, "2026-11")
    assert payroll.total(records) == Money(expected)


def test_report_exporter_protocol() -> None:
    exporter = JsonReportExporter()
    assert isinstance(exporter, ReportExporter)  # runtime_checkable
    text = make_container().report_service().export(exporter)
    assert '"department": "IT"' in text


def test_generic_helpers() -> None:
    assert first([3, 4]) == 3 and first([]) is None
    assert clamp(15, 0, 10) == 10 and clamp(0.5, 1.0, 2.0) == 1.0


def test_failed_hire_keeps_existing_employee() -> None:
    container = make_container()
    service = container.employee_service()
    service.hire(employee_from_payload(PAYLOADS[0]), 1)
    assert service.get(1).name == "Anna Koval"
    assert len(container.employees) == len(PAYLOADS)
