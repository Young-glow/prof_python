"""Experiment 3 (step 1): only two of three branches are tested."""

import pytest
from salary_grades import classify_salary


@pytest.mark.parametrize(("amount", "grade"), [(68_000, "high"), (41_000, "medium")])
def test_classify(amount: float, grade: str) -> None:
    assert classify_salary(amount) == grade
