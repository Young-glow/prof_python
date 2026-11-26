"""Experiment 5: a flaky test and its deterministic version."""

import random

import pytest

from employee_domain.models import Developer
from employee_domain.policies import PercentageBonus
from employee_domain.value_objects import Email, Money


def random_bonus_percent() -> int:
    return random.randint(1, 2) * 5  # 5% or 10%


@pytest.mark.parametrize("attempt", range(20))
def test_bonus_flaky(attempt: int) -> None:
    assert random_bonus_percent() == 5  # depends on randomness


@pytest.mark.parametrize("attempt", range(20))
def test_bonus_deterministic(attempt: int, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(random, "randint", lambda a, b: 1)
    percent = random_bonus_percent()
    dev = Developer(1, "Anna Koval", Email("a@company.ua"), Money(52_000))
    assert PercentageBonus(percent).bonus_for(dev).amount == pytest.approx(2_600)
