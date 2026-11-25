"""Demo scenario of laboratory work 4 (variant 6, employee accounting)."""

from __future__ import annotations

import argparse

from employee_domain.adapters import (
    ConsoleNotifier,
    JsonReportExporter,
    MemoryNotifier,
    TableReportExporter,
)
from employee_domain.container import Container
from employee_domain.dto import employee_from_payload
from employee_domain.exceptions import DomainError
from employee_domain.experiments import run_composition_experiment, run_di_experiment
from employee_domain.models import Department, Employee, Manager
from employee_domain.policies import ManagerOnlyBonus, PercentageBonus, RoleBonus
from employee_domain.protocols import ReportExporter
from employee_domain.seed import DEPARTMENTS, PAYLOADS
from employee_domain.value_objects import Money

SECTIONS = ("model", "services", "payroll", "reports", "design")


def title(text: str) -> None:
    print(f"\n=== {text} ===")


def build_application() -> Container:
    """Compose the application: create departments and hire staff."""
    container = Container(notifier=MemoryNotifier())  # silent initial load
    for dep_id, name in DEPARTMENTS.items():
        container.departments.add(Department(dep_id, name))
    service = container.employee_service()
    ids = {name: dep_id for dep_id, name in DEPARTMENTS.items()}
    for payload in PAYLOADS:
        service.hire(employee_from_payload(payload), ids[payload["department"]])
    for department in container.departments:
        heads = [e for e in department if isinstance(e, Manager)]
        if heads:
            department.assign_head(max(heads))
    container.notifier = ConsoleNotifier()
    return container


def show_model() -> None:
    title("Domain model")
    salary = Money(52000)
    print("Money value object :", salary, "|", repr(salary))
    print("Money + Money      :", salary + Money(3000))
    print("Money * 1.1        :", salary * 1.1)
    try:
        Money(-5)
    except DomainError as error:
        print("Money(-5)          -> ValidationError:", error)

    it = Department(1, "IT")
    dev = employee_from_payload(PAYLOADS[0])
    lead = employee_from_payload(PAYLOADS[1])
    it.add(dev)
    assert isinstance(lead, Manager)
    it.assign_head(lead)
    print("repr(dev)          :", repr(dev))
    print("str(dev)           :", dev)
    print("str(lead)          :", lead)
    print("monthly_pay        :", dev.monthly_pay(), "/", lead.monthly_pay())
    print("Department         :", it)
    print("len / in / []      :", len(it), "|", 1 in it, "|", it[3].name)
    print("iterate            :", [e.name for e in it])
    print("max by pay (__lt__):", max(it).name)
    try:
        dev.salary = Money(5000)
    except DomainError as error:
        print("dev.salary = 5000  -> ValidationError:", error)
    dev.raise_salary(10)
    print("raise_salary(10)   :", dev.salary)
    print("Employees created  :", Employee.created_count())
    print("isinstance checks  :", isinstance(lead, Employee), isinstance(lead, Manager))


def show_services(container: Container) -> None:
    title("Employee service")
    service = container.employee_service()
    for name in DEPARTMENTS.values():
        staff = service.find_by_department(name)
        print(f"{name:<8}: {', '.join(e.name for e in staff)}")
    best = service.highest_paid()
    print("Average pay   :", service.average_pay())
    print("Highest paid  :", best, "->", best.monthly_pay() if best else "-")
    print("Total payroll :", service.total_payroll())

    print("\nHire a new developer and move Maria Tkachenko to IT:")
    result = service.hire(
        employee_from_payload(
            {"id": 13, "name": "Olena Kravets", "email": "olena.kravets@company.ua",
             "salary": 30000, "role": "developer", "department": "HR"}
        ),
        3,
    )
    print("hire result   :", "success" if result else result.error)
    service.assign_department(5, 1)
    duplicate = service.hire(employee_from_payload(PAYLOADS[0]), 1)
    print("duplicate hire:", duplicate.error)
    print("IT now        :", len(service.find_by_department("IT")), "employees")


def show_payroll(container: Container) -> None:
    title("Payroll (strategy pattern)")
    for policy in (RoleBonus(), PercentageBonus(5), ManagerOnlyBonus(Money(5000))):
        container.bonus_policy = policy
        payroll = container.payroll_service()
        records = payroll.build(container.employees, "2026-11")
        print(f"{policy.name:<24} total = {payroll.total(records)}")
    container.bonus_policy = RoleBonus()
    payroll = container.payroll_service()
    records = payroll.build(container.employees, "2026-11")
    print("\nPayroll sheet (RoleBonus):")
    for record in records:
        print(" ", record)
    payroll.notify(records, "accounting@company.ua")


def show_reports(container: Container) -> None:
    title("Department reports (ReportExporter Protocol)")
    reports = container.report_service()
    exporters: list[ReportExporter] = [TableReportExporter(), JsonReportExporter()]
    for exporter in exporters:
        print(f"{type(exporter).__name__}, isinstance(ReportExporter) =",
              isinstance(exporter, ReportExporter))
    print(reports.export(exporters[0]))
    print(reports.export(exporters[1]).split("},")[0] + "}, ...]")


def show_design() -> None:
    title("Experiment 1: concrete dependency vs dependency injection")
    run_di_experiment()
    title("Experiment 2: inheritance vs composition")
    run_composition_experiment()


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab 4: OOP employee accounting")
    parser.add_argument("--section", choices=SECTIONS, help="show one section")
    args = parser.parse_args()
    sections = [args.section] if args.section else list(SECTIONS)

    print("Laboratory work 4 - variant 6: employee accounting")
    container = build_application() if set(sections) - {"model", "design"} else None
    for section in sections:
        if section == "model":
            show_model()
        elif section == "design":
            show_design()
        elif container is not None:
            {"services": show_services, "payroll": show_payroll,
             "reports": show_reports}[section](container)


if __name__ == "__main__":
    main()
