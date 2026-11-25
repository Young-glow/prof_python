# Employee Manager

Laboratory works for the course "Professional Python".
Variant 6 — "Employee accounting".

| Lab | Topic | Package |
| --- | --- | --- |
| 1 | Professional Python project and Git | `employee_manager` |
| 2 | Data structures and functional decomposition | `data_processor` |

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

## Tests and checks

```bash
python -m pytest          # 18 tests
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
- `reports/` — laboratory work reports.

## Author

Student: Anastasiia Zhmurko
Group: FeP-32
