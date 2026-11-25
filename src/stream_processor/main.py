"""Entry point: streaming processing of employee data (lab 3, variant 6)."""

import argparse
from collections import Counter
from itertools import chain, islice
from pathlib import Path

from stream_processor.analytics import (
    calculate_statistics,
    count_by_level,
    running_payroll,
    salary_differences,
    take_until_payroll,
)
from stream_processor.batches import batched
from stream_processor.experiment import print_early_termination, print_experiment
from stream_processor.export import export_batches
from stream_processor.iterators import SalaryRange, flatten
from stream_processor.models import EmployeeRecord
from stream_processor.pipeline import build_pipeline, find_first, stage_log
from stream_processor.readers import employee_ids

SAMPLE = Path("data/employees.csv")
EXPORT = Path("data/generated/high_salary_export.csv")


def show(employee: EmployeeRecord) -> str:
    return (f"{employee.employee_id:3} {employee.name:20} {employee.position:20} "
            f"{employee.department:10} {employee.salary:10.2f}")


def demo_pipeline() -> None:
    print("=== Lazy pipeline: read -> clean -> parse -> validate -> "
          "normalize -> filter ===")
    pipeline = build_pipeline(SAMPLE, min_salary=40000)
    print(f"Pipeline object: {type(pipeline).__name__} (nothing read yet)")
    print("\nFirst 3 employees with salary >= 40000 (islice):")
    for employee in islice(pipeline, 3):
        print(show(employee))

    print("\nIT department, all salaries:")
    for employee in build_pipeline(SAMPLE, departments=("IT",)):
        print(show(employee))

    errors: Counter[str] = Counter()
    stage_log.clear()
    stats = calculate_statistics(build_pipeline(SAMPLE, errors=errors))
    print("\n=== Streaming statistics (one pass) ===")
    print(f"Valid employees: {stats.count}")
    print(f"Invalid records: {sum(errors.values())} {dict(errors)}")
    print(f"Average salary: {stats.average_salary:.2f} UAH")
    print(f"Payroll fund: {stats.payroll:.2f} UAH")
    if stats.highest_paid is not None:
        print(f"Highest paid: {stats.highest_paid.name} "
              f"({stats.highest_paid.salary:.2f} UAH)")
    print(f"Employees by department: {dict(stats.departments.most_common())}")
    print(f"Stage log: {stage_log}")


def demo_itertools() -> None:
    print("=== itertools ===")
    payroll = list(running_payroll(build_pipeline(SAMPLE)))
    print(f"accumulate (running payroll): {payroll[:5]} ... {payroll[-1]:.0f}")
    print(f"pairwise (salary differences): "
          f"{list(islice(salary_differences(build_pipeline(SAMPLE)), 5))}")
    print(f"groupby (salary levels): {count_by_level(build_pipeline(SAMPLE))}")
    print(f"takewhile (payroll <= 150000): "
          f"{take_until_payroll(build_pipeline(SAMPLE), 150000)}")
    combined = chain(build_pipeline(SAMPLE, departments=("HR",)),
                     build_pipeline(SAMPLE, departments=("Sales",)))
    print(f"chain (HR + Sales): {[e.name for e in combined]}")
    print(f"count + islice (new ids): {list(islice(employee_ids(100), 5))}")
    two_files = build_pipeline([SAMPLE, SAMPLE])
    print(f"read_many (2 files via chain): {sum(1 for _ in two_files)} records")
    total = sum(e.salary for e in build_pipeline(SAMPLE, departments=("Finance",)))
    print(f"generator expression (Finance payroll): {total:.2f}")
    first = find_first(build_pipeline(SAMPLE), 60000)
    print(f"find_first salary >= 60000 (early termination): "
          f"{first.name if first else None}")


def demo_iterators() -> None:
    print("=== iterable vs iterator ===")
    levels = SalaryRange(20000, 70000, 10000)
    print(f"SalaryRange (iterable, reusable): {list(levels)} {list(levels)}")
    iterator = iter(levels)
    print(f"iter(iterator) is iterator: {iter(iterator) is iterator}")
    print(f"next(): {next(iterator)}, {next(iterator)}")
    print(f"rest: {list(iterator)}, after exhaustion: {list(iterator)}")
    salaries = (e.salary for e in build_pipeline(SAMPLE))
    print(f"generator expression first time: {len(list(salaries))} values, "
          f"second time: {len(list(salaries))} values (one-shot)")
    print(f"flatten (recursive yield from): {list(flatten([1, [2, [3, [4]]], 5]))}")


def demo_batches() -> None:
    print("=== Batch processing ===")
    for number, batch in enumerate(batched(build_pipeline(SAMPLE), 5), start=1):
        print(f"batch {number}: {[e.employee_id for e in batch]}")
    batches = export_batches(build_pipeline(SAMPLE, min_salary=40000), EXPORT, 2)
    print(f"Exported employees with salary >= 40000 to {EXPORT} in {batches} batches")


SECTIONS = {
    "pipeline": demo_pipeline,
    "itertools": demo_itertools,
    "iterators": demo_iterators,
    "batches": demo_batches,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="stream-processor",
        description="Streaming processing of employee data (lab 3, variant 6).",
    )
    parser.add_argument("--section", choices=tuple(SECTIONS),
                        help="show only one part of the demo")
    parser.add_argument("--experiment", action="store_true",
                        help="eager vs lazy on 10 000, 100 000, 500 000 records")
    parser.add_argument("--early", action="store_true",
                        help="early termination on 1 000 000 records")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.experiment:
        print_experiment()
    elif args.early:
        print_early_termination()
    elif args.section:
        SECTIONS[args.section]()
    else:
        for show_section in SECTIONS.values():
            show_section()
            print()


if __name__ == "__main__":
    main()
