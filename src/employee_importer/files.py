"""Own context managers: atomic (transaction-like) file write and timing."""

from __future__ import annotations

import logging
import os
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Literal, TextIO

from employee_importer.exceptions import DataExportError

logger = logging.getLogger(__name__)


class AtomicWriter:
    """Class-based context manager: write to *.tmp, replace the target on success.

    If the body of ``with`` raises, the temporary file is deleted and the
    previous output stays untouched. OSError becomes DataExportError (chained).
    """

    def __init__(
        self, path: Path, *, backup: bool = False, newline: str | None = None
    ) -> None:
        self.path = path
        self.temporary = path.with_suffix(path.suffix + ".tmp")
        self.backup = backup
        self.newline = newline
        self._file: TextIO | None = None

    def __enter__(self) -> TextIO:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._file = self.temporary.open(
                "w", encoding="utf-8", newline=self.newline
            )
        except OSError as error:
            raise DataExportError(f"Cannot create {self.temporary}") from error
        return self._file

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> Literal[False]:
        if self._file is not None:
            self._file.close()
        if exc_type is not None:
            self.temporary.unlink(missing_ok=True)
            logger.error(
                "Export to %s cancelled, temporary file removed", self.path.name
            )
            if isinstance(exc_value, OSError):  # low-level I/O -> domain error
                raise DataExportError(f"Cannot write {self.path.name}") from exc_value
            return False  # propagate any other exception unchanged
        try:
            if self.backup and self.path.exists():
                backup = self.path.with_suffix(self.path.suffix + ".bak")
                shutil.copy2(self.path, backup)
            os.replace(self.temporary, self.path)  # atomic on the same disk
        except OSError as error:
            self.temporary.unlink(missing_ok=True)
            raise DataExportError(f"Cannot replace {self.path}") from error
        return False


def atomic_write_text(path: Path, text: str) -> None:
    with AtomicWriter(path) as file:
        file.write(text)


@contextmanager
def logged_operation(operation: str) -> Iterator[None]:
    """Generator-based context manager: logs start, failure or duration."""
    logger.info("%s started", operation)
    start = perf_counter()
    try:
        yield
    except Exception:
        logger.exception("%s failed", operation)
        raise
    else:
        logger.info("%s finished in %.4f s", operation, perf_counter() - start)
