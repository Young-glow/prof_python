"""Concrete bonus policies (strategy pattern, OCP)."""

from employee_domain.exceptions import ValidationError
from employee_domain.models import Employee, Manager
from employee_domain.protocols import BonusPolicy
from employee_domain.value_objects import Money


class NoBonus(BonusPolicy):
    def bonus_for(self, employee: Employee) -> Money:
        return Money.zero(employee.salary.currency)


class RoleBonus(BonusPolicy):
    """Bonus defined by the role itself: monthly_pay() - salary."""

    def bonus_for(self, employee: Employee) -> Money:
        extra = employee.monthly_pay().amount - employee.salary.amount
        return Money(round(extra, 2), employee.salary.currency)


class PercentageBonus(BonusPolicy):
    """The same percent of the base salary for everyone."""

    def __init__(self, percent: float) -> None:
        if not 0 <= percent <= 100:
            raise ValidationError("Invalid percent")
        self.percent = percent

    def bonus_for(self, employee: Employee) -> Money:
        return employee.salary * (self.percent / 100)

    @property
    def name(self) -> str:
        return f"PercentageBonus({self.percent:g}%)"


class ManagerOnlyBonus(BonusPolicy):
    """Added later without changing PayrollService (open/closed)."""

    def __init__(self, amount: Money) -> None:
        self.amount = amount

    def bonus_for(self, employee: Employee) -> Money:
        if isinstance(employee, Manager):
            return self.amount
        return Money.zero(employee.salary.currency)
