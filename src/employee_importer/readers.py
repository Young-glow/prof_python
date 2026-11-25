"""Streaming importers behind one Protocol; the format is chosen by extension."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Protocol

import yaml

from employee_importer.exceptions import DataImportError, UnsupportedFormatError

Row = dict[str, Any]
NumberedRow = tuple[int, Row]


class Importer(Protocol):
    """Reads records one by one together with their line/position number."""

    def read(self, path: Path) -> Iterator[NumberedRow]: ...


class CsvImporter:
    """True streaming: only one row is kept in memory."""

    def read(self, path: Path) -> Iterator[NumberedRow]:
        try:
            with path.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames is None:
                    raise DataImportError(f"CSV file is empty: {path.name}")
                yield from enumerate(reader, start=2)
        except OSError as error:
            raise DataImportError(f"Cannot read input file: {path}") from error
        except csv.Error as error:
            raise DataImportError(f"Malformed CSV in {path.name}") from error


class JsonLinesImporter:
    """Streaming: one JSON object per line."""

    def read(self, path: Path) -> Iterator[NumberedRow]:
        try:
            with path.open("r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, start=1):
                    if not line.strip():
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError as error:
                        raise DataImportError(
                            f"Invalid JSON at line {line_number}"
                        ) from error
                    yield line_number, item
        except OSError as error:
            raise DataImportError(f"Cannot read input file: {path}") from error


class JsonImporter:
    """JSON array: the document is parsed as a whole (not streaming)."""

    def read(self, path: Path) -> Iterator[NumberedRow]:
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except OSError as error:
            raise DataImportError(f"Cannot read input file: {path}") from error
        except json.JSONDecodeError as error:
            raise DataImportError(f"Invalid JSON document {path.name}") from error
        if not isinstance(data, list):
            raise DataImportError("JSON input must be an array of objects")
        yield from enumerate(data, start=1)


class YamlImporter:
    """YAML list of mappings, loaded with safe_load (no arbitrary objects)."""

    def read(self, path: Path) -> Iterator[NumberedRow]:
        try:
            with path.open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file)
        except OSError as error:
            raise DataImportError(f"Cannot read input file: {path}") from error
        except yaml.YAMLError as error:
            raise DataImportError(f"Invalid YAML document {path.name}") from error
        if not isinstance(data, list):
            raise DataImportError("YAML input must be a list of records")
        yield from enumerate(data, start=1)


IMPORTERS: dict[str, type[Importer]] = {
    "csv": CsvImporter,
    "jsonl": JsonLinesImporter,
    "json": JsonImporter,
    "yaml": YamlImporter,
    "yml": YamlImporter,
}


def get_importer(path: Path, fmt: str | None = None) -> Importer:
    """Pick an importer by explicit format or by the file extension."""
    key = (fmt or path.suffix.lstrip(".")).lower()
    try:
        return IMPORTERS[key]()
    except KeyError as error:
        raise UnsupportedFormatError(key) from error
