"""Entry point: demonstrates all features of laboratory work 2 (variant 6)."""

import argparse

from data_processor.analytics import (
    average,
    average_salary_by_department,
    build_summary,
    calculate_average_salary,
    calculate_payroll,
    create_record,
    find_highest_paid,
    pipeline,
    salary_range,
    sort_items,
)
from data_processor.benchmark import print_benchmark
from data_processor.data import Employee, employees
from data_processor.decorators import operation_history, timings
from data_processor.processors import (
    count_by_department,
    create_department_filter,
    create_employee_index,
    create_salary_filter,
    filter_items,
    find_by_name,
    get_unique_departments,
    group_by,
    group_nested,
)

LINE = "-" * 66


def print_employees(title: str, items: list[Employee]) -> None:
    """Print employees as a table."""
    print(f"\n{title}")
    print(LINE)
    for e in items:
        print(
            f"{e['id']:3} {e['name']:20} {e['position']:20} "
            f"{e['department']:8} {e['salary']:10.2f}"
        )


def demo_structures() -> None:
    print("\n=== Unique departments (set) ===")
    departments = get_unique_departments(employees)
    print(sorted(departments))
    print(f"'IT' in departments: {'IT' in departments}")

    print("\n=== Counter by department ===")
    for department, count in count_by_department(employees).most_common():
        print(f"{department:8} {count}")

    print("\n=== Grouping by department (defaultdict) ===")
    for department, members in group_by(employees, "department").items():
        names = ", ".join(str(e["name"]) for e in members)
        print(f"{department:8} -> {names}")

    print("\n=== Nested grouping: department -> position ===")
    for department, positions in group_nested(
        employees, "department", "position"
    ).items():
        inner = {position: len(people) for position, people in positions.items()}
        print(f"{department:8} {inner}")


def demo_aggregation() -> None:
    print("\n=== Aggregation ===")
    print(f"Average salary: {calculate_average_salary(employees):.2f} UAH")
    print(f"Total payroll fund: {calculate_payroll(employees):.2f} UAH")
    low, high = salary_range(employees)
    print(f"Salary range (tuple): ({low:.2f}, {high:.2f})")
    best = find_highest_paid(employees)
    if best is not None:
        print(f"Highest paid: {best['name']}, {best['position']} "
              f"({best['salary']:.2f} UAH)")

    print("\n=== Average salary by department ===")
    for department, value in sorted(
        average_salary_by_department(employees).items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(f"{department:8} {value:10.2f}")


def demo_search_filter_sort() -> None:
    index = create_employee_index(employees)
    print("\n=== Search ===")
    print(f"By id 8 (dict index): {index.get(8)}")
    print(f"By name 'enko': {[e['name'] for e in find_by_name(employees, 'enko')]}")

    is_well_paid = create_salary_filter(50000)
    print_employees("Salary >= 50000 (closure filter)",
                    filter_items(employees, is_well_paid))

    in_range = create_salary_filter(30000, 40000)
    print_employees("Salary from 30000 to 40000",
                    filter_items(employees, in_range))

    print_employees("Ranking by salary (sort with lambda)",
                    sort_items(employees, "salary", reverse=True))

    it_sorted = pipeline(
        employees,
        lambda items: filter_items(items, create_department_filter("IT")),
        lambda items: sort_items(items, "salary"),
    )
    print_employees("Pipeline: IT -> sort by salary", it_sorted)


def demo_functions() -> None:
    print("\n=== *args and **kwargs ===")
    print(f"average(52000, 31000, 68000) = {average(52000, 31000, 68000):.2f}")
    new_employee = create_record(
        id=13, name="Viktoriia Rudenko", position="Designer",
        department="Marketing", salary=36000.0,
    )
    print(f"create_record(**kwargs) -> {new_employee}")

    print("\n=== Summary (export) ===")
    for key, value in build_summary(employees).items():
        print(f"{key:15}: {value}")

    print("\n=== Decorators ===")
    for name, seconds in timings.items():
        print(f"@measure_time {name}: {seconds:.8f} s")
    print("@log_operation, last 5 operations (deque):")
    for operation in operation_history:
        print(f"  {operation}")


SECTIONS = ("structures", "aggregation", "search", "functions")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="data-processor",
        description="Employee data processing (laboratory work 2, variant 6).",
    )
    parser.add_argument("--benchmark", action="store_true",
                        help="compare list and dict search")
    parser.add_argument("--section", choices=SECTIONS,
                        help="show only one part of the demo")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.benchmark:
        print_benchmark()
        return
    print("Data Processor (laboratory work 2, variant 6)")
    parts = {
        "structures": demo_structures,
        "aggregation": demo_aggregation,
        "search": demo_search_filter_sort,
        "functions": demo_functions,
    }
    if args.section is not None:
        parts[args.section]()
        return
    print_employees("All employees (list of dict)", employees)
    for show in parts.values():
        show()


if __name__ == "__main__":
    main()
