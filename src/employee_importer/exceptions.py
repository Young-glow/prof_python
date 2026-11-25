"""Domain-specific exception hierarchy.

ApplicationError
├── ConfigurationError
└── DataError
    ├── DataImportError
    │   └── UnsupportedFormatError
    ├── DataValidationError
    │   └── RecordValidationError
    └── DataExportError
"""


class ApplicationError(Exception):
    """Base exception of the application."""


class ConfigurationError(ApplicationError):
    """Configuration is missing or invalid."""


class DataError(ApplicationError):
    """Base exception for problems with data."""


class DataImportError(DataError):
    """Input data cannot be read or parsed."""


class UnsupportedFormatError(DataImportError):
    """File format is not supported by any importer/exporter."""

    def __init__(self, fmt: str) -> None:
        super().__init__(f"Unsupported data format: {fmt!r}")
        self.format = fmt


class DataValidationError(DataError):
    """Base exception for invalid data."""


class RecordValidationError(DataValidationError):
    """One input record is invalid; keeps the position of the problem."""

    def __init__(
        self,
        message: str,
        *,
        line_number: int | None = None,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.line_number = line_number
        self.field = field

    def __str__(self) -> str:
        where = f"line {self.line_number}" if self.line_number else "unknown line"
        column = f", field '{self.field}'" if self.field else ""
        return f"{where}{column}: {self.args[0]}"


class DataExportError(DataError):
    """Output cannot be written."""
