"""Logging setup: console + rotating file, with salary masking."""

from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler

from employee_importer.config import LoggingConfig

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_SENSITIVE = re.compile(r"(salary\s*[=:]\s*)([^\s,;|)]+)", re.IGNORECASE)


class SensitiveDataFilter(logging.Filter):
    """Masks salary values if they ever get into a log message."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        masked = _SENSITIVE.sub(r"\1***", message)
        if masked != message:
            record.msg, record.args = masked, None
        return True


def configure_logging(config: LoggingConfig) -> None:
    config.path.parent.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, config.level.upper(), logging.INFO)
    file_handler = RotatingFileHandler(
        config.path,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    console = logging.StreamHandler()
    for handler in (file_handler, console):
        handler.addFilter(SensitiveDataFilter())
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[file_handler, console],
        force=True,
    )
