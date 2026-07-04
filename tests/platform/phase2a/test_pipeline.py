"""Phase 2A pipeline plugin tests."""

from __future__ import annotations

import pytest

from quant_platform.bootstrap import bootstrap_pipeline, get_data_provider, get_storage_backend
from quant_platform.plugins.binance_vision import BinanceVisionDataProvider
from quant_platform.plugins.clickhouse import ClickHouseStorageBackend
from quant_platform.runtime import PipelineRuntime
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
        runtime = bootstrap_pipeline(config)
        assert isinstance(runtime, PipelineRuntime)
        provider = runtime.data_provider
        assert isinstance(provider, BinanceVisionDataProvider)

    def test_storage_backend_plugin(self):
        config = _test_config()
        runtime = bootstrap_pipeline(config)
        storage = runtime.storage_backend
        assert isinstance(storage, ClickHouseStorageBackend)

    def test_provider_creates_worker(self):
        config = _test_config()
        runtime = bootstrap_pipeline(config)
        worker = runtime.data_provider.create_worker()
        assert worker is not None

    def test_legacy_get_helpers(self):
        config = _test_config()
        runtime = bootstrap_pipeline(config)
        provider = get_data_provider(runtime.manager, config)
        storage = get_storage_backend(runtime.manager, config)
        assert isinstance(provider, BinanceVisionDataProvider)
        assert isinstance(storage, ClickHouseStorageBackend)


class TestBackwardCompat:
    def test_config_without_plugins_section(self):
        config = AppConfig(symbols=["ETHUSDT"], timeframes=["1m"])
        runtime = bootstrap_pipeline(config)
        assert runtime.manager is not None
