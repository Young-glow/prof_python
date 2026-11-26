"""Unit tests: AtomicWriter / logged_operation context managers, log masking."""

import logging
from pathlib import Path

import pytest

from employee_importer.exceptions import DataExportError
from employee_importer.files import AtomicWriter, logged_operation
from employee_importer.logging_config import SensitiveDataFilter


def test_atomic_writer_replaces_file_and_keeps_backup(tmp_path: Path) -> None:
    target = tmp_path / "out" / "employees.json"
    with AtomicWriter(target) as file:
        file.write("old")
    with AtomicWriter(target, backup=True) as file:
        file.write("new")
    assert target.read_text(encoding="utf-8") == "new"
    backup = tmp_path / "out" / "employees.json.bak"
    assert backup.read_text(encoding="utf-8") == "old"
    assert not (tmp_path / "out" / "employees.json.tmp").exists()


def test_cleanup_when_exception_inside_with(tmp_path: Path) -> None:
    target = tmp_path / "employees.json"
    target.write_text("old valid data", encoding="utf-8")
    writer = AtomicWriter(target)
    with pytest.raises(DataExportError) as exc_info, writer as file:
        file.write("partial")
        raise OSError(28, "No space left on device")
    assert isinstance(exc_info.value.__cause__, OSError)
    assert file.closed
    assert target.read_text(encoding="utf-8") == "old valid data"
    assert not writer.temporary.exists()


def test_other_exceptions_are_not_converted(tmp_path: Path) -> None:
    target = tmp_path / "employees.json"
    with pytest.raises(ValueError, match="bug"), AtomicWriter(target):
        raise ValueError("bug in caller")
    assert not target.exists()


def test_logged_operation(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO), logged_operation("Import"):
        pass
    assert "Import started" in caplog.text
    assert "Import finished in" in caplog.text
    caplog.clear()
    with (
        pytest.raises(KeyError),
        caplog.at_level(logging.INFO),
        logged_operation("Export"),
    ):
        raise KeyError("x")
    assert caplog.records[-1].levelname == "ERROR"
    assert caplog.records[-1].exc_info is not None  # logger.exception


def test_salary_is_masked_in_log_file(importer_logging: Path) -> None:
    logging.getLogger("employee_importer.test").warning("Row 5: salary=41000 rejected")
    for handler in logging.getLogger().handlers:
        handler.flush()
    text = importer_logging.read_text(encoding="utf-8")
    assert "salary=***" in text
    assert "41000" not in text


def test_filter_leaves_other_messages() -> None:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "id=%s", ("5",), None)
    assert SensitiveDataFilter().filter(record) is True
    assert record.getMessage() == "id=5"
