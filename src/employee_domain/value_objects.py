"""Immutable value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import total_ordering

from employee_domain.exceptions import ValidationError


@total_ordering
@dataclass(frozen=True, slots=True)
class Money:
    """Amount of money in a currency (immutable value object)."""

    amount: float
    currency: str = "UAH"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValidationError("Money amount cannot be negative")
        if len(self.currency) != 3:
            raise ValidationError("Currency must be a 3-letter code")

    def _check_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValidationError("Currency mismatch")

    def __add__(self, other: Money) -> Money:
        self._check_currency(other)
        return Money(round(self.amount + other.amount, 2), self.currency)

    def __mul__(self, factor: float) -> Money:
        return Money(round(self.amount * factor, 2), self.currency)

    def __lt__(self, other: Money) -> bool:
        self._check_currency(other)
        return self.amount < other.amount

    def __str__(self) -> str:
        return f"{self.amount:,.2f} {self.currency}".replace(",", " ")

    @classmethod
    def zero(cls, currency: str = "UAH") -> Money:
        return cls(0.0, currency)


@dataclass(frozen=True, slots=True)
class Email:
    """Validated e-mail address."""

    value: str

    def __post_init__(self) -> None:
        if "@" not in self.value or self.value.startswith("@"):
            raise ValidationError(f"Invalid e-mail: {self.value!r}")

    def __str__(self) -> str:
        return self.value


class DeveloperLevel(str, Enum):
    """Qualification level of a developer."""

    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"
