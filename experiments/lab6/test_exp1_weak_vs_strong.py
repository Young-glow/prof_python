"""Experiment 1: execution is not verification."""

import pytest
from payroll_calc import total_payroll


def test_total_payroll_weak() -> None:
    total_payroll([52_000, 31_000, 68_000])  # no assert: passes despite the bug


def test_total_payroll_strong() -> None:
    assert total_payroll([52_000, 31_000, 68_000]) == pytest.approx(151_000)
