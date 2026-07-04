"""Downloader dependency interfaces for testability and plugin adapters."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from services.downloader.discovery import (
    build_checksum_url,
    build_download_url,
    local_zip_path,
)
from services.shared.models import MonthlyFile

if TYPE_CHECKING:
    from services.shared.config import AppConfig


class DownloadPathResolver(Protocol):
    """Resolve download URLs and local paths for a monthly file."""

    def download_url(self, config: AppConfig, monthly_file: MonthlyFile) -> str: ...
    def checksum_url(self, config: AppConfig, monthly_file: MonthlyFile) -> str: ...
    def local_path(self, config: AppConfig, monthly_file: MonthlyFile) -> Path: ...


class BinanceDownloadPaths:
    """Default path resolver delegating to Binance Vision discovery helpers."""

    def download_url(self, config: AppConfig, monthly_file: MonthlyFile) -> str:
        return build_download_url(config, monthly_file)

    def checksum_url(self, config: AppConfig, monthly_file: MonthlyFile) -> str:
        return build_checksum_url(config, monthly_file)

    def local_path(self, config: AppConfig, monthly_file: MonthlyFile) -> Path:
        return Path(local_zip_path(config, monthly_file))
