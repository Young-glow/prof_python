"""Design experiments: hard-coded dependency vs DI, inheritance vs composition."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Protocol

from employee_domain.adapters import ConsoleNotifier, MemoryNotifier
from employee_domain.protocols import Notifier

# ---------------------------------------------------------------------------
# Experiment 1. Variant A (concrete dependency) vs variant B (injection)
# ---------------------------------------------------------------------------


class PayrollNotifierA:
    """Variant A: the service creates its concrete dependency itself."""

    def __init__(self) -> None:
        self.notifier = ConsoleNotifier()  # tight coupling

    def payroll_ready(self, email: str, total: float) -> None:
        self.notifier.send(email, f"Payroll ready: {total:.2f} UAH")


class PayrollNotifierB:
    """Variant B: the dependency is injected through an abstraction."""

    def __init__(self, notifier: Notifier) -> None:
        self.notifier = notifier

    def payroll_ready(self, email: str, total: float) -> None:
        self.notifier.send(email, f"Payroll ready: {total:.2f} UAH")


def run_di_experiment() -> None:
    print("Variant A (creates ConsoleNotifier inside):")
    PayrollNotifierA().payroll_ready("accounting@company.ua", 419160)
    print("  -> to test it we can only look at the console output.")

    print("Variant B (Notifier injected):")
    PayrollNotifierB(ConsoleNotifier()).payroll_ready(
        "accounting@company.ua", 419160
    )
    fake = MemoryNotifier()
    PayrollNotifierB(fake).payroll_ready("accounting@company.ua", 419160)
    print(f"  -> with MemoryNotifier the message is captured: {fake.messages}")


# ---------------------------------------------------------------------------
# Experiment 2. The same behaviour by inheritance and by composition
# ---------------------------------------------------------------------------

Row = dict[str, str]
SAMPLE = "name,salary\nAnna Koval,52000\nBad Row,abc\nIryna Bondar,68000"


class BaseProcessor(ABC):
    """Inheritance: template method, steps are overridden in subclasses."""

    def process(self, text: str) -> str:
        rows = self.parse(text)
        valid = [row for row in rows if self.validate(row)]
        return self.format(valid)

    @abstractmethod
    def parse(self, text: str) -> list[Row]: ...

    @abstractmethod
    def validate(self, row: Row) -> bool: ...

    @abstractmethod
    def format(self, rows: list[Row]) -> str: ...


class CsvProcessor(BaseProcessor):
    def parse(self, text: str) -> list[Row]:
        header, *lines = text.splitlines()
        keys = header.split(",")
        return [dict(zip(keys, line.split(","), strict=True)) for line in lines]

    def validate(self, row: Row) -> bool:
        return row["salary"].isdigit()

    def format(self, rows: list[Row]) -> str:
        return "; ".join(f"{r['name']}={r['salary']}" for r in rows)


class CsvJsonProcessor(CsvProcessor):
    """A new output format needs one more subclass in the hierarchy."""

    def format(self, rows: list[Row]) -> str:
        return json.dumps(rows)


class Parser(Protocol):
    def parse(self, text: str) -> list[Row]: ...


class Validator(Protocol):
    def validate(self, row: Row) -> bool: ...


class Formatter(Protocol):
    def format(self, rows: list[Row]) -> str: ...


class CsvParser:
    def parse(self, text: str) -> list[Row]:
        header, *lines = text.splitlines()
        keys = header.split(",")
        return [dict(zip(keys, line.split(","), strict=True)) for line in lines]


class SalaryValidator:
    def validate(self, row: Row) -> bool:
        return row["salary"].isdigit()


class TextFormatter:
    def format(self, rows: list[Row]) -> str:
        return "; ".join(f"{r['name']}={r['salary']}" for r in rows)


class JsonFormatter:
    def format(self, rows: list[Row]) -> str:
        return json.dumps(rows)


class Processor:
    """Composition: Processor HAS a parser, a validator and a formatter."""

    def __init__(
        self, parser: Parser, validator: Validator, formatter: Formatter
    ) -> None:
        self.parser = parser
        self.validator = validator
        self.formatter = formatter

    def process(self, text: str) -> str:
        rows = self.parser.parse(text)
        valid = [row for row in rows if self.validator.validate(row)]
        return self.formatter.format(valid)


def run_composition_experiment() -> None:
    print("Inheritance  CsvProcessor     :", CsvProcessor().process(SAMPLE))
    print("Inheritance  CsvJsonProcessor :", CsvJsonProcessor().process(SAMPLE))
    text = Processor(CsvParser(), SalaryValidator(), TextFormatter())
    print("Composition  text formatter   :", text.process(SAMPLE))
    as_json = Processor(CsvParser(), SalaryValidator(), JsonFormatter())
    print("Composition  json formatter   :", as_json.process(SAMPLE))
    print("  -> composition swaps one component; inheritance adds a subclass.")
