"""Tests for G1 service refactor seams."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.database.batch import klines_to_tuples
from services.downloader.ports import BinanceDownloadPaths
from services.downloader.worker import DownloadWorker
from services.importer.csv_parser import DefaultKlineCsvParser, parse_csv_bytes
from services.importer.ports import KlineStorage, StoragePool
from services.importer.worker import ImportWorker
from services.shared.config import AppConfig, BinanceConfig, PathsConfig
from services.shared.models import KlineRow, MonthlyFile


def _config() -> AppConfig:
    return AppConfig(
        symbols=["BTCUSDT"],
        timeframes=["1h"],
        binance=BinanceConfig(),
        paths=PathsConfig(download_dir="/downloads", logs_dir="/logs", state_dir="/downloads/.state"),
    )


class TestDownloadPathResolver:
    def test_injected_resolver_used(self) -> None:
        config = _config()
        monthly = MonthlyFile(symbol="BTCUSDT", timeframe="1h", year=2020, month=1)
        resolver = MagicMock()
        resolver.local_path.return_value = Path("/tmp/custom.zip")
        resolver.download_url.return_value = "https://example.test/file.zip"
        resolver.checksum_url.return_value = "https://example.test/file.zip.CHECKSUM"

        worker = DownloadWorker(config, path_resolver=resolver)
        assert worker._paths is resolver

        assert worker._paths.local_path(config, monthly) == Path("/tmp/custom.zip")
        resolver.local_path.assert_called_once_with(config, monthly)

    def test_default_binance_paths(self) -> None:
        config = _config()
        monthly = MonthlyFile(symbol="BTCUSDT", timeframe="1h", year=2020, month=1)
        paths = BinanceDownloadPaths()
        url = paths.download_url(config, monthly)
        assert "BTCUSDT" in url and monthly.filename in url


class TestStoragePoolProtocol:
    def test_import_worker_accepts_storage_pool(self) -> None:
        config = _config()
        storage = MagicMock(spec=KlineStorage)
        storage.is_file_imported.return_value = True
        pool = MagicMock(spec=StoragePool)
        pool.get.return_value = storage

        worker = ImportWorker(config, pool)
        zip_path = Path("/downloads/BTCUSDT/1h/BTCUSDT-1h-2020-01.zip")
        worker._import_file(zip_path, storage)

        storage.is_file_imported.assert_called_once()


class TestKlinesBatchHelper:
    def test_klines_to_tuples_pure(self) -> None:
        t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        t1 = datetime(2024, 1, 1, 1, tzinfo=timezone.utc)
        row = KlineRow(
            symbol="BTCUSDT",
            timeframe="1h",
            open_time=t0,
            open=1.0,
            high=2.0,
            low=0.5,
            close=1.5,
            volume=100.0,
            close_time=t1,
            quote_volume=150.0,
            trade_count=10,
            taker_buy_volume=50.0,
            taker_buy_quote_volume=75.0,
        )
        tuples = klines_to_tuples([row])
        assert tuples == [row.as_tuple()]
        assert klines_to_tuples([]) == []


class TestCsvParser:
    def test_default_parser_is_stateless(self) -> None:
        parser = DefaultKlineCsvParser()
        csv_line = (
            "1609459200000,29000.0,29050.0,28900.0,29025.0,100.0,"
            "1609462799999,2900000.0,500,50.0,1450000.0,0,0,0,0,0,0,0,0\n"
        )
        r1 = parser.parse_stream(csv_line.encode(), symbol="BTCUSDT", timeframe="1h")
        r2 = parse_csv_bytes(csv_line.encode(), symbol="BTCUSDT", timeframe="1h")
        assert r1.row_count == r2.row_count == 1
