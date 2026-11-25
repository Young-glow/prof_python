"""The same code after the corrections suggested by mypy."""

from employee_domain.models import Department, Developer, Employee
from employee_domain.repositories import InMemoryRepository
from employee_domain.value_objects import Email, Money

# Fix 1: the value has the declared type
employee_id: int = 1


# Fix 2: the returned value matches the annotation
def total() -> int:
    return 100


# Fix 3: each repository stores its own type
repository: InMemoryRepository[Employee] = InMemoryRepository()
departments: InMemoryRepository[Department] = InMemoryRepository()
departments.add(Department(1, "IT"))

# Fix 4: the id is an int
developer = Developer(employee_id, "Anna Koval", Email("anna@company.ua"), Money(52000))
repository.add(developer)
