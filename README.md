# Employee Manager

Laboratory works for the course "Professional Python".
Variant 6 — "Employee accounting".

| Lab | Topic | Package |
| --- | --- | --- |
| 1 | Professional Python project and Git | `employee_manager` |
| 2 | Data structures and functional decomposition | `data_processor` |
| 3 | Iterators, generators and streaming processing | `stream_processor` |
| 4 | Professional OOP and the Python type system | `employee_domain` |

## Description

Console application for keeping records of employees
(name, position, department, salary) and calculating
salary statistics.

Features:

- list of employees;
- search by department;
- average salary;
- employee with the maximum salary;
- total payroll fund;
- adding an employee from the keyboard with validation;
- sorting by salary;
- search by several criteria;
- statistics (min / max / average / median, payroll by department).

## Requirements

Python 3.11+

## Installation

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

python -m pip install -e ".[dev]"
```

## Run

Interactive menu:

```bash
python -m employee_manager.main
```

or

```bash
employee-manager
```

Demo mode (no input required):

```bash
python -m employee_manager.main --demo
```

## Example

```
Employee Manager (variant 6)

1. Show all employees
...
Select command: 3

Average salary: 43166.67 UAH
Highest paid: Iryna Bondar, Team Lead (68000.00 UAH)
Total payroll fund: 259000.00 UAH
```

## Laboratory work 2: data processor

Module for processing structured employee data: unique departments,
grouping, average salary (total and by department), highest paid employee,
payroll fund, filtering by salary, `Counter` by department, search,
sorting, nested grouping, pipeline processing and summary export.

It uses `list`, `tuple`, `set`, `dict`, `Counter`, `defaultdict`, `deque`,
list/set/dict comprehensions, generator expressions, `*args`, `**kwargs`,
`lambda`, closures and decorators (including a parametrized one).

```bash
python -m data_processor.main                       # full demo
python -m data_processor.main --section search      # one part only
python -m data_processor.main --benchmark           # list vs dict search
```

Sections: `structures`, `aggregation`, `search`, `functions`.

### Complexity of the main operations

| Operation | Structure | Complexity |
| --- | --- | --- |
| search by id | list (`find_linear`) | O(n) |
| building an index | dict comprehension | O(n) |
| search by id | dict (`index.get`) | O(1) average |
| membership test | set | O(1) average |
| grouping | defaultdict | O(n) |
| sorting | `sorted` | O(n log n) |

## Laboratory work 3: stream processor

Lazy streaming pipeline for a CSV file of employees
(`employee_id,name,position,department,salary`):

```
CSV file -> read_lines() -> clean_lines() -> parse_csv_rows()
         -> validate_employees() -> normalize_names()
         -> filter_by_department() -> filter_by_salary()
         -> calculate_statistics() / batched() -> export_batches()
