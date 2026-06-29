"""Discover available monthly ZIP files from Binance Vision S3 listings."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx
import structlog

from services.shared.models import MonthlyFile

if TYPE_CHECKING:
    from services.shared.config import AppConfig

logger = structlog.get_logger("downloader.discovery")

S3_NS = "http://s3.amazonaws.com/doc/2006-03-01/"

MONTHLY_FILE_PATTERN = re.compile(
    r"^([A-Z0-9]+)-([\w]+)-(\d{4})-(\d{2})\.zip$",
    re.IGNORECASE,
)


def _parse_s3_listing(xml_text: str) -> tuple[list[str], bool, str | None]:
    """
    Parse S3 ListBucketResult XML.

    Returns (object_keys, is_truncated, next_marker).
    """
    root = ET.fromstring(xml_text)
    keys: list[str] = []

    for contents in root.findall(f"{{{S3_NS}}}Contents"):
        key_el = contents.find(f"{{{S3_NS}}}Key")
        if key_el is not None and key_el.text:
            keys.append(key_el.text)

    truncated_el = root.find(f"{{{S3_NS}}}IsTruncated")
    is_truncated = truncated_el is not None and truncated_el.text == "true"

    next_marker: str | None = None
    for tag in ("NextMarker", "NextContinuationToken"):
        el = root.find(f"{{{S3_NS}}}{tag}")
        if el is not None and el.text:
            next_marker = el.text
            break

    if is_truncated and next_marker is None and keys:
        next_marker = keys[-1]

    return keys, is_truncated, next_marker


def _keys_to_monthly_files(
    keys: list[str],
    symbol: str,
    timeframe: str,
) -> list[MonthlyFile]:
    """Convert S3 object keys to MonthlyFile instances (ZIP files only)."""
    files: list[MonthlyFile] = []
    seen: set[str] = set()

    for key in keys:
        filename = key.rstrip("/").split("/")[-1]
        if not filename.endswith(".zip") or filename.endswith(".zip.CHECKSUM"):
            continue

        match = MONTHLY_FILE_PATTERN.match(filename)
        if not match:
            continue

        link_symbol, link_tf, year_str, month_str = match.groups()
        if link_symbol.upper() != symbol.upper() or link_tf != timeframe:
            continue

        if filename in seen:
            continue
        seen.add(filename)

        files.append(
            MonthlyFile(
                symbol=symbol.upper(),
                timeframe=timeframe,
                year=int(year_str),
                month=int(month_str),
            )
        )

    return files


async def discover_monthly_files(
    client: httpx.AsyncClient,
    config: AppConfig,
    symbol: str,
    timeframe: str,
) -> list[MonthlyFile]:
    """
    Fetch Binance Vision S3 listing and parse available monthly ZIP files.

    Binance Vision serves directory listings via JavaScript on the website,
    but the underlying S3 bucket exposes an XML ListObjects API that we query
    directly.

    Returns files sorted oldest month first.
    """
    prefix = f"data/futures/um/monthly/klines/{symbol}/{timeframe}/"
    all_keys: list[str] = []
    marker: str | None = None

    while True:
        params: dict[str, str] = {
            "prefix": prefix,
            "delimiter": "/",
            "max-keys": "1000",
        }
        if marker:
            params["marker"] = marker

        url = f"{config.binance.s3_listing_url}?{urlencode(params)}"
        logger.debug("discovering_files", symbol=symbol, timeframe=timeframe, url=url)

        response = await client.get(url)
        response.raise_for_status()

        keys, is_truncated, next_marker = _parse_s3_listing(response.text)
        all_keys.extend(keys)

        if not is_truncated or not next_marker:
            break
        marker = next_marker

    files = _keys_to_monthly_files(all_keys, symbol, timeframe)
    files.sort(key=lambda f: f.sort_key())

    logger.info(
        "files_discovered",
        symbol=symbol,
        timeframe=timeframe,
        count=len(files),
    )
    return files


def build_download_url(config: AppConfig, monthly_file: MonthlyFile) -> str:
    """Build full URL for a monthly ZIP file."""
    return (
        f"{config.binance.base_url}/{monthly_file.symbol}/"
        f"{monthly_file.timeframe}/{monthly_file.filename}"
    )


def build_checksum_url(config: AppConfig, monthly_file: MonthlyFile) -> str:
    """Build full URL for a monthly CHECKSUM file."""
    return (
        f"{config.binance.base_url}/{monthly_file.symbol}/"
        f"{monthly_file.timeframe}/{monthly_file.checksum_filename}"
    )


def local_zip_path(config: AppConfig, monthly_file: MonthlyFile) -> str:
    """Return local filesystem path for a downloaded ZIP."""
    return str(
        config.paths.download_path
        / monthly_file.symbol
        / monthly_file.timeframe
        / monthly_file.filename
    )
