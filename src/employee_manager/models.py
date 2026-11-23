"""Data models of the application."""

from dataclasses import dataclass

from employee_manager.config import MAX_NAME_LENGTH, MIN_SALARY
from employee_manager.exceptions import InvalidEmployeeDataError


@dataclass
class Employee:
    """Employee of the company."""

    name: str
    position: str
    department: str
    salary: float

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.position = self.position.strip()
        self.department = self.department.strip()

        for field_name in ("name", "position", "department"):
            value: str = getattr(self, field_name)
            if not value:
                raise InvalidEmployeeDataError(
                    f"Field '{field_name}' must not be empty."
                )
            if len(value) > MAX_NAME_LENGTH:
                raise InvalidEmployeeDataError(
                    f"Field '{field_name}' is longer than "
                    f"{MAX_NAME_LENGTH} characters."
                )

        if self.salary < MIN_SALARY:
            raise InvalidEmployeeDataError(
                f"Salary must be at least {MIN_SALARY:.2f}."
            )
