"""Type-checking experiment: three deliberate errors (run: mypy examples/type_errors.py)."""

from employee_domain.models import Department, Developer, Employee
from employee_domain.repositories import InMemoryRepository
from employee_domain.value_objects import Email, Money

# Error 1: a str is assigned to a variable annotated as int
employee_id: int = "1"


# Error 2: the function promises int but returns str
def total() -> int:
    return "100"


# Error 3: a Department is added to a repository of employees
repository: InMemoryRepository[Employee] = InMemoryRepository()
repository.add(Department(1, "IT"))

# Bonus: an id of a wrong type is passed to the constructor
developer = Developer("one", "Anna Koval", Email("anna@company.ua"), Money(52000))
