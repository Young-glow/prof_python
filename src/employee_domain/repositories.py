"""Generic in-memory repository."""

from collections.abc import Callable, Iterator
from typing import Generic

from employee_domain.exceptions import DomainError
from employee_domain.protocols import T


class InMemoryRepository(Generic[T]):
    """Stores any objects with an integer ``id`` in a dict (O(1) access)."""

    def __init__(self) -> None:
        self._items: dict[int, T] = {}

    def add(self, item: T) -> None:
        if item.id in self._items:
            raise DomainError(f"Item with id={item.id} already exists")
        self._items[item.id] = item

    def get(self, item_id: int) -> T | None:
        return self._items.get(item_id)

    def all(self) -> list[T]:
        return list(self._items.values())

    def remove(self, item_id: int) -> bool:
        return self._items.pop(item_id, None) is not None

    def find(self, predicate: Callable[[T], bool]) -> list[T]:
        return [item for item in self._items.values() if predicate(item)]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items.values())

    def __contains__(self, item_id: object) -> bool:
        return item_id in self._items

    def __getitem__(self, item_id: int) -> T:
        return self._items[item_id]
