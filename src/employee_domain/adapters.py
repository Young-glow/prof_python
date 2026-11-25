"""Concrete implementations of the protocols (they do NOT inherit them)."""

import json

from employee_domain.dto import DepartmentReport


class ConsoleNotifier:
    def send(self, recipient: str, message: str) -> None:
        print(f"  [notify -> {recipient}] {message}")


class MemoryNotifier:
    """Test double: collects messages instead of printing them."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def send(self, recipient: str, message: str) -> None:
        self.messages.append((recipient, message))


class TableReportExporter:
    def export(self, reports: list[DepartmentReport]) -> str:
        header = (
            f"{'Department':<10} {'Head':<18} {'Staff':>5} "
            f"{'Average':>11} {'Max':>11} {'Payroll':>12}"
        )
        lines = [header, "-" * len(header)]
        for row in reports:
            lines.append(
                f"{row['department']:<10} {row['head']:<18} {row['employees']:>5} "
                f"{row['average_pay']:>11.2f} {row['max_pay']:>11.2f} "
                f"{row['payroll']:>12.2f}"
            )
        return "\n".join(lines)


class JsonReportExporter:
    def export(self, reports: list[DepartmentReport]) -> str:
        return json.dumps(reports, ensure_ascii=False, indent=2)
