"""Application / service layer: use cases built from injected abstractions."""

from collections.abc import Callable, Iterable
from typing import Generic

from employee_domain.dto import DepartmentReport
from employee_domain.exceptions import DomainError, EmployeeNotFoundError
from employee_domain.generics import Result, T
from employee_domain.models import Department, Employee, PayrollRecord
from employee_domain.protocols import BonusPolicy, Notifier, ReportExporter, Repository
from employee_domain.value_objects import Money


class MetricService(Generic[T]):
    """Generic service: statistics over any items by a numeric key."""

    def __init__(self, key: Callable[[T], float]) -> None:
        self._key = key

    def total(self, items: Iterable[T]) -> float:
        return round(sum(self._key(item) for item in items), 2)

    def average(self, items: Iterable[T]) -> float:
        values = [self._key(item) for item in items]
        return round(sum(values) / len(values), 2) if values else 0.0

    def maximum(self, items: Iterable[T]) -> T | None:
        return max(items, key=self._key, default=None)


def _pay(employee: Employee) -> float:
    return employee.monthly_pay().amount


class EmployeeService:
    """Hiring, department assignment, search and salary statistics."""

    def __init__(
        self,
        employees: Repository[Employee],
        departments: Repository[Department],
        notifier: Notifier,
    ) -> None:
        self._employees = employees
        self._departments = departments
        self._notifier = notifier
        self._metrics: MetricService[Employee] = MetricService(_pay)

    def hire(self, employee: Employee, department_id: int) -> Result[Employee]:
        if self._employees.get(employee.id) is not None:
            return Result(error=f"Employee with id={employee.id} already exists")
        self._employees.add(employee)
        try:
            self.assign_department(employee.id, department_id)
        except DomainError as error:
            self._employees.remove(employee.id)  # roll back the new employee only
            return Result(error=str(error))
        self._notifier.send(
            str(employee.email), f"Welcome, {employee.name}! Role: {employee.role}"
        )
        return Result(value=employee)

    def assign_department(self, employee_id: int, department_id: int) -> None:
        employee = self._employees.get(employee_id)
        if employee is None:
            raise EmployeeNotFoundError(employee_id)
        target = self._departments.get(department_id)
        if target is None:
            raise DomainError(f"Department with id={department_id} not found")
        for department in self._departments:
            if employee in department and department is not target:
                department.remove(employee_id)
                self._notifier.send(
                    str(employee.email),
                    f"You moved from {department.name} to {target.name}",
                )
        target.add(employee)

    def find_by_department(self, name: str) -> list[Employee]:
        return self._employees.find(lambda e: e.department == name)

    def get(self, employee_id: int) -> Employee:
        employee = self._employees.get(employee_id)
        if employee is None:
            raise EmployeeNotFoundError(employee_id)
        return employee

    def average_pay(self) -> Money:
        return Money(self._metrics.average(self._employees))

    def highest_paid(self) -> Employee | None:
        return self._metrics.maximum(self._employees)

    def total_payroll(self) -> Money:
        return Money(self._metrics.total(self._employees))


class PayrollService:
    """Builds the payroll sheet; the bonus rule is an injected strategy."""

    def __init__(self, policy: BonusPolicy, notifier: Notifier) -> None:
        self._policy = policy
        self._notifier = notifier

    def build(self, employees: Iterable[Employee], period: str) -> list[PayrollRecord]:
        records = [
            PayrollRecord(
                employee_id=e.id,
                name=e.name,
                role=e.role,
                department=e.department or "-",
                period=period,
                base=e.salary,
                bonus=self._policy.bonus_for(e),
            )
            for e in employees
        ]
        records.sort(key=lambda r: r.total, reverse=True)
        return records

    @staticmethod
    def total(records: Iterable[PayrollRecord]) -> Money:
        result = Money.zero()
        for record in records:
            result = result + record.total
        return result

    def notify(self, records: Iterable[PayrollRecord], accounting: str) -> None:
        records = list(records)
        if not records:
            raise DomainError("Payroll has no records, nothing to announce")
        self._notifier.send(
            accounting,
            f"Payroll {records[0].period} ready: {len(records)} records, "
            f"total {self.total(records)}",
        )


class ReportService:
    """Builds department reports and exports them via ReportExporter."""

    def __init__(self, departments: Repository[Department]) -> None:
        self._departments = departments
        self._metrics: MetricService[Employee] = MetricService(_pay)

    def department_report(self, department: Department) -> DepartmentReport:
        best = self._metrics.maximum(department)
        return {
            "department": department.name,
            "head": department.head.name if department.head else "-",
            "employees": len(department),
            "average_pay": self._metrics.average(department),
            "max_pay": _pay(best) if best else 0.0,
            "payroll": department.payroll.amount,
        }

    def build(self) -> list[DepartmentReport]:
        return [self.department_report(d) for d in self._departments if len(d)]

    def export(self, exporter: ReportExporter) -> str:
        return exporter.export(self.build())
