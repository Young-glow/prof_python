"""Custom exceptions of the application."""


class EmployeeError(Exception):
    """Base exception for the employee manager."""


class InvalidEmployeeDataError(EmployeeError):
    """Raised when employee data does not pass validation."""
