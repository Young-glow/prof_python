"""Domain entities: Employee hierarchy, Department and PayrollRecord."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import total_ordering
from typing import ClassVar

from employee_domain.exceptions import (
    DepartmentError,
    EmployeeNotFoundError,
    ValidationError,
)
from employee_domain.value_objects import DeveloperLevel, Email, Money


@total_ordering
class Employee(ABC):
    """Abstract base entity of every employee (is-a root of the hierarchy)."""

    # class attributes: shared by all instances
    MIN_SALARY: ClassVar[Money] = Money(8000.0)
    MAX_NAME_LENGTH: ClassVar[int] = 50
    _created: ClassVar[int] = 0

    def __init__(
        self,
        employee_id: int,
        name: str,
        email: Email,
        salary: Money,
    ) -> None:
        if employee_id <= 0:
            raise ValidationError("Employee id must be positive")
        # instance attributes: belong to this object only
        self._id = employee_id
        self.name = name  # goes through the property setter
        self.email = email
        self.salary = salary  # goes through the property setter
        self._department: str | None = None
        Employee._created += 1

    # --- encapsulation through properties ---------------------------------
    @property
    def id(self) -> int:
        """Read-only identifier."""
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        value = value.strip()
        if not value:
            raise ValidationError("Name must not be empty")
        if len(value) > self.MAX_NAME_LENGTH:
            raise ValidationError("Name is too long")
        self._name = value

    @property
    def salary(self) -> Money:
        return self._salary

    @salary.setter
    def salary(self, value: Money) -> None:
        if value < self.MIN_SALARY:
            raise ValidationError(f"Salary must be at least {self.MIN_SALARY}")
        self._salary = value

    @property
    def department(self) -> str | None:
        """Department name; changed only by Department.add()/remove()."""
        return self._department

    def raise_salary(self, percent: float) -> None:
        """The object itself controls how its salary may change."""
        if not 0 < percent <= 50:
            raise ValidationError("Raise must be in range (0, 50] percent")
        self.salary = self.salary * (1 + percent / 100)

    # --- abstract interface ------------------------------------------------
    @property
    @abstractmethod
    def role(self) -> str:
        """Human-readable role of the employee."""

    @abstractmethod
    def monthly_pay(self) -> Money:
        """Full monthly pay: base salary plus role-specific part."""

    @classmethod
    def created_count(cls) -> int:
        return Employee._created

    # --- dunder methods ----------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(id={self.id!r}, name={self.name!r}, "
            f"salary={self.salary.amount!r})"
        )

    def __str__(self) -> str:
        department = self.department or "-"
        return f"#{self.id} {self.name} ({self.role}, {department}): {self.salary}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Employee):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __lt__(self, other: Employee) -> bool:
        return self.monthly_pay() < other.monthly_pay()


class Manager(Employee):
    """Manager is an Employee who leads a team and gets a bonus."""

    def __init__(
        self,
        employee_id: int,
        name: str,
        email: Email,
        salary: Money,
        team_size: int = 0,
        bonus_percent: float = 10.0,
    ) -> None:
        super().__init__(employee_id, name, email, salary)
        if team_size < 0:
            raise ValidationError("Team size cannot be negative")
        if not 0 <= bonus_percent <= 100:
            raise ValidationError("Bonus percent must be in range [0, 100]")
        self.team_size = team_size
        self.bonus_percent = bonus_percent

    @property
    def role(self) -> str:
        return "Manager"

    def monthly_pay(self) -> Money:
        return self.salary * (1 + self.bonus_percent / 100)


class Developer(Employee):
    """Developer is an Employee with a level and a set of skills."""

    LEVEL_ALLOWANCE: ClassVar[dict[DeveloperLevel, Money]] = {
        DeveloperLevel.JUNIOR: Money(0.0),
        DeveloperLevel.MIDDLE: Money(3000.0),
        DeveloperLevel.SENIOR: Money(7000.0),
    }

    def __init__(
        self,
        employee_id: int,
        name: str,
        email: Email,
        salary: Money,
        level: DeveloperLevel = DeveloperLevel.JUNIOR,
        skills: tuple[str, ...] = (),
    ) -> None:
        super().__init__(employee_id, name, email, salary)
        self.level = level
        self.skills = skills

    @property
    def role(self) -> str:
        return f"{self.level.value.capitalize()} Developer"

    def monthly_pay(self) -> Money:
        return self.salary + self.LEVEL_ALLOWANCE[self.level]


@dataclass
class Department:
    """Department has employees (composition) and behaves like a collection."""

    id: int
    name: str
    head: Manager | None = None
    _employees: dict[int, Employee] = field(default_factory=dict, repr=False)

    def add(self, employee: Employee) -> None:
        if employee.department is not None and employee.department != self.name:
            raise DepartmentError(
                f"{employee.name} already works in {employee.department}"
            )
        self._employees[employee.id] = employee
        employee._department = self.name

    def remove(self, employee_id: int) -> Employee:
        employee = self._employees.pop(employee_id, None)
        if employee is None:
            raise EmployeeNotFoundError(employee_id)
        employee._department = None
        if self.head is not None and self.head.id == employee_id:
            self.head = None
        return employee

    def assign_head(self, manager: Manager) -> None:
        if manager.id not in self:
            self.add(manager)
        self.head = manager
        manager.team_size = len(self) - 1

    @property
    def payroll(self) -> Money:
        total = Money.zero()
        for employee in self:
            total = total + employee.monthly_pay()
        return total

    # custom collection protocol
    def __len__(self) -> int:
        return len(self._employees)

    def __iter__(self) -> Iterator[Employee]:
        return iter(self._employees.values())

    def __contains__(self, item: object) -> bool:
        if isinstance(item, Employee):
            return item.id in self._employees
        return item in self._employees

    def __getitem__(self, employee_id: int) -> Employee:
        try:
            return self._employees[employee_id]
        except KeyError:
            raise EmployeeNotFoundError(employee_id) from None

    def __str__(self) -> str:
        head = self.head.name if self.head else "-"
        return f"{self.name} (head: {head}, employees: {len(self)})"


@dataclass(frozen=True, slots=True)
class PayrollRecord:
    """One line of the payroll sheet (immutable data object)."""

    employee_id: int
    name: str
    role: str
    department: str
    period: str
    base: Money
    bonus: Money

    @property
    def total(self) -> Money:
        return self.base + self.bonus

    def __str__(self) -> str:
        return (
            f"{self.period} | {self.name:<18} | {self.department:<8} | "
            f"{self.base!s:>13} + {self.bonus!s:>12} = {self.total!s:>13}"
        )
