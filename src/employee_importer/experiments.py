"""Experiments of laboratory work 5."""

from __future__ import annotations

import csv
import hashlib
import logging
import random
import sys
import tempfile
import traceback
import tracemalloc
from collections.abc import Callable, Iterator
from pathlib import Path
from time import perf_counter
from typing import Any

from employee_importer.config import load_config
from employee_importer.exceptions import (
    ApplicationError,
    DataExportError,
    RecordValidationError,
)
from employee_importer.exporters import JsonExporter
from employee_importer.models import FIELDS, Employee, ImportStatistics
from employee_importer.readers import CsvImporter
from employee_importer.services import filter_by_min_salary, import_employees
from employee_importer.validators import StrictPolicy, TolerantPolicy, ValidationPolicy

GENERATED = Path("data/generated/lab5")
DEPARTMENTS = ("IT", "Finance", "HR", "Sales")
ALLOWED = frozenset(DEPARTMENTS)
FIRST = ("Anna", "Oleh", "Iryna", "Maria", "Dmytro", "Taras", "Olena", "Yurii")
LAST = ("Koval", "Melnyk", "Bondar", "Moroz", "Savchenko", "Lysenko", "Kravets")
POSITIONS = ("Developer", "Accountant", "Recruiter", "Analyst", "Manager")
BAD_ROWS = (
    ["abc", "Bad Id", "Developer", "IT", "40000"],
    ["0", "Zero Id", "Developer", "IT", "40000"],
    ["5", "", "Developer", "IT", "40000"],
    ["6", "No Position", "", "HR", "40000"],
    ["7", "Wrong Dept", "Manager", "Marketing", "40000"],
    ["8", "Negative Pay", "Analyst", "Finance", "-1"],
    ["9", "Text Pay", "Analyst", "Finance", "n/a"],
    ["10", "Robot 3000", "Developer", "IT", "40000"],
    ["11", "Missing Pay", "Developer", "IT", ""],
    ["12", "Empty Dept", "Developer", "", "40000"],
)


def title(text: str) -> None:
    print(f"\n=== {text} ===")


def generate_csv(
    path: Path, valid: int, invalid_rows: int = 0, seed: int = 2026
) -> Path:
    """Write ``valid`` correct rows and spread ``invalid_rows`` bad rows evenly."""
    rng = random.Random(seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    step = valid // invalid_rows if invalid_rows else 0
    bad = 0
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS)
        for number in range(1, valid + 1):
            writer.writerow([
                number,
                f"{rng.choice(FIRST)} {rng.choice(LAST)}",
                rng.choice(POSITIONS),
                rng.choice(DEPARTMENTS),
                rng.randrange(20_000, 90_000, 500),
            ])
            if step and number % step == step // 2 and bad < invalid_rows:
                writer.writerow(BAD_ROWS[bad % len(BAD_ROWS)])
                bad += 1
    return path


# --- Experiment 1. Strict vs tolerant --------------------------------------
def _run_policy(path: Path, policy: ValidationPolicy, output: Path) -> dict[str, Any]:
    stats = ImportStatistics()
    outcome = "completed (exit code 0)"
    try:
        employees = import_employees(
            CsvImporter(), path, allowed_departments=ALLOWED,
            policy=policy, statistics=stats,
        )
        stats.exported = JsonExporter().export(
            filter_by_min_salary(employees, 0, stats), output
        )
    except RecordValidationError as error:
        outcome = f"stopped at {error} (exit code 1)"
    return {"stats": stats, "outcome": outcome, "file": output.exists()}


def experiment_strict_vs_tolerant() -> None:
    title("Experiment 1: strict vs tolerant (1000 valid + 10 invalid records)")
    path = generate_csv(GENERATED / "strict_tolerant.csv", 1000, 10)
    logging.getLogger("employee_importer").setLevel(logging.ERROR)
    with tempfile.TemporaryDirectory() as tmp:
        results = {
            "Strict": _run_policy(path, StrictPolicy(), Path(tmp) / "strict.json"),
            "Tolerant": _run_policy(path, TolerantPolicy(), Path(tmp) / "tol.json"),
        }
    logging.getLogger("employee_importer").setLevel(logging.NOTSET)
    print(f"{'Parameter':<22}{'Strict':>14}{'Tolerant':>14}")
    for label, attr in (("Processed records", "total"), ("Valid", "valid"),
                        ("Invalid", "invalid"), ("Exported", "exported")):
        values = [getattr(r["stats"], attr) for r in results.values()]
        print(f"{label:<22}{values[0]:>14}{values[1]:>14}")
    created = ["yes" if r["file"] else "no" for r in results.values()]
    print(f"{'Output file created':<22}{created[0]:>14}{created[1]:>14}")
    for name, result in results.items():
        print(f"{name} finish: {result['outcome']}")


