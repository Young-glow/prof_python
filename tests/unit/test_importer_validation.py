"""Unit tests: validation of external employee rows (lab 5 importer)."""

from typing import Any

import pytest

from employee_importer.exceptions import RecordValidationError
from employee_importer.models import Employee
from employee_importer.validators import (
    StrictPolicy,
    TolerantPolicy,
    parse_employee,
    policy_for,
)

ALLOWED = {"IT", "Finance", "HR", "Sales"}
VALID: dict[str, Any] = {
    "employee_id": "1", "name": "anna  koval", "position": "Python Developer",
    "department": "IT", "salary": "52000",
}


def parse(**changes: Any) -> Employee:
    return parse_employee({**VALID, **changes}, line_number=7,
                          allowed_departments=ALLOWED)


def test_valid_row_becomes_domain_object() -> None:
    assert parse() == Employee(1, "Anna Koval", "Python Developer", "IT", 52_000.0)


@pytest.mark.parametrize(
    "salary", ["0", "0.01", "999999.99"], ids=["zero", "min-positive", "large"]
)
def test_salary_boundaries_accepted(salary: str) -> None:
    assert parse(salary=salary).salary == pytest.approx(float(salary))


@pytest.mark.parametrize(
    ("changes", "field", "message"),
    [
        ({"salary": "-0.01"}, "salary", "Salary must be >= 0"),
        ({"salary": "n/a"}, "salary", "Salary must be a number"),
        ({"salary": "nan"}, "salary", "finite"),
        ({"salary": "inf"}, "salary", "finite"),
        ({"employee_id": "abc"}, "employee_id", "must be an integer"),
        ({"employee_id": "0"}, "employee_id", "must be positive"),
        ({"name": ""}, "name", "Name is empty"),
        ({"name": "R2-D2"}, "name", "invalid characters"),
        ({"position": "  "}, "position", "Position is empty"),
        ({"department": "Marketing"}, "department", "not allowed"),
    ],
    ids=["negative-salary", "text-salary", "nan-salary", "inf-salary", "text-id",
         "zero-id", "empty-name", "digits-in-name", "blank-position", "bad-dept"],
)
def test_invalid_row_raises_custom_exception(
    changes: dict[str, str], field: str, message: str
) -> None:
    with pytest.raises(RecordValidationError, match=message) as exc_info:
        parse(**changes)
    assert exc_info.value.field == field
    assert exc_info.value.line_number == 7


def test_missing_column_and_exception_chaining() -> None:
    row = {k: v for k, v in VALID.items() if k != "salary"}
    with pytest.raises(RecordValidationError) as exc_info:
        parse_employee(row, line_number=3, allowed_departments=ALLOWED)
    assert isinstance(exc_info.value.__cause__, KeyError)
    assert str(exc_info.value) == "line 3, field 'salary': Salary must be a number"


def test_salary_value_is_not_leaked_in_error() -> None:
    with pytest.raises(RecordValidationError) as exc_info:
        parse(salary="secret-52000")
    assert "52000" not in str(exc_info.value)


def test_policies() -> None:
    error = RecordValidationError("bad", line_number=1, field="name")
    assert isinstance(policy_for(True), TolerantPolicy)
    assert isinstance(policy_for(False), StrictPolicy)
    assert TolerantPolicy().handle(error) is None
    with pytest.raises(RecordValidationError):
        StrictPolicy().handle(error)


@pytest.mark.parametrize("column", ["name", "position", "department"])
def test_missing_text_column_is_reported(column: str) -> None:
    """Added after coverage showed that the KeyError branch was never executed."""
    row = {k: v for k, v in VALID.items() if k != column}
    message = f"Missing column '{column}'"
    with pytest.raises(RecordValidationError, match=message) as info:
        parse_employee(row, line_number=4, allowed_departments=ALLOWED)
    assert isinstance(info.value.__cause__, KeyError)
