"""Benchmark: search by id in a list (O(n)) versus a dict index (O(1))."""

import random
from time import perf_counter

from data_processor.data import generate_employees
from data_processor.processors import create_employee_index, find_linear

SIZES: tuple[int, ...] = (1_000, 10_000, 100_000)
SEARCHES = 200


def run_benchmark(
    sizes: tuple[int, ...] = SIZES,
    searches: int = SEARCHES,
) -> list[tuple[int, float, float, float]]:
    """Return (size, list search, dict search, index build) times in seconds.

    Search times are averages for one search of a random id.
    """
    results = []
    generator = random.Random(1)
    for size in sizes:
        data = generate_employees(size)
        ids = [generator.randint(1, size) for _ in range(searches)]

        start = perf_counter()
        for employee_id in ids:
            find_linear(data, employee_id)
        list_time = (perf_counter() - start) / searches

        start = perf_counter()
        index = create_employee_index(data)
        build_time = perf_counter() - start

        start = perf_counter()
        for employee_id in ids:
            index.get(employee_id)
        dict_time = (perf_counter() - start) / searches

        results.append((size, list_time, dict_time, build_time))
    return results


def print_benchmark() -> None:
    print(f"Search of a random id, average of {SEARCHES} searches")
    print(f"{'records':>9} {'list, s':>12} {'dict, s':>12} "
          f"{'ratio':>9} {'build index, s':>15}")
    for size, list_time, dict_time, build_time in run_benchmark():
        print(f"{size:9d} {list_time:12.2e} {dict_time:12.2e} "
              f"{list_time / dict_time:9.0f} {build_time:15.2e}")