# --- Experiment 2. Streaming vs eager -------------------------------------
def eager_import(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def streaming_import(path: Path) -> Iterator[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        yield from csv.DictReader(file)


def count_eager(path: Path) -> int:
    return len(eager_import(path))


def count_streaming(path: Path) -> int:
    return sum(1 for _ in streaming_import(path))


def _measure(action: Callable[[Path], int], path: Path) -> tuple[float, float, int]:
    tracemalloc.start()
    start = perf_counter()
    count = action(path)
    elapsed = perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return elapsed, peak / 1024 / 1024, count


def experiment_memory(sizes: tuple[int, ...] = (10_000, 100_000, 500_000)) -> None:
    title("Experiment 2: streaming vs eager import (tracemalloc)")
    print(f"{'Records':>9} {'Eager s':>9} {'Stream s':>9} "
          f"{'Eager peak MB':>14} {'Stream peak MB':>15} {'RAM ratio':>10}")
    for size in sizes:
        path = GENERATED / f"employees_{size}.csv"
        if not path.exists():
            generate_csv(path, size)
        eager = _measure(count_eager, path)
        stream = _measure(count_streaming, path)
        assert eager[2] == stream[2] == size
        print(f"{size:>9,} {eager[0]:>9.3f} {stream[0]:>9.3f} "
              f"{eager[1]:>14.2f} {stream[1]:>15.3f} {eager[1] / stream[1]:>9.0f}x")
    print("The generator was fully consumed (sum over all rows) in each case.")


# --- Experiment 3. Exception chaining -------------------------------------
def experiment_chaining() -> None:
    title("Experiment 3: exception chaining")
    path = GENERATED / "chaining.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "employee_id,name,position,department,salary\n"
        "1,Anna Koval,Python Developer,IT,wrong\n",
        encoding="utf-8",
    )
    logging.getLogger("employee_importer").setLevel(logging.CRITICAL)
    try:
        list(import_employees(CsvImporter(), path, allowed_departments=ALLOWED,
                              policy=StrictPolicy(), statistics=ImportStatistics()))
    except RecordValidationError as error:
        traceback.print_exception(error, file=sys.stdout, limit=1)
        print("Chain:", " -> ".join(
            type(e).__name__ for e in (error.__cause__, error) if e is not None))
        print("error.field =", error.field, "| error.line_number =", error.line_number)
    finally:
        logging.getLogger("employee_importer").setLevel(logging.NOTSET)


# --- Experiment 4. Atomic output ------------------------------------------
def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def experiment_atomic() -> None:
    title("Experiment 4: atomic output")
    target = GENERATED / "atomic_employees.json"
    good = [Employee(1, "Anna Koval", "Python Developer", "IT", 52000.0),
            Employee(3, "Iryna Bondar", "Team Lead", "IT", 68000.0)]
    JsonExporter().export(good, target)
    before = _digest(target)
    print(f"1) valid output written: {target.name}, sha256={before}")

    def crashing() -> Iterator[Employee]:
        yield good[0]
        yield good[1]
        raise OSError(28, "No space left on device (simulated)")

    try:
        JsonExporter().export(crashing(), target)
    except DataExportError as error:
        print(f"2) export failed: {type(error).__name__}: {error}")
        print(f"   caused by: {type(error.__cause__).__name__}: {error.__cause__}")
    tmp_exists = target.with_suffix(".json.tmp").exists()
    print(f"3) previous output intact: {_digest(target) == before} "
          f"(sha256={_digest(target)})")
    print(f"4) temporary file removed: {not tmp_exists}")
    print("5) application continues -> controlled shutdown, no partial JSON")


# --- Experiment 5. Configuration errors -----------------------------------
GOOD_CONFIG = """version: 1
input: {path: staff.csv}
output: {path: OUTDIR/employees.json, format: json}
processing:
  minimum_salary: MIN
  skip_invalid: true
  allowed_departments: [IT, Finance, HR, Sales]
logging: {level: INFO, path: logs/importer.log}
"""


def experiment_config() -> None:
    title("Experiment 5: configuration errors")
    source = Path("data/staff.csv")
    cases: list[tuple[str, str | None, bool]] = [
        ("1. config.yaml is missing", None, True),
        ("2. invalid YAML syntax", "version: 1\ninput: [path: data", True),
        ("3. no 'input' key", GOOD_CONFIG.split("input:")[0]
         + "output:" + GOOD_CONFIG.split("output:")[1], True),
        ("4. minimum_salary = -100", GOOD_CONFIG.replace("MIN", "-100"), True),
        ("5. input file is missing", GOOD_CONFIG.replace("MIN", "0"), False),
        ("6. output dir does not exist", GOOD_CONFIG.replace("MIN", "0"), True),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for name, text, copy_input in cases:
            folder = Path(tmp) / name[:1]
            folder.mkdir()
            if copy_input:
                (folder / "staff.csv").write_bytes(source.read_bytes())
            config = folder / "config.yaml"
            if text is not None:
                config.write_text(text.replace("OUTDIR", "new/dir"), encoding="utf-8")
            try:
                loaded = load_config(config, env={})
            except ApplicationError as error:
                cause = type(error.__cause__).__name__ if error.__cause__ else "-"
                message = str(error).replace(str(folder.resolve()), "<tmp>")
                message = message.replace(str(folder), "<tmp>")
                print(f"{name:<31} -> {type(error).__name__}: {message} "
                      f"[cause: {cause}]")
            else:
                exists = loaded.output.path.parent.exists()
                print(f"{name:<31} -> OK: config valid, output dir exists={exists}")
                JsonExporter().export([], loaded.output.path)
                print(f"{'':<31}    AtomicWriter created it, after export: "
                      f"exists={loaded.output.path.parent.exists()}")


EXPERIMENTS: dict[str, Callable[[], None]] = {
    "strict": experiment_strict_vs_tolerant,
    "memory": experiment_memory,
    "chaining": experiment_chaining,
    "atomic": experiment_atomic,
    "config": experiment_config,
}


def run(name: str) -> None:
    for key, experiment in EXPERIMENTS.items():
        if name in (key, "all"):
            experiment()
