"""Manual dependency-injection container: the only place with concrete classes."""

from dataclasses import dataclass, field

from employee_domain.adapters import ConsoleNotifier
from employee_domain.models import Department, Employee
from employee_domain.policies import RoleBonus
from employee_domain.protocols import BonusPolicy, Notifier
from employee_domain.repositories import InMemoryRepository
from employee_domain.services import EmployeeService, PayrollService, ReportService


@dataclass
class Container:
    notifier: Notifier = field(default_factory=ConsoleNotifier)
    bonus_policy: BonusPolicy = field(default_factory=RoleBonus)
    employees: InMemoryRepository[Employee] = field(
        default_factory=InMemoryRepository
    )
    departments: InMemoryRepository[Department] = field(
        default_factory=InMemoryRepository
    )

    def employee_service(self) -> EmployeeService:
        return EmployeeService(self.employees, self.departments, self.notifier)

    def payroll_service(self) -> PayrollService:
        return PayrollService(self.bonus_policy, self.notifier)

    def report_service(self) -> ReportService:
        return ReportService(self.departments)
