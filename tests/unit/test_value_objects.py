"""Unit tests: Money and Email value objects."""

import dataclasses

import pytest

from employee_domain.exceptions import ValidationError
from employee_domain.value_objects import Email, Money


def test_money_creation_keeps_amount_and_currency() -> None:
    money = Money(52_000)
    assert money.amount == 52_000
    assert money.currency == "UAH"


def test_money_is_immutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        Money(1).amount = 2  # type: ignore[misc]


@pytest.mark.parametrize(
    "amount",
    [pytest.param(0, id="zero"), pytest.param(0.01, id="one-kopeck"),
     pytest.param(1_000_000, id="large")],
)
def test_valid_money_amounts(amount: float) -> None:
    assert Money(amount).amount == pytest.approx(amount)


@pytest.mark.parametrize("amount", [-0.01, -1, -52_000])
def test_negative_money_is_rejected(amount: float) -> None:
    with pytest.raises(ValidationError, match="negative"):
        Money(amount)


def test_money_addition_and_multiplication() -> None:
    assert Money(0.1) + Money(0.2) == Money(0.3)  # rounded to kopecks
    assert (Money(52_000) * 1.15).amount == pytest.approx(59_800)


def test_currency_mismatch_is_rejected() -> None:
    with pytest.raises(ValidationError, match="Currency mismatch"):
        Money(100, "UAH") + Money(10, "USD")


def test_money_ordering_and_str() -> None:
    assert Money(100) < Money(200)
    assert max(Money(5), Money(50), Money(1)) == Money(50)
    assert str(Money(1_234.5)) == "1 234.50 UAH"


@pytest.mark.parametrize("value", ["", "anna.company.ua", "@company.ua"])
def test_invalid_email_is_rejected(value: str) -> None:
    with pytest.raises(ValidationError, match="Invalid e-mail"):
        Email(value)
