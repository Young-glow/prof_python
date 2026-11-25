"""Shared fixtures of the laboratory work 6 test suite.

pytest finds this file automatically, tests never import it.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from employee_domain.adapters import MemoryNotifier
from employee_domain.container import Container
from employee_domain.models import Department, Developer, Employee, Manager
from employee_domain.value_objects import DeveloperLevel, Email, Money

EmployeeFactory = Callable[..., Employee]

STAFF_CSV = (
    "employee_id,name,position,department,salary\n"
    "1,Anna Koval,Python Developer,IT,52000\n"
    "2,Oleh Melnyk,Accountant,Finance,31000\n"
    "3,Iryna Bondar,Team Lead,IT,68000\n"
    "4,Sofiia Hnatiuk,HR Specialist,HR,27500\n"
    "5,,Recruiter,HR,29000\n"
    "abc,Petro Novak,Sales Manager,Sales,35000\n"
)

CONFIG_TEMPLATE = """version: 1
input:
  path: staff.csv
output:
  path: out/employees.{fmt}
  format: {fmt}
  errors_path: out/errors.csv
  summary_path: out/summary.json
  backup: true
processing:
  minimum_salary: {minimum}
  skip_invalid: {skip}
  allowed_departments: [IT, Finance, HR, Sales]
logging:
  level: INFO
  path: logs/importer.log
"""


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Autouse: real EMPLOYEE_IMPORTER_* variables never leak into tests."""
    for name in ("MIN_SALARY", "SKIP_INVALID", "LOG_LEVEL"):
        monkeypatch.delenv(f"EMPLOYEE_IMPORTER_{name}", raising=False)


@pytest.fixture
def employee_factory() -> EmployeeFactory:
    """Fixture factory: builds employees with sensible defaults."""

    def create(
        *,
        employee_id: int = 1,
        name: str = "Anna Koval",
        salary: float = 52_000,
        role: str = "developer",
        level: DeveloperLevel = DeveloperLevel.MIDDLE,
        bonus_percent: float = 10.0,
    ) -> Employee:
        email = Email(f"user{employee_id}@company.ua")
        if role == "manager":
            return Manager(
                employee_id, name, email, Money(salary), bonus_percent=bonus_percent
            )
        return Developer(employee_id, name, email, Money(salary), level=level)

    return create


@pytest.fixture
def developer(employee_factory: EmployeeFactory) -> Employee:
    return employee_factory()


@pytest.fixture
def manager(employee_factory: EmployeeFactory) -> Manager:
    employee = employee_factory(
        employee_id=3, name="Iryna Bondar", salary=68_000, role="manager",
        bonus_percent=15,
    )
    assert isinstance(employee, Manager)
    return employee


@pytest.fixture
def staff(employee_factory: EmployeeFactory) -> list[Employee]:
    """Five employees, total monthly pay = 289 640 UAH."""
    return [
        employee_factory(employee_id=1, name="Anna Koval", salary=52_000),
        employee_factory(employee_id=3, name="Iryna Bondar", salary=68_000,
                         role="manager", bonus_percent=15),
        employee_factory(employee_id=6, name="Taras Lysenko", salary=38_000,
                         level=DeveloperLevel.JUNIOR),
        employee_factory(employee_id=8, name="Dmytro Savchenko", salary=61_000,
                         level=DeveloperLevel.SENIOR),
        employee_factory(employee_id=9, name="Kateryna Moroz", salary=47_000,
                         role="manager", bonus_percent=12),
    ]


@pytest.fixture
def container(staff: list[Employee]) -> Container:
    """Application with real in-memory repositories (fakes) and MemoryNotifier."""
    app = Container(notifier=MemoryNotifier())
    app.departments.add(Department(1, "IT"))
    app.departments.add(Department(2, "Finance"))
    app.departments.add(Department(3, "HR"))
    service = app.employee_service()
    for employee in staff:
        department = 2 if employee.id == 9 else 1
        assert service.hire(employee, department)
    return app


@pytest.fixture
def staff_csv(tmp_path: Path) -> Path:
    path = tmp_path / "staff.csv"
    path.write_text(STAFF_CSV, encoding="utf-8")
    return path


@pytest.fixture
def make_config(staff_csv: Path) -> Callable[..., Path]:
    """Factory: writes config.yaml next to staff.csv inside tmp_path."""

    def create(fmt: str = "json", minimum: float = 30_000, skip: bool = True) -> Path:
        path = staff_csv.parent / "config.yaml"
        text = CONFIG_TEMPLATE.format(fmt=fmt, minimum=minimum, skip=str(skip).lower())
        path.write_text(text, encoding="utf-8")
        return path

    return create


@pytest.fixture(params=["json", "jsonl", "csv"], ids=["to-json", "to-jsonl", "to-csv"])
def output_format(request: pytest.FixtureRequest) -> str:
    """Parameterized fixture: every dependent test runs for three formats."""
    return str(request.param)


@pytest.fixture
def importer_logging(tmp_path: Path) -> Iterator[Path]:
    """Setup + teardown: log into tmp_path, then remove and close the handlers."""
    from employee_importer.config import LoggingConfig
    from employee_importer.logging_config import configure_logging

    log_file = tmp_path / "logs" / "test.log"
    configure_logging(LoggingConfig("INFO", log_file, 10_000, 1))
    yield log_file
    root = logging.getLogger()
    for handler in list(root.handlers):
        handler.close()
        root.removeHandler(handler)
