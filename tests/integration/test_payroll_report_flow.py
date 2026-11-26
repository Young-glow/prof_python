"""Integration: CSV employees -> domain model -> async payroll -> JSON report."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from employee_domain.adapters import JsonReportExporter, MemoryNotifier
from employee_domain.async_payroll import AsyncPayrollService, PayrollProvider
from employee_domain.models import Department, Developer, Employee
from employee_domain.repositories import InMemoryRepository
from employee_domain.services import ReportService
from employee_domain.value_objects import Email, Money
from employee_importer.models import ImportStatistics
from employee_importer.readers import CsvImporter
from employee_importer.services import filter_by_min_salary, import_employees
from employee_importer.validators import TolerantPolicy

pytestmark = pytest.mark.integration


def to_domain(record_id: int, name: str, salary: float) -> Employee:
    return Developer(record_id, name, Email(f"user{record_id}@company.ua"),
                     Money(salary))


@pytest.mark.asyncio
async def test_employee_payroll_report_flow(staff_csv: Path, tmp_path: Path) -> None:
    # 1. real import: CSV -> validation -> filter
    stats = ImportStatistics()
    imported = list(filter_by_min_salary(
        import_employees(CsvImporter(), staff_csv,
                         allowed_departments={"IT", "Finance", "HR", "Sales"},
                         policy=TolerantPolicy(), statistics=stats),
        30_000, stats,
    ))
    assert len(imported) == 3

    # 2. domain model: departments with real employees
    departments: InMemoryRepository[Department] = InMemoryRepository()
    for dep_id, name in enumerate(("IT", "Finance"), start=1):
        departments.add(Department(dep_id, name))
    by_name = {d.name: d for d in departments}
    staff = [to_domain(r.employee_id, r.name, r.salary) for r in imported]
    for record, employee in zip(imported, staff, strict=True):
        by_name[record.department].add(employee)

    # 3. async payroll: the external provider is the only mocked boundary
    provider = AsyncMock(spec=PayrollProvider)
    provider.fetch_bonus.side_effect = lambda employee_id, period: employee_id * 100
    notifier = MemoryNotifier()
    total = await AsyncPayrollService(provider, notifier).run(
        staff, "2026-11", "accounting@company.ua"
    )
    assert total.amount == pytest.approx(151_000 + 100 + 200 + 300)
    assert notifier.messages == [
        ("accounting@company.ua", "Payroll 2026-11: 3 records, total 151 600.00 UAH")
    ]

    # 4. real JSON report written to tmp_path
    report_file = tmp_path / "report.json"
    report_file.write_text(
        ReportService(departments).export(JsonReportExporter()), encoding="utf-8"
    )
    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert [(r["department"], r["employees"]) for r in report] == [
        ("IT", 2), ("Finance", 1)
    ]
    assert report[0]["payroll"] == pytest.approx(120_000)
    assert report[1]["max_pay"] == pytest.approx(31_000)


def test_report_exporter_mock_does_not_hide_real_data(
    staff: list[Employee],
) -> None:
    departments: InMemoryRepository[Department] = InMemoryRepository()
    department = Department(1, "IT")
    for employee in staff:
        department.add(employee)
    departments.add(department)
    exporter = Mock()
    exporter.export.side_effect = OSError("printer is offline")
    with pytest.raises(OSError, match="offline"):
        ReportService(departments).export(exporter)
    (reports,), _ = exporter.export.call_args
    assert reports[0]["payroll"] == pytest.approx(291_840)
