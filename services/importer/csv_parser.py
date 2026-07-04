"""CSV parsing facade over shared validation module."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from services.importer.zip_reader import extract_csv_from_zip
from services.shared.models import ValidationResult
from services.shared.validation import detect_gaps, parse_csv_stream


class KlineCsvParser(Protocol):
    """Parse and validate kline CSV payloads."""

    def parse_stream(self, data: bytes, *, symbol: str, timeframe: str) -> ValidationResult: ...
    def parse_zip(
        self,
        zip_path: Path,
        symbol: str,
        timeframe: str,
        *,
        validate_gaps: bool = True,
    ) -> ValidationResult: ...


class DefaultKlineCsvParser:
    """Stateless parser using shared validation utilities."""

    def parse_stream(self, data: bytes, *, symbol: str, timeframe: str) -> ValidationResult:
        return parse_csv_stream(data, symbol=symbol, timeframe=timeframe)

    def parse_zip(
        self,
        zip_path: Path,
        symbol: str,
        timeframe: str,
        *,
        validate_gaps: bool = True,
    ) -> ValidationResult:
        _, csv_bytes = extract_csv_from_zip(zip_path)
        result = self.parse_stream(csv_bytes, symbol=symbol, timeframe=timeframe)
        if validate_gaps and result.valid_rows:
            result.warnings.extend(detect_gaps(result.valid_rows, timeframe))
        return result


_default_parser = DefaultKlineCsvParser()


def parse_zip_klines(
    zip_path: Path,
    symbol: str,
    timeframe: str,
    validate_gaps: bool = True,
) -> ValidationResult:
    """
    Extract CSV from ZIP in memory and parse/validate kline rows.

    Prefer streaming via open_csv_reader + iter_kline_batches in the worker
    for large files.
    """
    return _default_parser.parse_zip(
        zip_path,
        symbol,
        timeframe,
        validate_gaps=validate_gaps,
    )


def parse_csv_bytes(data: bytes, *, symbol: str, timeframe: str) -> ValidationResult:
    """Parse raw CSV bytes without touching the filesystem."""
    return _default_parser.parse_stream(data, symbol=symbol, timeframe=timeframe)
