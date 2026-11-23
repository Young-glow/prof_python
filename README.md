# Employee Manager

Laboratory work No. 1 for the course "Professional Python".
Variant 6 — "Employee accounting".

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

## Tests and checks

```bash
python -m pytest          # 6 tests
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
- `reports/` — laboratory work reports.

## Author

Student: Anastasiia Zhmurko
Group: FeP-32
