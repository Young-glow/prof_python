"""Experiment 1-2: a payroll helper with a deliberate defect."""


def total_payroll(salaries: list[float]) -> float:
    """Should return the sum of all salaries (BUG: the last one is skipped)."""
    total = 0.0
    for salary in salaries[:-1]:  # deliberate off-by-one defect
        total += salary
    return total


def total_payroll_fixed(salaries: list[float]) -> float:
    return float(sum(salaries))
