"""Phase 2A pipeline plugin tests."""

from __future__ import annotations

import pytest

from quant_platform.bootstrap import bootstrap_pipeline, get_data_provider, get_storage_backend
from quant_platform.plugins.binance_vision import BinanceVisionDataProvider
from quant_platform.plugins.clickhouse import ClickHouseStorageBackend
from services.shared.config import AppConfig, BinanceConfig, PathsConfig


def _test_config() -> AppConfig:
    return AppConfig(
        symbols=["BTCUSDT"],
        timeframes=["1h"],
        paths=PathsConfig(download_dir="./downloads", logs_dir="./logs", state_dir="./downloads/.state"),
    )


class TestPipelinePlugins:
    def test_bootstrap_registers_plugins(self):
        config = _test_config()
        manager = bootstrap_pipeline(config)
        provider = get_data_provider(manager, config)
        assert isinstance(provider, BinanceVisionDataProvider)

    def test_storage_backend_plugin(self):
        config = _test_config()
        manager = bootstrap_pipeline(config)
        storage = get_storage_backend(manager, config)
        assert isinstance(storage, ClickHouseStorageBackend)

    def test_provider_creates_worker(self):
        config = _test_config()
        manager = bootstrap_pipeline(config)
        provider = get_data_provider(manager, config)
        worker = provider.create_worker()
        assert worker is not None


class TestBackwardCompat:
    def test_config_without_plugins_section(self):
        config = AppConfig(symbols=["ETHUSDT"], timeframes=["1m"])
        assert config.plugins is None
        manager = bootstrap_pipeline(config)
        assert manager is not None
