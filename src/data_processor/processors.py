"""Basic processing: unique values, indexes, search, filtering, grouping."""

from collections import Counter, defaultdict
from collections.abc import Callable, Iterable

from data_processor.data import Employee
from data_processor.decorators import log_operation

Predicate = Callable[[Employee], bool]


@log_operation("set comprehension")
def get_unique_departments(employees: Iterable[Employee]) -> set[str]:
    """Return the set of departments.  O(n)."""
    return {str(employee["department"]) for employee in employees}


@log_operation("dict comprehension")
def create_employee_index(employees: Iterable[Employee]) -> dict[int, Employee]:
    """Build an index id -> employee.  Building O(n), lookup O(1) on average."""
    return {int(employee["id"]): employee for employee in employees}


def find_linear(employees: Iterable[Employee], employee_id: int) -> Employee | None:
    """Search an employee by id in a list.  O(n)."""
    for employee in employees:
        if employee["id"] == employee_id:
            return employee
    return None


def find_by_name(employees: Iterable[Employee], text: str) -> list[Employee]:
    """Case-insensitive search by part of the name.  O(n)."""
    text = text.strip().lower()
    return [e for e in employees if text in str(e["name"]).lower()]


def filter_items(employees: Iterable[Employee], predicate: Predicate) -> list[Employee]:
    """Universal filter: keep employees for which predicate(employee) is True."""
    return [employee for employee in employees if predicate(employee)]


def create_salary_filter(
    minimum: float = 0.0,
    maximum: float = float("inf"),
) -> Predicate:
    """Closure: return a predicate that remembers `minimum` and `maximum`."""

    def predicate(employee: Employee) -> bool:
        return minimum <= float(employee["salary"]) <= maximum

    return predicate


def create_department_filter(*departments: str) -> Predicate:
    """Closure with *args: predicate 'department is one of the given'."""
    allowed = set(departments)  # set: membership test O(1) on average

    def predicate(employee: Employee) -> bool:
        return employee["department"] in allowed

    return predicate


@log_operation("defaultdict grouping")
def group_by(employees: Iterable[Employee], field: str) -> dict[str, list[Employee]]:
    """Group employees by any field using defaultdict(list).  O(n)."""
    result: defaultdict[str, list[Employee]] = defaultdict(list)
    for employee in employees:
        result[str(employee[field])].append(employee)
    return dict(result)


def group_nested(
    employees: Iterable[Employee],
    outer: str,
    inner: str,
) -> dict[str, dict[str, list[Employee]]]:
    """Nested grouping, e.g. department -> position -> employees."""
    return {
        key: group_by(members, inner)
        for key, members in group_by(employees, outer).items()
    }


@log_operation("Counter")
def count_by_department(employees: Iterable[Employee]) -> Counter[str]:
    """Counter of employees in each department.  O(n)."""
    return Counter(str(employee["department"]) for employee in employees)
