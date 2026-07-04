"""Binance monthly klines dataset builder plugin."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from quant_platform.core.plugin import PluginDependency, PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="binance_klines_monthly",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    author="crypto-pipeline",
    description="Monthly klines dataset builder composing provider + parser + storage",
    dependencies=[
        PluginDependency(name="binance_vision", version="*"),
        PluginDependency(name="clickhouse", version="*"),
        PluginDependency(name="binance_kline_csv", version="*"),
    ],
    registry_group="platform.dataset_builders",
)


@dataclass
class DatasetPipeline:
    data_provider: Any
    storage: Any
    parser: Any


class BinanceKlinesMonthlyBuilder:
    def __init__(
        self,
        data_provider: Any,
        storage: Any,
        parser: Any,
    ) -> None:
        self._provider = data_provider
        self._storage = storage
        self._parser = parser

    def build(self, config: dict[str, Any] | None = None) -> DatasetPipeline:
        return DatasetPipeline(
            data_provider=self._provider,
            storage=self._storage,
            parser=self._parser,
        )


def factory(
    *,
    config: Any = None,
    data_provider: Any = None,
    storage: Any = None,
    parser: Any = None,
) -> BinanceKlinesMonthlyBuilder:
    return BinanceKlinesMonthlyBuilder(data_provider, storage, parser)
