"""In-memory ZIP extraction — no permanent CSV files on disk."""

from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import structlog

logger = structlog.get_logger("importer.zip_reader")


class ZipReadError(Exception):
    """Raised when a ZIP file cannot be read or is corrupted."""


def _select_csv_member(zf: zipfile.ZipFile) -> str:
    csv_members = [m for m in zf.namelist() if m.lower().endswith(".csv")]
    if not csv_members:
        raise ZipReadError("No CSV found in ZIP")
    if len(csv_members) > 1:
        logger.warning("multiple_csv_in_zip", count=len(csv_members))
    return csv_members[0]


@contextmanager
def open_csv_reader(zip_path: Path) -> Generator[csv.reader, None, None]:
    """
    Stream CSV rows directly from a ZIP archive without loading the full file.

    Memory-efficient: reads and parses incrementally from the ZIP member.
    """
    if not zip_path.exists():
        raise ZipReadError(f"ZIP file not found: {zip_path}")

    if zip_path.stat().st_size == 0:
        raise ZipReadError(f"Empty ZIP file: {zip_path}")

    zf: zipfile.ZipFile | None = None
    try:
        zf = zipfile.ZipFile(zip_path, "r")
        bad = zf.testzip()
        if bad is not None:
            raise ZipReadError(f"Corrupted ZIP member: {bad}")

        csv_name = _select_csv_member(zf)
        with zf.open(csv_name) as raw:
            text_stream = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            yield csv.reader(text_stream)
    except zipfile.BadZipFile as exc:
        raise ZipReadError(f"Corrupted ZIP file: {zip_path}") from exc
    finally:
        if zf is not None:
            zf.close()


def extract_csv_from_zip(zip_path: Path) -> tuple[str, bytes]:
    """
    Extract the single CSV file from a monthly kline ZIP archive in memory.

    Returns (csv_filename, csv_bytes). Raises ZipReadError on failure.
    Prefer open_csv_reader() for large files.
    """
    if not zip_path.exists():
        raise ZipReadError(f"ZIP file not found: {zip_path}")

    if zip_path.stat().st_size == 0:
        raise ZipReadError(f"Empty ZIP file: {zip_path}")

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            csv_name = _select_csv_member(zf)
            csv_bytes = zf.read(csv_name)
    except zipfile.BadZipFile as exc:
        raise ZipReadError(f"Corrupted ZIP file: {zip_path}") from exc

    if not csv_bytes.strip():
        raise ZipReadError(f"Empty CSV in ZIP: {zip_path}")

    return csv_name, csv_bytes


def validate_zip_integrity(zip_path: Path) -> bool:
    """Quick ZIP integrity check without full extraction."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            bad = zf.testzip()
            return bad is None
    except zipfile.BadZipFile:
        return False
