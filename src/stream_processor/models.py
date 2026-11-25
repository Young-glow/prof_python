"""Record type passed between pipeline stages."""

from typing import NamedTuple

CSV_HEADER: tuple[str, ...] = (
    "employee_id", "name", "position", "department", "salary",
)


class EmployeeRecord(NamedTuple):
    """One valid employee record (immutable, lightweight)."""

    employee_id: int
    name: str
    position: str
    department: str
    salary: float
