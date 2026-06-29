"""SHA256 checksum verification for downloaded files."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

CHECKSUM_PATTERN = re.compile(
    r"^([a-fA-F0-9]{64})\s+(.+)$",
    re.MULTILINE,
)


def parse_checksum_file(content: str) -> dict[str, str]:
    """
    Parse Binance CHECKSUM file content.

    Format: SHA256 hash followed by filename.
    Returns mapping of filename -> lowercase hex digest.
    """
    result: dict[str, str] = {}
    for match in CHECKSUM_PATTERN.finditer(content.strip()):
        digest, filename = match.group(1).lower(), match.group(2).strip()
        result[filename] = digest
    return result


def compute_file_sha256(path: Path, chunk_size: int = 1_048_576) -> str:
    """Compute SHA256 hex digest of a file using streaming reads."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file_checksum(path: Path, expected_digest: str, chunk_size: int = 1_048_576) -> bool:
    """Return True if file digest matches expected SHA256."""
    actual = compute_file_sha256(path, chunk_size=chunk_size)
    return actual.lower() == expected_digest.lower()
