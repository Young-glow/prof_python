"""Domain object, invalid-record description and import statistics."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field

FIELDS: tuple[str, ...] = ("employee_id", "name", "position", "department", "salary")


@dataclass(frozen=True, slots=True)
class Employee:
    """Validated employee record (domain object)."""

    employee_id: int
    name: str
    position: str
    department: str
    salary: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class InvalidRecord:
    """Rejected input row for the error report (salary is never stored)."""

    line_number: int
    field: str
    message: str
    employee_id: str


@dataclass
class ImportStatistics:
    """Counters that are filled while the stream is processed."""

    total: int = 0
    valid: int = 0
    invalid: int = 0
    filtered_out: int = 0
    exported: int = 0
    errors_by_field: Counter[str] = field(default_factory=Counter)

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["errors_by_field"] = dict(self.errors_by_field)
        return data
