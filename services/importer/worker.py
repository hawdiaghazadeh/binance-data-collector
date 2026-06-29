"""Serial import worker with transactional per-file rollback."""

from __future__ import annotations

import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from services.database.client import ClickHouseClient, ClickHouseClientPool
from services.importer.zip_reader import open_csv_reader
from services.shared.models import ImportStats, ValidationResult
from services.shared.validation import iter_kline_batches

if TYPE_CHECKING:
    from services.shared.config import AppConfig

logger = structlog.get_logger("importer.worker")

ZIP_FILENAME_PATTERN = re.compile(
    r"^([A-Z0-9]+)-([\w]+)-(\d{4})-(\d{2})\.zip$",
    re.IGNORECASE,
)


def zip_chronological_key(path: Path) -> tuple[str, str, int, int]:
    """Sort key: symbol → timeframe → year → month (oldest first)."""
    match = ZIP_FILENAME_PATTERN.match(path.name)
    if not match:
        return ("", "", 0, 0)
    symbol, timeframe, year_str, month_str = match.groups()
    return (symbol.upper(), timeframe, int(year_str), int(month_str))


class ImportWorker:
    """
    Importer with strict data integrity guarantees per monthly ZIP file.

    - Files are processed in chronological order (serial by default).
    - Before each file: existing rows for that month are deleted.
    - On any failure: month data is rolled back; import_state is not updated.
    - Only fully successful imports are marked complete.
    """

    def __init__(self, config: AppConfig, db_pool: ClickHouseClientPool) -> None:
        self._config = config
        self._db_pool = db_pool
        self._stats = ImportStats()
        self._stats_lock = threading.Lock()
        self._shutdown = False

    @property
    def stats(self) -> ImportStats:
        return self._stats

    def request_shutdown(self) -> None:
        self._shutdown = True
        logger.info("shutdown_requested")

    def _increment_stat(self, field: str, value: int = 1) -> None:
        with self._stats_lock:
            setattr(self._stats, field, getattr(self._stats, field) + value)

    def discover_local_zips(self) -> list[Path]:
        """Find all monthly ZIP files sorted chronologically."""
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
                for zip_path in tf_dir.glob("*.zip"):
                    if ZIP_FILENAME_PATTERN.match(zip_path.name):
                        zips.append(zip_path)

        zips.sort(key=zip_chronological_key)
        return zips

    def run(self) -> ImportStats:
        """Execute import pipeline in chronological order."""
        zip_files = self.discover_local_zips()
        self._stats.total_files = len(zip_files)

        logger.info(
            "import_started",
            total_files=len(zip_files),
            serial=self._config.importer.serial_import,
        )

        if self._config.importer.serial_import:
            db = self._db_pool.get()
            for zip_path in zip_files:
                if self._shutdown:
                    logger.info("import_interrupted")
                    break
                self._import_file(zip_path, db)
        else:
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
                        self._increment_stat("failed")

        return self._stats

    def _import_file(self, zip_path: Path, db: ClickHouseClient | None = None) -> None:
        """Import a single ZIP file with retries and rollback on failure."""
        client = db or self._db_pool.get()
        file_key = str(zip_path.relative_to(self._config.paths.download_path))

        if client.is_file_imported(file_key):
            logger.debug("file_already_imported", file=file_key)
            self._increment_stat("skipped")
            return

        match = ZIP_FILENAME_PATTERN.match(zip_path.name)
        if not match:
            logger.warning("invalid_filename", file=zip_path.name)
            self._increment_stat("failed")
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
                    client, zip_path, symbol, timeframe, year, month, file_key
                )
                self._increment_stat("imported")
                self._increment_stat("rows_inserted", rows_inserted)
                logger.info("file_imported", file=file_key, rows=rows_inserted)

                if self._config.importer.delete_after_import:
                    zip_path.unlink(missing_ok=True)
                    logger.debug("zip_deleted", file=file_key)

                return

            except Exception as exc:
                if self._config.importer.rollback_on_failure:
                    self._rollback_month(client, symbol, timeframe, year, month, file_key)

                if attempt > self._config.importer.retry_count:
                    logger.error(
                        "import_failed",
                        file=file_key,
                        error=str(exc),
                        attempts=attempt,
                    )
                    self._increment_stat("failed")
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

    def _rollback_month(
        self,
        db: ClickHouseClient,
        symbol: str,
        timeframe: str,
        year: int,
        month: int,
        file_key: str,
    ) -> None:
        """Remove partial data and import state after a failed import."""
        try:
            db.delete_month_klines(symbol, timeframe, year, month)
            db.remove_file_import_state(file_key)
            logger.warning("import_rolled_back", file=file_key)
        except Exception as exc:
            logger.error("rollback_failed", file=file_key, error=str(exc))

    def _process_zip(
        self,
        db: ClickHouseClient,
        zip_path: Path,
        symbol: str,
        timeframe: str,
        year: int,
        month: int,
        file_key: str,
    ) -> int:
        """
        Transactional import: delete month → insert batches → validate → commit state.

        Raises on validation failure; caller performs rollback.
        """
        db.delete_month_klines(symbol, timeframe, year, month)

        total_inserted = 0
        result: ValidationResult | None = None

        try:
            with open_csv_reader(zip_path) as reader:
                batch_iter, result = iter_kline_batches(
                    reader,
                    symbol=symbol,
                    timeframe=timeframe,
                    batch_size=self._config.importer.batch_size,
                    validate_gaps=self._config.importer.validate_gaps,
                )

                for batch in batch_iter:
                    if not batch:
                        continue
                    total_inserted += db.insert_klines(batch)

            assert result is not None
            self._validate_result(result, file_key, total_inserted)

            for warning in result.warnings[:10]:
                logger.warning("validation_warning", file=file_key, warning=warning)

            db.mark_file_imported(
                file_path=file_key,
                symbol=symbol,
                timeframe=timeframe,
                year=year,
                month=month,
                rows_inserted=total_inserted,
            )

            return total_inserted

        except Exception:
            if self._config.importer.rollback_on_failure:
                db.delete_month_klines(symbol, timeframe, year, month)
            raise

    def _validate_result(
        self,
        result: ValidationResult,
        file_key: str,
        total_inserted: int,
    ) -> None:
        """Enforce strict validation — fail import if data is not clean."""
        if total_inserted == 0:
            raise ValueError(f"No valid rows in {file_key}")

        if self._config.importer.strict_validation:
            if result.invalid_count > 0:
                for error in result.errors[:10]:
                    logger.error("validation_error", file=file_key, error=error)
                raise ValueError(
                    f"Strict validation failed: {result.invalid_count} invalid row(s) in {file_key}"
                )

            if result.duplicate_count > 0:
                raise ValueError(
                    f"Strict validation failed: {result.duplicate_count} duplicate row(s) in {file_key}"
                )

        elif result.has_errors:
            for error in result.errors[:10]:
                logger.warning("validation_error", file=file_key, error=error)
