"""Experiment 2 (step 2): the same coverage with meaningful assertions."""

import pytest
from payroll_calc import total_payroll, total_payroll_fixed


@pytest.mark.parametrize("function", [total_payroll, total_payroll_fixed])
def test_total_is_sum(function: object) -> None:
    assert function([52_000, 31_000]) == pytest.approx(83_000)  # type: ignore[operator]
