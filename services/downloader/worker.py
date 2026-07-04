"""Async download worker with retry, checksum verification, and resume support."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import structlog

from services.downloader.ports import BinanceDownloadPaths, DownloadPathResolver
from services.shared.checksum import parse_checksum_file, verify_file_checksum
from services.shared.models import DownloadStats, MonthlyFile

if TYPE_CHECKING:
    from services.shared.config import AppConfig

logger = structlog.get_logger("downloader.worker")


class DownloadWorker:
    """
    Concurrent async downloader for Binance Vision monthly kline ZIP files.

    Supports resumable downloads, checksum verification, and exponential backoff retries.
    """

    def __init__(
        self,
        config: AppConfig,
        *,
        path_resolver: DownloadPathResolver | None = None,
    ) -> None:
        self._config = config
        self._paths = path_resolver or BinanceDownloadPaths()
        self._semaphore = asyncio.Semaphore(config.downloader.max_concurrent)
        self._stats = DownloadStats()
        self._shutdown = False

    @property
    def stats(self) -> DownloadStats:
        return self._stats

    @property
    def is_shutdown(self) -> bool:
        return self._shutdown

    def request_shutdown(self) -> None:
        """Signal graceful shutdown."""
        self._shutdown = True
        logger.info("shutdown_requested")

    async def download_all(
        self,
        client: httpx.AsyncClient,
        files: list[MonthlyFile],
    ) -> DownloadStats:
        """Download all files concurrently with progress tracking."""
        self._stats.total_files = len(files)

        tasks = [self._download_with_semaphore(client, f) for f in files]
        await asyncio.gather(*tasks, return_exceptions=True)

        return self._stats

    async def _download_with_semaphore(
        self,
        client: httpx.AsyncClient,
        monthly_file: MonthlyFile,
    ) -> None:
        async with self._semaphore:
            if self._shutdown:
                return
            await self.download_file(client, monthly_file)

    async def download_file(
        self,
        client: httpx.AsyncClient,
        monthly_file: MonthlyFile,
    ) -> bool:
        """
        Download a single monthly ZIP file.

        Skips if file exists and passes checksum verification.
        Returns True on success or skip, False on failure.
        """
        dest = self._paths.local_path(self._config, monthly_file)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists() and dest.stat().st_size > 0:
            if await self._verify_existing(client, monthly_file, dest):
                logger.debug("file_skipped", file=monthly_file.filename)
                self._stats.skipped += 1
                return True
            logger.warning("file_exists_invalid_checksum", file=monthly_file.filename)
            dest.unlink(missing_ok=True)

        url = self._paths.download_url(self._config, monthly_file)
        backoff = self._config.downloader.retry_backoff_seconds

        for attempt in range(1, self._config.downloader.retry_count + 2):
            if self._shutdown:
                return False

            try:
                bytes_written = await self._stream_download(client, url, dest)

                if self._config.downloader.verify_checksum:
                    valid = await self._verify_existing(client, monthly_file, dest)
                    if not valid:
                        dest.unlink(missing_ok=True)
                        raise ValueError("Checksum verification failed")

                self._stats.downloaded += 1
                self._stats.bytes_downloaded += bytes_written
                logger.info(
                    "file_downloaded",
                    file=monthly_file.filename,
                    bytes=bytes_written,
                )
                return True

            except Exception as exc:
                dest.unlink(missing_ok=True)
                if attempt > self._config.downloader.retry_count:
                    logger.error(
                        "download_failed",
                        file=monthly_file.filename,
                        error=str(exc),
                        attempts=attempt,
                    )
                    self._stats.failed += 1
                    return False

                logger.warning(
                    "download_retry",
                    file=monthly_file.filename,
                    attempt=attempt,
                    error=str(exc),
                    backoff=backoff,
                )
                await asyncio.sleep(backoff)
                backoff *= self._config.downloader.retry_backoff_multiplier

        return False

    async def _stream_download(
        self,
        client: httpx.AsyncClient,
        url: str,
        dest: Path,
    ) -> int:
        """Stream download to disk in chunks."""
        bytes_written = 0
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with dest.open("wb") as fh:
                async for chunk in response.aiter_bytes(
                    chunk_size=self._config.downloader.chunk_size_bytes
                ):
                    fh.write(chunk)
                    bytes_written += len(chunk)
        return bytes_written

    async def _verify_existing(
        self,
        client: httpx.AsyncClient,
        monthly_file: MonthlyFile,
        dest: Path,
    ) -> bool:
        """Verify file checksum if CHECKSUM file is available on Binance Vision."""
        if not self._config.downloader.verify_checksum:
            return True

        checksum_url = self._paths.checksum_url(self._config, monthly_file)
        try:
            response = await client.get(checksum_url)
            if response.status_code == 404:
                return True
            response.raise_for_status()
        except httpx.HTTPError:
            return True

        checksums = parse_checksum_file(response.text)
        expected = checksums.get(monthly_file.filename)
        if expected is None:
            return True

        return verify_file_checksum(
            dest,
            expected,
            chunk_size=self._config.downloader.chunk_size_bytes,
        )

    async def fetch_checksum(
        self,
        client: httpx.AsyncClient,
        monthly_file: MonthlyFile,
    ) -> str | None:
        """Fetch expected SHA256 digest for a file, if available."""
        checksum_url = self._paths.checksum_url(self._config, monthly_file)
        try:
            response = await client.get(checksum_url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            checksums = parse_checksum_file(response.text)
            return checksums.get(monthly_file.filename)
        except httpx.HTTPError:
            return None
