"""Abstractions of the domain: Protocols (structural typing) and an ABC."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Protocol, TypeVar, runtime_checkable

if TYPE_CHECKING:
    from employee_domain.dto import DepartmentReport
    from employee_domain.models import Employee
    from employee_domain.value_objects import Money


class HasId(Protocol):
    """Anything that has an integer identifier."""

    @property
    def id(self) -> int: ...


T = TypeVar("T", bound=HasId)  # bound TypeVar: only objects with .id


class Repository(Protocol[T]):
    """Repository abstraction (the service depends on it, not on storage)."""

    def add(self, item: T) -> None: ...

    def get(self, item_id: int) -> T | None: ...

    def all(self) -> list[T]: ...

    def remove(self, item_id: int) -> bool: ...

    def find(self, predicate: Callable[[T], bool]) -> list[T]: ...

    def __len__(self) -> int: ...

    def __iter__(self) -> Iterator[T]: ...


# Interface segregation: two small protocols instead of one big "Output".
class Notifier(Protocol):
    """Sends a short message to a recipient."""

    def send(self, recipient: str, message: str) -> None: ...


@runtime_checkable
class ReportExporter(Protocol):
    """Turns a department report into text (console table, JSON, ...)."""

    def export(self, reports: list[DepartmentReport]) -> str: ...


class BonusPolicy(ABC):
    """Strategy of bonus calculation (nominal interface through ABC)."""

    @abstractmethod
    def bonus_for(self, employee: Employee) -> Money:
        """Return the bonus of the employee for one month."""

    @property
    def name(self) -> str:
        return type(self).__name__
