"""Domain models for kline data and download tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Status of a download or import task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class MonthlyFile:
    """Represents a monthly ZIP file on Binance Vision."""

    symbol: str
    timeframe: str
    year: int
    month: int
    filename: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "filename",
            f"{self.symbol}-{self.timeframe}-{self.year:04d}-{self.month:02d}.zip",
        )

    @property
    def checksum_filename(self) -> str:
        return f"{self.filename}.CHECKSUM"

    def sort_key(self) -> tuple[int, int]:
        """Sort oldest month first."""
        return (self.year, self.month)


@dataclass(frozen=True, slots=True)
class KlineRow:
    """Validated kline candle row ready for database insertion."""

    symbol: str
    timeframe: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: datetime
    quote_volume: float
    trade_count: int
    taker_buy_volume: float
    taker_buy_quote_volume: float

    def as_tuple(self) -> tuple:
        """Convert to tuple for ClickHouse batch insert."""
        return (
            self.symbol,
            self.timeframe,
            self.open_time,
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
            self.close_time,
            self.quote_volume,
            self.trade_count,
            self.taker_buy_volume,
            self.taker_buy_quote_volume,
        )


@dataclass
class ValidationResult:
    """Result of CSV/kline validation."""

    valid_rows: list[KlineRow] = field(default_factory=list)
    duplicate_count: int = 0
    invalid_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def row_count(self) -> int:
        return len(self.valid_rows)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors) or self.invalid_count > 0


@dataclass
class DownloadStats:
    """Downloader run statistics."""

    total_files: int = 0
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    bytes_downloaded: int = 0

    def log_summary(self, logger) -> None:
        logger.info(
            "download_statistics",
            statistics=True,
            total_files=self.total_files,
            downloaded=self.downloaded,
            skipped=self.skipped,
            failed=self.failed,
            bytes_downloaded=self.bytes_downloaded,
        )


@dataclass
class ImportStats:
    """Importer run statistics."""

    total_files: int = 0
    imported: int = 0
    skipped: int = 0
    failed: int = 0
    rows_inserted: int = 0

    def log_summary(self, logger) -> None:
        logger.info(
            "import_statistics",
            statistics=True,
            total_files=self.total_files,
            imported=self.imported,
            skipped=self.skipped,
            failed=self.failed,
            rows_inserted=self.rows_inserted,
        )
