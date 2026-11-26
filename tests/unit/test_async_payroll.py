"""Unit tests: AsyncPayrollService with AsyncMock provider."""

from unittest.mock import AsyncMock, Mock, call

import pytest

from employee_domain.async_payroll import (
    AsyncPayrollService,
    PayrollProvider,
    PayrollProviderError,
)
from employee_domain.exceptions import ValidationError
from employee_domain.models import Employee
from employee_domain.protocols import Notifier


@pytest.fixture
def provider() -> AsyncMock:
    return AsyncMock(spec=PayrollProvider)


@pytest.mark.asyncio
async def test_payroll_with_async_provider(
    staff: list[Employee], provider: AsyncMock
) -> None:
    provider.fetch_bonus.return_value = 1_000
    notifier = Mock(spec=Notifier)
    service = AsyncPayrollService(provider, notifier)

    total = await service.run(staff, "2026-11", "accounting@company.ua")

    assert total.amount == pytest.approx(266_000 + 5 * 1_000)
    assert provider.fetch_bonus.await_count == 5
    provider.fetch_bonus.assert_any_await(3, "2026-11")
    provider.fetch_bonus.assert_awaited_with(9, "2026-11")  # the last call
    notifier.send.assert_called_once_with(
        "accounting@company.ua", "Payroll 2026-11: 5 records, total 271 000.00 UAH"
    )


@pytest.mark.asyncio
async def test_temporary_failure_is_retried(
    developer: Employee, provider: AsyncMock
) -> None:
    provider.fetch_bonus.side_effect = [ConnectionError("timeout"), 2_500.0]
    service = AsyncPayrollService(provider, Mock(spec=Notifier))

    [record] = await service.build([developer], "2026-11")

    assert record.bonus.amount == pytest.approx(2_500)
    assert provider.fetch_bonus.await_args_list == [
        call(1, "2026-11"), call(1, "2026-11")
    ]


@pytest.mark.asyncio
async def test_provider_down_raises_and_skips_notification(
    staff: list[Employee], provider: AsyncMock
) -> None:
    provider.fetch_bonus.side_effect = ConnectionError("payroll API is down")
    notifier = Mock(spec=Notifier)
    service = AsyncPayrollService(provider, notifier, retries=2)

    with pytest.raises(PayrollProviderError, match="unavailable") as exc_info:
        await service.run(staff, "2026-11", "accounting@company.ua")

    assert isinstance(exc_info.value.__cause__, ConnectionError)
    assert provider.fetch_bonus.await_count == 3  # 1 call + 2 retries
    notifier.send.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("value", "cause"),
    [(-5, ValidationError), ("abc", ValueError), (None, TypeError)],
    ids=["negative", "text", "none"],
)
async def test_invalid_bonus_from_provider(
    developer: Employee, provider: AsyncMock, value: object, cause: type
) -> None:
    provider.fetch_bonus.return_value = value
    service = AsyncPayrollService(provider, Mock(spec=Notifier))
    with pytest.raises(PayrollProviderError, match="Invalid bonus") as exc_info:
        await service.build([developer], "2026-11")
    assert isinstance(exc_info.value.__cause__, cause)
    provider.fetch_bonus.assert_awaited_once_with(1, "2026-11")


def test_negative_retries_are_rejected(provider: AsyncMock) -> None:
    with pytest.raises(ValueError, match="retries"):
        AsyncPayrollService(provider, Mock(spec=Notifier), retries=-1)
