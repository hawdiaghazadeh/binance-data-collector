"""Unit tests for CSV parser and validation."""

from __future__ import annotations

import io
import zipfile
from datetime import timezone
from pathlib import Path

import pytest

from services.importer.csv_parser import parse_zip_klines
from services.importer.zip_reader import ZipReadError, extract_csv_from_zip
from services.shared.validation import detect_gaps, parse_csv_stream


SAMPLE_CSV = """\
1609459200000,28923.63,29600.00,28803.59,29359.90,12345.67,1609462799999,360000000.00,50000,6000.00,175000000.00,0
1609462800000,29359.90,29450.00,29200.00,29300.00,10000.00,1609466399999,290000000.00,45000,5000.00,145000000.00,0
"""


@pytest.fixture
def sample_zip(tmp_path: Path) -> Path:
    zip_path = tmp_path / "BTCUSDT-1h-2021-01.zip"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("BTCUSDT-1h-2021-01.csv", SAMPLE_CSV)
    zip_path.write_bytes(buffer.getvalue())
    return zip_path


def test_parse_csv_stream_valid_rows() -> None:
    result = parse_csv_stream(SAMPLE_CSV, symbol="BTCUSDT", timeframe="1h")
    assert result.row_count == 2
    assert result.duplicate_count == 0
    assert not result.has_errors
    assert result.valid_rows[0].symbol == "BTCUSDT"
    assert result.valid_rows[0].open_time.tzinfo == timezone.utc


def test_parse_csv_stream_empty_file() -> None:
    result = parse_csv_stream("", symbol="BTCUSDT", timeframe="1h")
    assert result.row_count == 0
    assert "Empty CSV file" in result.errors[0]


def test_parse_csv_stream_duplicate_detection() -> None:
    duplicate_csv = SAMPLE_CSV + SAMPLE_CSV.split("\n")[0] + "\n"
    result = parse_csv_stream(duplicate_csv, symbol="BTCUSDT", timeframe="1h")
    assert result.duplicate_count >= 1


def test_parse_csv_stream_invalid_high_low() -> None:
    bad_csv = "1609459200000,100,50,200,75,1,1609462799999,1,1,1,1,0\n"
    result = parse_csv_stream(bad_csv, symbol="BTCUSDT", timeframe="1h")
    assert result.invalid_count >= 1


def test_parse_csv_stream_skips_header_row() -> None:
    csv_with_header = (
        "open_time,open,high,low,close,volume,close_time,quote_volume,count,"
        "taker_buy_volume,taker_buy_quote_volume,ignore\n"
        + SAMPLE_CSV
    )
    result = parse_csv_stream(csv_with_header, symbol="BTCUSDT", timeframe="1h")
    assert result.row_count == 2
    assert result.invalid_count == 0
    assert "Skipped CSV header row" in result.warnings


def test_extract_csv_from_zip(sample_zip: Path) -> None:
    name, content = extract_csv_from_zip(sample_zip)
    assert name.endswith(".csv")
    assert b"1609459200000" in content


def test_extract_csv_from_empty_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "empty.zip"
    zip_path.write_bytes(b"")
    with pytest.raises(ZipReadError):
        extract_csv_from_zip(zip_path)


def test_extract_csv_from_corrupted_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "bad.zip"
    zip_path.write_text("not a zip file", encoding="utf-8")
    with pytest.raises(ZipReadError):
        extract_csv_from_zip(zip_path)


def test_parse_zip_klines(sample_zip: Path) -> None:
    result = parse_zip_klines(
        sample_zip,
        symbol="BTCUSDT",
        timeframe="1h",
        validate_gaps=False,
    )
    assert result.row_count == 2


def test_detect_gaps() -> None:
    result = parse_csv_stream(SAMPLE_CSV, symbol="BTCUSDT", timeframe="1h")
    gaps = detect_gaps(result.valid_rows, "1h")
    assert isinstance(gaps, list)
