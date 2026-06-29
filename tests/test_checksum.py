"""Unit tests for checksum utilities."""

from __future__ import annotations

from pathlib import Path

from services.shared.checksum import (
    compute_file_sha256,
    parse_checksum_file,
    verify_file_checksum,
)


def test_parse_checksum_file() -> None:
    content = "a" * 64 + "  BTCUSDT-1h-2021-01.zip\n"
    result = parse_checksum_file(content)
    assert "BTCUSDT-1h-2021-01.zip" in result
    assert len(result["BTCUSDT-1h-2021-01.zip"]) == 64


def test_compute_and_verify_sha256(tmp_path: Path) -> None:
    file_path = tmp_path / "test.bin"
    file_path.write_bytes(b"hello world")

    digest = compute_file_sha256(file_path)
    assert len(digest) == 64
    assert verify_file_checksum(file_path, digest) is True
    assert verify_file_checksum(file_path, "0" * 64) is False
