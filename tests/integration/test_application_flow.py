"""Integration: the lab 4 demo application runs end to end (stdout checked)."""

import sys

import pytest

from employee_domain import main as domain_main

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("section", "expected"),
    [
        ("model", "max by pay (__lt__): Iryna Bondar"),
        ("services", "Total payroll : 419 160.00 UAH"),
        ("payroll", "RoleBonus                total = 419 160.00 UAH"),
        ("reports", "isinstance(ReportExporter) = True"),
        ("design", "composition swaps one component"),
    ],
)
def test_demo_sections(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    section: str,
    expected: str,
) -> None:
    monkeypatch.setattr(sys, "argv", ["employee-domain", "--section", section])
    domain_main.main()
    out = capsys.readouterr().out
    assert "Laboratory work 4 - variant 6" in out
    assert expected in out


def test_full_demo_runs_all_sections(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["employee-domain"])
    domain_main.main()
    out = capsys.readouterr().out
    for title in ("Domain model", "Employee service", "Payroll", "Department reports",
                  "Experiment 2"):
        assert f"=== {title}" in out
    assert "[notify -> olena.kravets@company.ua]" in out  # ConsoleNotifier used


def test_unknown_section_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["employee-domain", "--section", "unknown"])
    with pytest.raises(SystemExit) as exc_info:
        domain_main.main()
    assert exc_info.value.code == 2
