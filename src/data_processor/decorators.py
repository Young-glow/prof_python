"""Decorators: execution time measurement and operation history."""

from collections import deque
from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

# deque: keeps only the last 5 operations, old ones drop out automatically
operation_history: deque[str] = deque(maxlen=5)

# dict: last measured execution time of each function, seconds
timings: dict[str, float] = {}


def measure_time(func: F) -> F:
    """Measure and remember how long the decorated function runs."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = perf_counter()
        result = func(*args, **kwargs)
        timings[func.__name__] = perf_counter() - start
        return result

    return wrapper  # type: ignore[return-value]


def log_operation(label: str) -> Callable[[F], F]:
    """Parametrized decorator: write `label` to the operation history."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            operation_history.append(f"{label}: {func.__name__}")
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
