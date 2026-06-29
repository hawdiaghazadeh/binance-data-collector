"""Concurrent import worker with batch inserts and resume support."""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from services.database.client import ClickHouseClient
from services.importer.csv_parser import parse_zip_klines
from services.shared.models import ImportStats
from services.shared.validation import iter_batches

if TYPE_CHECKING:
    from services.shared.config import AppConfig

logger = structlog.get_logger("importer.worker")

ZIP_FILENAME_PATTERN = re.compile(
    r"^([A-Z0-9]+)-([\w]+)-(\d{4})-(\d{2})\.zip$",
    re.IGNORECASE,
)


class ImportWorker:
    """
    Multi-threaded importer that reads ZIP files and batch-inserts into ClickHouse.

    Skips already-imported files, validates data, and supports graceful shutdown.
    """

    def __init__(self, config: AppConfig, db: ClickHouseClient) -> None:
        self._config = config
        self._db = db
        self._stats = ImportStats()
        self._shutdown = False

    @property
    def stats(self) -> ImportStats:
        return self._stats

    def request_shutdown(self) -> None:
        self._shutdown = True
        logger.info("shutdown_requested")

    def discover_local_zips(self) -> list[Path]:
        """Find all monthly ZIP files in the download directory."""
        download_dir = self._config.paths.download_path
        zips: list[Path] = []

        for symbol in self._config.symbols:
            symbol_dir = download_dir / symbol
            if not symbol_dir.exists():
                continue
            for timeframe in self._config.timeframes:
                tf_dir = symbol_dir / timeframe
                if not tf_dir.exists():
                    continue
                for zip_path in sorted(tf_dir.glob("*.zip")):
                    if ZIP_FILENAME_PATTERN.match(zip_path.name):
                        zips.append(zip_path)

        zips.sort(key=lambda p: p.name)
        return zips

    def run(self) -> ImportStats:
        """Execute import pipeline with thread pool."""
        zip_files = self.discover_local_zips()
        self._stats.total_files = len(zip_files)

        logger.info("import_started", total_files=len(zip_files))

        with ThreadPoolExecutor(max_workers=self._config.importer.max_workers) as executor:
            futures = {
                executor.submit(self._import_file, zip_path): zip_path
                for zip_path in zip_files
            }

            for future in as_completed(futures):
                if self._shutdown:
                    logger.info("import_interrupted")
                    break
                zip_path = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    logger.error(
                        "import_task_failed",
                        file=str(zip_path),
                        error=str(exc),
                    )
                    self._stats.failed += 1

        return self._stats

    def _import_file(self, zip_path: Path) -> None:
        """Import a single ZIP file with retries."""
        file_key = str(zip_path.relative_to(self._config.paths.download_path))

        if self._db.is_file_imported(file_key):
            logger.debug("file_already_imported", file=file_key)
            self._stats.skipped += 1
            return

        match = ZIP_FILENAME_PATTERN.match(zip_path.name)
        if not match:
            logger.warning("invalid_filename", file=zip_path.name)
            self._stats.failed += 1
            return

        symbol, timeframe, year_str, month_str = match.groups()
        symbol = symbol.upper()
        year, month = int(year_str), int(month_str)

        backoff = self._config.importer.retry_backoff_seconds

        for attempt in range(1, self._config.importer.retry_count + 2):
            if self._shutdown:
                return

            try:
                rows_inserted = self._process_zip(
                    zip_path, symbol, timeframe, year, month, file_key
                )
                self._stats.imported += 1
                self._stats.rows_inserted += rows_inserted
                logger.info(
                    "file_imported",
                    file=file_key,
                    rows=rows_inserted,
                )

                if self._config.importer.delete_after_import:
                    zip_path.unlink(missing_ok=True)
                    logger.debug("zip_deleted", file=file_key)

                return

            except Exception as exc:
                if attempt > self._config.importer.retry_count:
                    logger.error(
                        "import_failed",
                        file=file_key,
                        error=str(exc),
                        attempts=attempt,
                    )
                    self._stats.failed += 1
                    return

                logger.warning(
                    "import_retry",
                    file=file_key,
                    attempt=attempt,
                    error=str(exc),
                    backoff=backoff,
                )
                time.sleep(backoff)
                backoff *= 2

    def _process_zip(
        self,
        zip_path: Path,
        symbol: str,
        timeframe: str,
        year: int,
        month: int,
        file_key: str,
    ) -> int:
        """Parse ZIP and batch insert rows into ClickHouse."""
        result = parse_zip_klines(
            zip_path,
            symbol=symbol,
            timeframe=timeframe,
            validate_gaps=self._config.importer.validate_gaps,
        )

        if result.has_errors:
            for error in result.errors[:10]:
                logger.warning("validation_error", file=file_key, error=error)
            if not result.valid_rows:
                raise ValueError(f"No valid rows in {file_key}")

        if result.duplicate_count:
            logger.warning(
                "duplicates_in_csv",
                file=file_key,
                count=result.duplicate_count,
            )

        for warning in result.warnings[:10]:
            logger.warning("validation_warning", file=file_key, warning=warning)

        total_inserted = 0
        for batch in iter_batches(result.valid_rows, self._config.importer.batch_size):
            total_inserted += self._db.insert_klines(batch)

        self._db.mark_file_imported(
            file_path=file_key,
            symbol=symbol,
            timeframe=timeframe,
            year=year,
            month=month,
            rows_inserted=total_inserted,
        )

        return total_inserted
