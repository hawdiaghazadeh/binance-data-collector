"""Binance Vision data provider plugin."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quant_platform.core.plugin import PluginLifecycle, PluginMetadata
from quant_platform.version import PLATFORM_VERSION
from services.downloader.discovery import (
    build_download_url,
    discover_monthly_files,
)
from services.downloader.worker import DownloadWorker

if TYPE_CHECKING:
    from services.shared.config import AppConfig

PLUGIN_METADATA = PluginMetadata(
    name="binance_vision",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    author="crypto-pipeline",
    description="Binance Vision historical data provider",
    supported_markets=["crypto"],
    lifecycle=PluginLifecycle.SINGLETON,
    registry_group="platform.data_providers",
)


class BinanceVisionDataProvider:
    def __init__(self, config: AppConfig | None = None) -> None:
        if config is None:
            from services.shared.config import load_config

            config = load_config()
        self._config = config

    def create_worker(self) -> DownloadWorker:
        return DownloadWorker(self._config)

    async def discover_files(self, client: Any, symbol: str, timeframe: str) -> list[Any]:
        return await discover_monthly_files(client, self._config, symbol, timeframe)

    def build_download_url(self, file_info: Any) -> str:
        return build_download_url(self._config, file_info)

    @property
    def config(self) -> AppConfig:
        return self._config


def factory(*, config: Any = None) -> BinanceVisionDataProvider:
    return BinanceVisionDataProvider(config=config)
