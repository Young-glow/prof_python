"""Custom exception hierarchy of the domain."""


class DomainError(Exception):
    """Base class for all domain errors."""


class ValidationError(DomainError):
    """Raised when an object would get an invalid state."""


class EmployeeNotFoundError(DomainError):
    """Raised when an employee with the given id does not exist."""

    def __init__(self, employee_id: int) -> None:
        super().__init__(f"Employee with id={employee_id} not found")
        self.employee_id = employee_id


class DepartmentError(DomainError):
    """Raised on invalid operations with a department."""
