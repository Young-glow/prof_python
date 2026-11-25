"""Entry point: reliable import -> validation -> filtering -> atomic export."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from employee_importer.config import AppConfig, load_config
from employee_importer.exceptions import ApplicationError
from employee_importer.exporters import get_exporter, write_error_report, write_summary
from employee_importer.files import logged_operation
from employee_importer.logging_config import LOG_FORMAT, configure_logging
from employee_importer.models import ImportStatistics, InvalidRecord
from employee_importer.readers import get_importer
from employee_importer.services import filter_by_min_salary, import_employees
from employee_importer.validators import policy_for

logger = logging.getLogger("employee_importer")


def _shown(path: Path) -> str:
    """Path relative to the working directory (shorter, no user names)."""
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.name


def run(config: AppConfig) -> ImportStatistics:
    """The whole pipeline; any domain error propagates to main()."""
    statistics = ImportStatistics()
    rejected: list[InvalidRecord] = []
    policy = policy_for(config.processing.skip_invalid)
    importer = get_importer(config.input.path, config.input.format)
    exporter = get_exporter(config.output.format, backup=config.output.backup)
    logger.info(
        "Input=%s (%s), output=%s, mode=%s",
        config.input.path.name,
        type(importer).__name__,
        config.output.path.name,
        policy.name,
    )
    with logged_operation("Employee import/export"):
        employees = import_employees(
            importer,
            config.input.path,
            allowed_departments=config.processing.allowed_departments,
            policy=policy,
            statistics=statistics,
            rejected=rejected,
        )
        selected = filter_by_min_salary(
            employees, config.processing.minimum_salary, statistics
        )
        statistics.exported = exporter.export(selected, config.output.path)

    write_error_report(rejected, config.output.errors_path)
    write_summary(
        {
            "finished_at": datetime.now().replace(microsecond=0),
            "input": _shown(config.input.path),
            "output": _shown(config.output.path),
            "mode": policy.name,
            "allowed_departments": config.processing.allowed_departments,
            "statistics": statistics.as_dict(),
        },
        config.output.summary_path,
    )
    logger.info(
        "Total=%s, valid=%s, invalid=%s, filtered=%s, exported=%s",
        statistics.total,
        statistics.valid,
        statistics.invalid,
        statistics.filtered_out,
        statistics.exported,
    )
    logger.info(
        "Errors report: %s, summary: %s",
        config.output.errors_path.name,
        config.output.summary_path.name,
    )
    return statistics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lab 5: employee import/export")
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument(
        "--experiment",
        choices=("strict", "memory", "chaining", "atomic", "config", "all"),
        help="run an experiment instead of the import",
    )
    args = parser.parse_args(argv)

    # console logging until the configuration is known
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt="%H:%M:%S")

    if args.experiment:
        from employee_importer import experiments

        experiments.run(args.experiment)
        return 0

    try:
        config = load_config(args.config)
        configure_logging(config.logging)
        run(config)
    except ApplicationError as error:
        # critical error: log a meaningful message and exit with code 1
        logger.error("Application stopped: %s: %s", type(error).__name__, error)
        if error.__cause__ is not None:
            logger.error("Caused by %s: %s", type(error.__cause__).__name__,
                         error.__cause__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
