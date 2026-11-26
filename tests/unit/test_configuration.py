"""Unit tests: YAML configuration, environment overrides (monkeypatch)."""

from collections.abc import Callable
from pathlib import Path

import pytest

from employee_importer import config as config_module
from employee_importer.config import load_config
from employee_importer.exceptions import ConfigurationError

ConfigFactory = Callable[..., Path]


def test_load_config_from_yaml(make_config: ConfigFactory) -> None:
    path = make_config(minimum=30_000)
    config = load_config(path, env={})
    assert config.processing.minimum_salary == pytest.approx(30_000)
    assert config.processing.allowed_departments == {"IT", "Finance", "HR", "Sales"}
    assert config.input.path == path.parent / "staff.csv"
    assert config.output.path == path.parent / "out" / "employees.json"


def test_environment_variable_overrides_yaml(
    make_config: ConfigFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EMPLOYEE_IMPORTER_MIN_SALARY", "45000")
    monkeypatch.setenv("EMPLOYEE_IMPORTER_SKIP_INVALID", "no")
    monkeypatch.setenv("EMPLOYEE_IMPORTER_LOG_LEVEL", "debug")
    config = load_config(make_config())  # env=None -> real os.environ
    assert config.processing.minimum_salary == pytest.approx(45_000)
    assert config.processing.skip_invalid is False
    assert config.logging.level == "DEBUG"


def test_yaml_value_used_when_variable_is_removed(
    make_config: ConfigFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EMPLOYEE_IMPORTER_MIN_SALARY", "1")
    monkeypatch.delenv("EMPLOYEE_IMPORTER_MIN_SALARY")
    assert load_config(make_config()).processing.minimum_salary == 30_000


def test_invalid_environment_value_is_chained(
    make_config: ConfigFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EMPLOYEE_IMPORTER_SKIP_INVALID", "maybe")
    with pytest.raises(ConfigurationError, match="environment") as exc_info:
        load_config(make_config())
    assert isinstance(exc_info.value.__cause__, ValueError)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("version: 1", "version: 3", "Unsupported configuration version"),
        ("minimum_salary: 30000", "minimum_salary: -1", "must be >= 0"),
        ("allowed_departments: [IT, Finance, HR, Sales]", "allowed_departments: []",
         "must not be empty"),
        ("allowed_departments: [IT, Finance, HR, Sales]", "allowed_departments: IT",
         "must be a list"),
        ("format: json", "format: xml", "Output format"),
        ("level: INFO", "level: LOUD", "Unknown logging level"),
        ("path: staff.csv", "path: absent.csv", "Input file not found"),
    ],
    ids=["version", "negative-minimum", "empty-departments", "departments-string",
         "format", "log-level", "missing-input"],
)
def test_invalid_configuration_fails_fast(
    make_config: ConfigFactory, old: str, new: str, message: str
) -> None:
    path = make_config()
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(ConfigurationError, match=message):
        load_config(path, env={})


def test_missing_and_broken_files(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError) as exc_info:
        load_config(tmp_path / "nope.yaml", env={})
    assert isinstance(exc_info.value.__cause__, FileNotFoundError)
    broken = tmp_path / "broken.yaml"
    broken.write_text("input: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Invalid YAML"):
        load_config(broken, env={})


def test_os_error_while_reading_is_wrapped(
    make_config: ConfigFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_safe_load(stream: object) -> object:
        raise PermissionError("access denied")

    monkeypatch.setattr(config_module.yaml, "safe_load", broken_safe_load)
    with pytest.raises(ConfigurationError, match="Cannot read") as exc_info:
        load_config(make_config(), env={})
    assert isinstance(exc_info.value.__cause__, PermissionError)
