"""Experiment 3 (step 2): all branches and boundaries."""

import pytest
from salary_grades import classify_salary


@pytest.mark.parametrize(
    ("amount", "grade"),
    [(68_000, "high"), (60_000, "high"), (59_999.99, "medium"), (41_000, "medium"),
     (30_000, "medium"), (29_999.99, "low"), (27_500, "low")],
)
def test_classify(amount: float, grade: str) -> None:
    assert classify_salary(amount) == grade
