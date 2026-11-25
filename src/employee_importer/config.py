"""Loading and validation of the YAML configuration (fail-fast)."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml

from employee_importer.exceptions import ConfigurationError

SUPPORTED_VERSION = 1
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
OUTPUT_FORMATS = ("json", "jsonl", "csv")
ENV_PREFIX = "EMPLOYEE_IMPORTER_"


@dataclass(frozen=True, slots=True)
class InputConfig:
    path: Path
    format: str | None  # None -> detected by the file extension


@dataclass(frozen=True, slots=True)
class OutputConfig:
    path: Path
    format: str
    errors_path: Path
    summary_path: Path
    backup: bool


@dataclass(frozen=True, slots=True)
class ProcessingConfig:
    minimum_salary: float
    skip_invalid: bool
    allowed_departments: frozenset[str]


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    level: str
    path: Path
    max_bytes: int
    backup_count: int


@dataclass(frozen=True, slots=True)
class AppConfig:
    version: int
    input: InputConfig
    output: OutputConfig
    processing: ProcessingConfig
    logging: LoggingConfig


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file)
    except FileNotFoundError as error:
        raise ConfigurationError(f"Configuration file not found: {path}") from error
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Invalid YAML in configuration {path}") from error
    except OSError as error:
        raise ConfigurationError(f"Cannot read configuration {path}") from error
    if not isinstance(raw, dict):
        raise ConfigurationError("Configuration root must be a mapping")
    return raw


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return True
    if text in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"Not a boolean: {value!r}")


def _build(raw: dict[str, Any], base: Path) -> AppConfig:
    """Map the nested YAML structure to typed dataclasses."""
    source, target = raw["input"], raw["output"]
    processing, logs = raw["processing"], raw["logging"]
    out_path = base / target["path"]
    return AppConfig(
        version=int(raw.get("version", 0)),
        input=InputConfig(base / source["path"], source.get("format")),
        output=OutputConfig(
            path=out_path,
            format=str(target.get("format", "json")).lower(),
            errors_path=base / target.get("errors_path", "output/errors.csv"),
            summary_path=base / target.get("summary_path", "output/summary.json"),
            backup=_to_bool(target.get("backup", True)),
        ),
        processing=ProcessingConfig(
            minimum_salary=float(processing["minimum_salary"]),
            skip_invalid=_to_bool(processing["skip_invalid"]),
            allowed_departments=frozenset(
                str(d) for d in processing["allowed_departments"]
            ),
        ),
        logging=LoggingConfig(
            level=str(logs.get("level", "INFO")).upper(),
            path=base / logs["path"],
            max_bytes=int(logs.get("max_bytes", 1_000_000)),
            backup_count=int(logs.get("backup_count", 3)),
        ),
    )


def apply_env_overrides(config: AppConfig, env: Mapping[str, str]) -> AppConfig:
    """Environment variables override YAML values without editing files."""
    try:
        processing, logs = config.processing, config.logging
        if (value := env.get(ENV_PREFIX + "MIN_SALARY")) is not None:
            processing = replace(processing, minimum_salary=float(value))
        if (value := env.get(ENV_PREFIX + "SKIP_INVALID")) is not None:
            processing = replace(processing, skip_invalid=_to_bool(value))
        if (value := env.get(ENV_PREFIX + "LOG_LEVEL")) is not None:
            logs = replace(logs, level=value.upper())
    except ValueError as error:
        raise ConfigurationError("Invalid environment override") from error
    return replace(config, processing=processing, logging=logs)


def validate_config(config: AppConfig) -> None:
    """Fail fast: stop before any processing if something is wrong."""
    if config.version != SUPPORTED_VERSION:
        raise ConfigurationError(
            f"Unsupported configuration version {config.version} "
            f"(expected {SUPPORTED_VERSION})"
        )
    if config.processing.minimum_salary < 0:
        raise ConfigurationError("minimum_salary must be >= 0")
    if not config.processing.allowed_departments:
        raise ConfigurationError("allowed_departments must not be empty")
    if config.output.format not in OUTPUT_FORMATS:
        raise ConfigurationError(
            f"Output format must be one of {', '.join(OUTPUT_FORMATS)}"
        )
    if config.logging.level not in LOG_LEVELS:
        raise ConfigurationError(f"Unknown logging level {config.logging.level!r}")
    if not config.input.path.is_file():
        raise ConfigurationError(f"Input file not found: {config.input.path}")


def load_config(
    path: Path, env: Mapping[str, str] | None = None
) -> AppConfig:
    """Read YAML -> typed config -> env overrides -> validation."""
    raw = _read_yaml(path)
    try:
        config = _build(raw, path.resolve().parent)
    except KeyError as error:
        raise ConfigurationError(
            f"Missing configuration key: {error.args[0]}"
        ) from error
    except (TypeError, ValueError) as error:
        raise ConfigurationError("Configuration structure is invalid") from error
    config = apply_env_overrides(config, os.environ if env is None else env)
    validate_config(config)
    return config
