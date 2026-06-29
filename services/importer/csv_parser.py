"""CSV parsing facade over shared validation module."""

from __future__ import annotations

from services.importer.zip_reader import extract_csv_from_zip
from services.shared.models import ValidationResult
from services.shared.validation import detect_gaps, parse_csv_stream
from pathlib import Path


def parse_zip_klines(
    zip_path: Path,
    symbol: str,
    timeframe: str,
    validate_gaps: bool = True,
) -> ValidationResult:
    """
    Extract CSV from ZIP in memory and parse/validate kline rows.

    Optionally detects missing candles within the file.
    """
    _, csv_bytes = extract_csv_from_zip(zip_path)
    result = parse_csv_stream(csv_bytes, symbol=symbol, timeframe=timeframe)

    if validate_gaps and result.valid_rows:
        gap_warnings = detect_gaps(result.valid_rows, timeframe)
        result.warnings.extend(gap_warnings)

    return result
