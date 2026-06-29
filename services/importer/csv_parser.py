"""CSV parsing facade over shared validation module."""

from __future__ import annotations

from pathlib import Path

from services.importer.zip_reader import extract_csv_from_zip
from services.shared.models import ValidationResult
from services.shared.validation import detect_gaps, parse_csv_stream


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
    _, csv_bytes = extract_csv_from_zip(zip_path)
    result = parse_csv_stream(csv_bytes, symbol=symbol, timeframe=timeframe)

    if validate_gaps and result.valid_rows:
        result.warnings.extend(detect_gaps(result.valid_rows, timeframe))

    return result
