"""Kline CSV validation and gap detection utilities."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone

from services.shared.models import KlineRow, ValidationResult

CSV_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
    "ignore",
]

TIMEFRAME_MS: dict[str, int] = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
    "1mo": 2_592_000_000,
}


def ms_to_datetime(ms: int | str) -> datetime:
    """Convert millisecond timestamp to UTC datetime."""
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc)


def is_header_row(row: list[str]) -> bool:
    """Detect CSV header rows (some Binance files include column names)."""
    if not row:
        return False
    first = row[0].strip().lower()
    return first in {"open_time", "timestamp", "time", "date"}


def _parse_row(
    row: list[str],
    row_num: int,
    symbol: str,
    timeframe: str,
    seen_open_times: set[int],
    result: ValidationResult,
) -> KlineRow | None:
    """Parse a single CSV row into a KlineRow, updating result metadata."""
    if len(row) < 11:
        result.invalid_count += 1
        result.errors.append(f"Row {row_num}: expected >= 11 columns, got {len(row)}")
        return None

    try:
        open_ms = int(row[0])
        if open_ms <= 0:
            raise ValueError("open_time must be positive")

        if open_ms in seen_open_times:
            result.duplicate_count += 1
            result.warnings.append(f"Row {row_num}: duplicate open_time {open_ms}")
            return None

        seen_open_times.add(open_ms)

        kline = KlineRow(
            symbol=symbol,
            timeframe=timeframe,
            open_time=ms_to_datetime(open_ms),
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[5]),
            close_time=ms_to_datetime(int(row[6])),
            quote_volume=float(row[7]),
            trade_count=int(row[8]),
            taker_buy_volume=float(row[9]),
            taker_buy_quote_volume=float(row[10]),
        )

        if kline.high < kline.low:
            result.invalid_count += 1
            result.errors.append(f"Row {row_num}: high < low")
            return None

        if kline.open < kline.low or kline.open > kline.high:
            result.invalid_count += 1
            result.errors.append(f"Row {row_num}: open outside high/low range")
            return None

        if kline.close < kline.low or kline.close > kline.high:
            result.invalid_count += 1
            result.errors.append(f"Row {row_num}: close outside high/low range")
            return None

        return kline

    except (ValueError, IndexError) as exc:
        result.invalid_count += 1
        result.errors.append(f"Row {row_num}: parse error — {exc}")
        return None


def parse_csv_stream(
    content: str | bytes,
    symbol: str,
    timeframe: str,
) -> ValidationResult:
    """
    Parse and validate kline CSV content from memory.

    Detects duplicates, invalid rows, wrong timestamps, and empty files.
    Skips header rows when present.
    """
    if isinstance(content, bytes):
        text = content.decode("utf-8")
    else:
        text = content

    if not text.strip():
        result = ValidationResult()
        result.errors.append("Empty CSV file")
        return result

    reader = csv.reader(io.StringIO(text))
    return _parse_csv_reader(reader, symbol, timeframe)


def iter_kline_batches(
    rows: Iterable[list[str]],
    symbol: str,
    timeframe: str,
    batch_size: int,
    validate_gaps: bool = True,
) -> tuple[Iterator[list[KlineRow]], ValidationResult]:
    """
    Stream-parse CSV rows and yield batches for memory-efficient insertion.

    Returns (batch_iterator, validation_result). Gap warnings are populated
    after the iterator is exhausted.
    """
    result = ValidationResult()
    seen_open_times: set[int] = set()
    open_times_for_gaps: list[int] = []
    row_num = 0
    batch: list[KlineRow] = []

    def _generator() -> Iterator[list[KlineRow]]:
        nonlocal row_num, batch

        for row in rows:
            row_num += 1

            if row_num == 1 and is_header_row(row):
                result.warnings.append("Skipped CSV header row")
                continue

            kline = _parse_row(row, row_num, symbol, timeframe, seen_open_times, result)
            if kline is None:
                continue

            open_times_for_gaps.append(int(kline.open_time.timestamp() * 1000))
            batch.append(kline)

            if len(batch) >= batch_size:
                chunk = batch
                batch = []
                yield chunk

        if batch:
            yield batch

        if row_num == 0:
            result.errors.append("CSV contains no data rows")

        if validate_gaps:
            result.warnings.extend(detect_gaps_from_ms(open_times_for_gaps, timeframe))

    return _generator(), result


def _parse_csv_reader(
    reader: csv.reader | Iterator[list[str]],
    symbol: str,
    timeframe: str,
) -> ValidationResult:
    result = ValidationResult()
    seen_open_times: set[int] = set()
    row_num = 0

    for row in reader:
        row_num += 1

        if row_num == 1 and is_header_row(row):
            result.warnings.append("Skipped CSV header row")
            continue

        kline = _parse_row(row, row_num, symbol, timeframe, seen_open_times, result)
        if kline is not None:
            result.valid_rows.append(kline)

    if row_num == 0:
        result.errors.append("CSV contains no data rows")

    return result


def detect_gaps_from_ms(open_times_ms: list[int], timeframe: str) -> list[str]:
    """Detect missing candles from a sorted list of open_time millisecond values."""
    if len(open_times_ms) < 2:
        return []

    interval_ms = TIMEFRAME_MS.get(timeframe)
    if interval_ms is None:
        return [f"Unknown timeframe for gap detection: {timeframe}"]

    warnings: list[str] = []
    sorted_times = sorted(open_times_ms)

    for i in range(1, len(sorted_times)):
        prev_ms = sorted_times[i - 1]
        curr_ms = sorted_times[i]
        expected = prev_ms + interval_ms

        if curr_ms > expected:
            missing = (curr_ms - expected) // interval_ms
            if missing > 0:
                warnings.append(
                    f"Gap detected: {missing} missing candle(s) between "
                    f"{ms_to_datetime(prev_ms).isoformat()} and "
                    f"{ms_to_datetime(curr_ms).isoformat()}"
                )

    return warnings


def detect_gaps(
    rows: list[KlineRow],
    timeframe: str,
) -> list[str]:
    """
    Detect missing candles based on expected interval between open_time values.

    Returns list of warning messages for each detected gap.
    """
    if len(rows) < 2:
        return []

    interval_ms = TIMEFRAME_MS.get(timeframe)
    if interval_ms is None:
        return [f"Unknown timeframe for gap detection: {timeframe}"]

    warnings: list[str] = []
    sorted_rows = sorted(rows, key=lambda r: r.open_time)

    for i in range(1, len(sorted_rows)):
        prev_ms = int(sorted_rows[i - 1].open_time.timestamp() * 1000)
        curr_ms = int(sorted_rows[i].open_time.timestamp() * 1000)
        expected = prev_ms + interval_ms

        if curr_ms > expected:
            missing = (curr_ms - expected) // interval_ms
            if missing > 0:
                warnings.append(
                    f"Gap detected: {missing} missing candle(s) between "
                    f"{sorted_rows[i - 1].open_time.isoformat()} and "
                    f"{sorted_rows[i].open_time.isoformat()}"
                )

    return warnings


def iter_batches(rows: list[KlineRow], batch_size: int) -> Iterator[list[KlineRow]]:
    """Yield slices of rows for batch insertion."""
    for i in range(0, len(rows), batch_size):
        yield rows[i : i + batch_size]
