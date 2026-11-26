"""Unit tests: payroll strategies, PayrollService and ReportService."""

from unittest.mock import Mock

import pytest

from employee_domain.container import Container
from employee_domain.exceptions import DomainError
from employee_domain.models import Employee
from employee_domain.policies import (
    ManagerOnlyBonus,
    NoBonus,
    PercentageBonus,
    RoleBonus,
)
from employee_domain.protocols import BonusPolicy, Notifier, ReportExporter
from employee_domain.services import PayrollService, ReportService
from employee_domain.value_objects import Money


@pytest.mark.parametrize(
    ("policy", "expected_total"),
    [
        pytest.param(NoBonus(), 266_000, id="no-bonus"),
        pytest.param(RoleBonus(), 291_840, id="role-bonus"),
        pytest.param(PercentageBonus(10), 292_600, id="10-percent"),
        pytest.param(ManagerOnlyBonus(Money(5_000)), 276_000, id="managers-only"),
    ],
)
def test_payroll_total_for_each_strategy(
    staff: list[Employee], policy: BonusPolicy, expected_total: float
) -> None:
    service = PayrollService(policy, Mock(spec=Notifier))
    records = service.build(staff, "2026-11")
    assert len(records) == 5
    assert service.total(records).amount == pytest.approx(expected_total)
    assert records[0].name == "Iryna Bondar"  # sorted by total, descending


@pytest.mark.parametrize("percent", [-0.01, 100.01])
def test_invalid_percentage_bonus(percent: float) -> None:
    with pytest.raises(DomainError, match="Invalid percent"):
        PercentageBonus(percent)


def test_payroll_notification_message(staff: list[Employee]) -> None:
    notifier = Mock(spec=Notifier)
    service = PayrollService(RoleBonus(), notifier)
    service.notify(service.build(staff, "2026-11"), "accounting@company.ua")
    notifier.send.assert_called_once_with(
        "accounting@company.ua",
        "Payroll 2026-11 ready: 5 records, total 291 840.00 UAH",
    )


def test_empty_payroll_cannot_be_announced() -> None:
    """Defect found by this test: an empty list used to raise IndexError."""
    notifier = Mock(spec=Notifier)
    service = PayrollService(RoleBonus(), notifier)
    with pytest.raises(DomainError, match="no records"):
        service.notify([], "accounting@company.ua")
    notifier.send.assert_not_called()


def test_report_service_uses_exporter_return_value(container: Container) -> None:
    exporter = Mock(spec=ReportExporter)
    exporter.export.return_value = "REPORT"
    result = ReportService(container.departments).export(exporter)

    assert result == "REPORT"
    exporter.export.assert_called_once()
    (reports,), _ = exporter.export.call_args
    assert [r["department"] for r in reports] == ["IT", "Finance"]  # HR is empty
    it_report = reports[0]
    assert it_report["employees"] == 4
    assert it_report["payroll"] == pytest.approx(239_200)
    assert it_report["max_pay"] == pytest.approx(78_200)
