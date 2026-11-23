"""Application entry point: console interface."""

import argparse

from employee_manager.config import CURRENCY
from employee_manager.exceptions import InvalidEmployeeDataError
from employee_manager.models import Employee
from employee_manager.services import (
    add_employee,
    calculate_average_salary,
    calculate_payroll,
    filter_by_department,
    find_highest_paid,
    payroll_by_department,
    salary_statistics,
    search_employees,
    sort_by_salary,
)


def create_demo_employees() -> list[Employee]:
    """Create a list of demo employees."""
    return [
        Employee("Anna Koval", "Python Developer", "IT", 52000),
        Employee("Oleh Melnyk", "Accountant", "Finance", 31000),
        Employee("Iryna Bondar", "Team Lead", "IT", 68000),
        Employee("Andrii Shevchenko", "HR Manager", "HR", 29000),
        Employee("Maria Tkachenko", "Financial Analyst", "Finance", 41000),
        Employee("Taras Lysenko", "QA Engineer", "IT", 38000),
    ]


def print_employees(employees: list[Employee]) -> None:
    """Print employees as a table."""
    if not employees:
        print("No employees found.")
        return
    print(f"\n{'Name':22}{'Position':20}{'Department':12}{'Salary':>12}")
    print("-" * 66)
    for employee in employees:
        print(
            f"{employee.name:22}"
            f"{employee.position:20}"
            f"{employee.department:12}"
            f"{employee.salary:12.2f}"
        )


def read_float(prompt: str) -> float:
    """Read a number from the keyboard, repeating until it is valid."""
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            print("Please enter a number.")


def input_employee() -> Employee | None:
    """Read a new employee from the keyboard."""
    try:
        return Employee(
            name=input("Name: "),
            position=input("Position: "),
            department=input("Department: "),
            salary=read_float(f"Salary ({CURRENCY}): "),
        )
    except InvalidEmployeeDataError as error:
        print(f"Error: {error}")
        return None


def print_report(employees: list[Employee]) -> None:
    """Print the main statistics required by the variant."""
    average = calculate_average_salary(employees)
    print(f"\nAverage salary: {average:.2f} {CURRENCY}")

    best = find_highest_paid(employees)
    if best is not None:
        print(
            f"Highest paid: {best.name}, {best.position} "
            f"({best.salary:.2f} {CURRENCY})"
        )

    payroll = calculate_payroll(employees)
    print(f"Total payroll fund: {payroll:.2f} {CURRENCY}")


def print_statistics(employees: list[Employee]) -> None:
    """Print extended statistics."""
    stats = salary_statistics(employees)
    print("\nSalary statistics:")
    for key, value in stats.items():
        print(f"  {key:8}: {value:12.2f} {CURRENCY}")
    print("\nPayroll by department:")
    for department, total in payroll_by_department(employees).items():
        print(f"  {department:10}: {total:12.2f} {CURRENCY}")


def print_menu() -> None:
    print()
    print("1. Show all employees")
    print("2. Find by department")
    print("3. Average salary / highest paid / payroll")
    print("4. Add employee")
    print("5. Sort by salary")
    print("6. Search by several criteria")
    print("7. Statistics")
    print("0. Exit")


def run_menu(employees: list[Employee]) -> None:
    """Run the interactive menu."""
    while True:
        print_menu()
        try:
            command = input("Select command: ").strip()
        except EOFError:
            print("\nGoodbye.")
            break

        if command == "1":
            print_employees(employees)
        elif command == "2":
            department = input("Department: ")
            group = filter_by_department(employees, department)
            print_employees(group)
            if group:
                print_report(group)
        elif command == "3":
            print_report(employees)
        elif command == "4":
            employee = input_employee()
            if employee is not None:
                add_employee(employees, employee)
                print(f"Employee {employee.name} added.")
        elif command == "5":
            print_employees(sort_by_salary(employees))
        elif command == "6":
            department = input("Department (empty = any): ")
            position = input("Position contains (empty = any): ")
            raw_min = input("Minimal salary (empty = any): ").strip()
            try:
                min_salary = float(raw_min) if raw_min else None
            except ValueError:
                print("Invalid number, salary filter ignored.")
                min_salary = None
            print_employees(
                search_employees(employees, department, position, min_salary)
            )
        elif command == "7":
            print_statistics(employees)
        elif command == "0":
            print("Goodbye.")
            break
        else:
            print("Unknown command.")


def run_demo(employees: list[Employee]) -> None:
    """Show all features of the variant without keyboard input."""
    print("\nAll employees:")
    print_employees(employees)

    department = "IT"
    print(f"\nEmployees of department {department}:")
    print_employees(filter_by_department(employees, department))

    print_report(employees)
    print_statistics(employees)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="employee-manager",
        description="Employee accounting (laboratory work 1, variant 6).",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="run a demo without keyboard input",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Start the application."""
    args = parse_args(argv)
    print("Employee Manager (variant 6)")
    employees = create_demo_employees()
    if args.demo:
        run_demo(employees)
    else:
        run_menu(employees)


if __name__ == "__main__":
    main()
