"""In-memory ZIP extraction — no permanent CSV files on disk."""

from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path

import structlog

logger = structlog.get_logger("importer.zip_reader")


class ZipReadError(Exception):
    """Raised when a ZIP file cannot be read or is corrupted."""


def extract_csv_from_zip(zip_path: Path) -> tuple[str, bytes]:
    """
    Extract the single CSV file from a monthly kline ZIP archive in memory.

    Returns (csv_filename, csv_bytes). Raises ZipReadError on failure.
    """
    if not zip_path.exists():
        raise ZipReadError(f"ZIP file not found: {zip_path}")

    if zip_path.stat().st_size == 0:
        raise ZipReadError(f"Empty ZIP file: {zip_path}")

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            csv_members = [m for m in zf.namelist() if m.lower().endswith(".csv")]
            if not csv_members:
                raise ZipReadError(f"No CSV found in ZIP: {zip_path}")
            if len(csv_members) > 1:
                logger.warning(
                    "multiple_csv_in_zip",
                    zip_path=str(zip_path),
                    count=len(csv_members),
                )
            csv_name = csv_members[0]
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
