"""Experiment 2 (step 1): 100% coverage, but the result is never checked."""

from payroll_calc import total_payroll, total_payroll_fixed


def test_total_runs() -> None:
    total_payroll([1.0, 2.0])
    total_payroll_fixed([1.0, 2.0])