```

Every stage is a generator, so records are processed one by one and the
whole file is never loaded into memory. Implemented: streaming validation
(with counting of invalid records), filtering by department and salary,
streaming average salary, highest paid employee, payroll fund, `Counter`
by department, batch export, custom iterator class, recursive generator
with `yield from`, `itertools` (`islice`, `chain`, `count`, `accumulate`,
`pairwise`, `groupby`, `takewhile`), eager vs lazy experiment and early
termination.

```bash
python -m stream_processor.main                      # full demo on data/employees.csv
python -m stream_processor.main --section itertools  # pipeline, itertools, iterators, batches
python -m stream_processor.main --experiment         # eager vs lazy (10k, 100k, 500k records)
python -m stream_processor.main --early              # early termination on 1 000 000 records
```

Large test files are generated automatically into `data/generated/`
(ignored by Git).

## Laboratory work 4: typed OOP model

Object model of employee accounting with a service layer.

| Element | Where |
| --- | --- |
| Domain classes | `Employee` (ABC), `Manager`, `Developer`, `Department`, `PayrollRecord` |
| Value objects (frozen dataclass) | `Money`, `Email` |
| Inheritance | `Manager(Employee)`, `Developer(Employee)`, bonus policies |
| Composition | `Department` has employees, services have repositories and notifier |
| Properties | `Employee.id`, `name`, `salary`, `department`; `Department.payroll` |
| Dunder methods | `__repr__`, `__str__`, `__eq__`, `__hash__`, `__lt__`, `__add__`, `__mul__`, `__len__`, `__iter__`, `__contains__`, `__getitem__`, `__bool__` |
| ABC | `Employee`, `BonusPolicy` |
| Protocol | `HasId`, `Repository[T]`, `Notifier`, `ReportExporter` (runtime_checkable) |
| Generics | `InMemoryRepository[T]` (bound TypeVar), `MetricService[T]`, `Result[T]`, constrained `Number` |
| TypedDict | `EmployeePayload` (with `NotRequired`), `DepartmentReport` |
| Services | `EmployeeService`, `PayrollService`, `ReportService` |
| DI | manual container `Container` in `container.py` |

```
             Employee (ABC)                      BonusPolicy (ABC)
               ▲        ▲                    ▲        ▲          ▲
           Manager   Developer           NoBonus  RoleBonus  PercentageBonus ...
               │        │
               └──► Department ◄── has many Employee      Money, Email (frozen)
                                                                   ▲
EmployeeService ── Repository[Employee], Repository[Department], Notifier
PayrollService  ── BonusPolicy, Notifier ──► PayrollRecord
ReportService   ── Repository[Department] ──► DepartmentReport ──► ReportExporter
```

```bash
python -m employee_domain.main                    # full demo
python -m employee_domain.main --section payroll  # model, services, payroll, reports, design
python -m mypy src                                # Success: no issues found
python -m mypy examples/type_errors.py            # type-checking experiment (4 errors)
python -m mypy examples/type_errors_fixed.py      # after the corrections
```

## Tests and checks

```bash
python -m pytest          # 42 tests
python -m mypy src tests  # strict type checking
python -m ruff check src tests
```

## Project structure

- `src/employee_manager/models.py` — data model `Employee` (dataclass with validation).
- `src/employee_manager/services.py` — business logic.
- `src/employee_manager/config.py` — configuration constants.
- `src/employee_manager/exceptions.py` — custom exceptions.
- `src/employee_manager/main.py` — application entry point, console menu.
- `tests/test_services.py` — tests.
- `src/data_processor/data.py` — input data (lab 2).
- `src/data_processor/decorators.py` — decorators `measure_time`, `log_operation`.
- `src/data_processor/processors.py` — search, filtering, grouping, closures.
- `src/data_processor/analytics.py` — aggregation, sorting, summary, pipeline.
- `src/data_processor/benchmark.py` — list vs dict search benchmark.
- `src/data_processor/main.py` — lab 2 entry point.
- `tests/test_data_processor.py` — lab 2 tests.
- `data/employees.csv` — sample input for lab 3 (with invalid records).
- `src/stream_processor/` — lab 3: `readers.py`, `parsers.py`, `filters.py`,
  `transformations.py`, `batches.py`, `analytics.py`, `export.py`,
  `iterators.py`, `pipeline.py`, `generate.py`, `experiment.py`, `main.py`.
- `tests/test_stream_processor.py` — lab 3 tests.
- `src/employee_domain/` — lab 4: `value_objects.py`, `exceptions.py`, `models.py`,
  `protocols.py`, `policies.py`, `repositories.py`, `generics.py`, `dto.py`,
  `adapters.py`, `services.py`, `container.py`, `experiments.py`, `seed.py`, `main.py`.
- `examples/` — lab 4 type-checking experiment.
- `tests/test_employee_domain.py` — lab 4 tests.
- `reports/` — laboratory work reports.

## Author

Student: Anastasiia Zhmurko
Group: FeP-32
