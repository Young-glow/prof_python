"""Business logic for working with employees."""

from statistics import median

from employee_manager.models import Employee


def add_employee(
    employees: list[Employee],
    employee: Employee,
) -> None:
    """Add an employee to the list."""
    employees.append(employee)


def filter_by_department(
    employees: list[Employee],
    department: str,
) -> list[Employee]:
    """Return employees of the given department (case-insensitive)."""
    department = department.strip().lower()
    return [
        employee
        for employee in employees
        if employee.department.lower() == department
    ]


def search_employees(
    employees: list[Employee],
    department: str | None = None,
    position: str | None = None,
    min_salary: float | None = None,
) -> list[Employee]:
    """Search employees by several optional criteria."""
    result = employees
    if department:
        result = filter_by_department(result, department)
    if position:
        position = position.strip().lower()
        result = [e for e in result if position in e.position.lower()]
    if min_salary is not None:
        result = [e for e in result if e.salary >= min_salary]
    return result


def calculate_average_salary(
    employees: list[Employee],
) -> float:
    """Return the average salary, or 0.0 for an empty list."""
    if not employees:
        return 0.0
    return calculate_payroll(employees) / len(employees)


def find_highest_paid(
    employees: list[Employee],
) -> Employee | None:
    """Return the employee with the maximum salary."""
    if not employees:
        return None
    return max(employees, key=lambda employee: employee.salary)


def calculate_payroll(
    employees: list[Employee],
) -> float:
    """Return the total payroll fund (sum of all salaries)."""
    return sum(employee.salary for employee in employees)


def sort_by_salary(
    employees: list[Employee],
    descending: bool = True,
) -> list[Employee]:
    """Return a new list sorted by salary."""
    return sorted(
        employees,
        key=lambda employee: employee.salary,
        reverse=descending,
    )


def salary_statistics(
    employees: list[Employee],
) -> dict[str, float]:
    """Return min, max, average and median salary."""
    if not employees:
        return {"min": 0.0, "max": 0.0, "average": 0.0, "median": 0.0}
    salaries = [employee.salary for employee in employees]
    return {
        "min": min(salaries),
        "max": max(salaries),
        "average": calculate_average_salary(employees),
        "median": median(salaries),
    }


def payroll_by_department(
    employees: list[Employee],
) -> dict[str, float]:
    """Return the payroll fund for each department."""
    result: dict[str, float] = {}
    for employee in employees:
        result[employee.department] = (
            result.get(employee.department, 0.0) + employee.salary
        )
    return result
