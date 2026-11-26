"""Asynchronous payroll: bonuses come from an external async provider."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Protocol

from employee_domain.exceptions import DomainError
from employee_domain.models import Employee, PayrollRecord
from employee_domain.protocols import Notifier
from employee_domain.value_objects import Money

logger = logging.getLogger(__name__)


class PayrollProvider(Protocol):
    """External system (e.g. an HTTP API of the accounting department)."""

    async def fetch_bonus(self, employee_id: int, period: str) -> float: ...


class PayrollProviderError(DomainError):
    """The external payroll provider is unavailable or returned bad data."""


class AsyncPayrollService:
    """employee -> async bonus -> PayrollRecord -> total -> notification."""

    def __init__(
        self, provider: PayrollProvider, notifier: Notifier, *, retries: int = 2
    ) -> None:
        if retries < 0:
            raise ValueError("retries must be >= 0")
        self._provider = provider
        self._notifier = notifier
        self._retries = retries

    async def _fetch_bonus(self, employee: Employee, period: str) -> Money:
        last_error: Exception | None = None
        for attempt in range(1, self._retries + 2):
            try:
                value = await self._provider.fetch_bonus(employee.id, period)
            except (ConnectionError, TimeoutError) as error:
                last_error = error
                logger.warning(
                    "Provider failed for employee #%s (attempt %s)",
                    employee.id,
                    attempt,
                )
                continue
            try:
                return Money(round(float(value), 2), employee.salary.currency)
            except (TypeError, ValueError, DomainError) as error:
                raise PayrollProviderError(
                    f"Invalid bonus for employee #{employee.id}"
                ) from error
        raise PayrollProviderError(
            f"Payroll provider unavailable for employee #{employee.id}"
        ) from last_error

    async def build(
        self, employees: Iterable[Employee], period: str
    ) -> list[PayrollRecord]:
        records = []
        for employee in employees:
            bonus = await self._fetch_bonus(employee, period)
            records.append(
                PayrollRecord(
                    employee.id,
                    employee.name,
                    employee.role,
                    employee.department or "-",
                    period,
                    employee.salary,
                    bonus,
                )
            )
        return records

    async def run(
        self, employees: Iterable[Employee], period: str, accounting: str
    ) -> Money:
        """Build the payroll and notify accounting only if everything succeeded."""
        records = await self.build(employees, period)
        total = Money.zero()
        for record in records:
            total = total + record.total
        self._notifier.send(
            accounting, f"Payroll {period}: {len(records)} records, total {total}"
        )
        return total
