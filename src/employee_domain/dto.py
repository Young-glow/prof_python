"""External payloads (TypedDict) and their conversion into domain objects."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, NotRequired, TypeAlias, TypedDict

from employee_domain.exceptions import ValidationError
from employee_domain.models import Developer, Employee, Manager
from employee_domain.value_objects import DeveloperLevel, Email, Money

Role: TypeAlias = Literal["manager", "developer"]


class EmployeePayload(TypedDict):
    """JSON-like record that comes from outside (file, API)."""

    id: int
    name: str
    email: str
    salary: float
    role: Role
    department: str
    team_size: NotRequired[int]
    bonus_percent: NotRequired[float]
    level: NotRequired[str]
    skills: NotRequired[list[str]]


class DepartmentReport(TypedDict):
    """Report row; stays a plain dict at runtime (easy to dump to JSON)."""

    department: str
    head: str
    employees: int
    average_pay: float
    max_pay: float
    payroll: float


def _manager(data: EmployeePayload) -> Employee:
    return Manager(
        data["id"],
        data["name"],
        Email(data["email"]),
        Money(data["salary"]),
        team_size=data.get("team_size", 0),
        bonus_percent=data.get("bonus_percent", 10.0),
    )


def _developer(data: EmployeePayload) -> Employee:
    return Developer(
        data["id"],
        data["name"],
        Email(data["email"]),
        Money(data["salary"]),
        level=DeveloperLevel(data.get("level", "junior")),
        skills=tuple(data.get("skills", [])),
    )


# class factory: new role = new builder, the factory itself does not change
EMPLOYEE_BUILDERS: dict[str, Callable[[EmployeePayload], Employee]] = {
    "manager": _manager,
    "developer": _developer,
}


def employee_from_payload(data: EmployeePayload) -> Employee:
    builder = EMPLOYEE_BUILDERS.get(data["role"])
    if builder is None:
        raise ValidationError(f"Unknown role: {data['role']!r}")
    return builder(data)
