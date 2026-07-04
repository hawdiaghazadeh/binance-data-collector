"""Futures environment plugin (Phase 11)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.environments.futures import FuturesEnvironmentEngine
from quant_platform.environments.source import resolve_prices

PLUGIN_METADATA = PluginMetadata(
    name="futures_env",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Gym-like leveraged futures environment over kline close prices",
    input_types=["klines"],
    output_types=["observation", "reward"],
    registry_group="platform.environments",
)


class FuturesEnvironment:
    def __init__(self, engine: FuturesEnvironmentEngine) -> None:
        self._engine = engine

    def reset(self) -> dict[str, Any]:
        return self._engine.reset()

    def step(self, action: Any) -> tuple[dict[str, Any], float, bool, dict[str, Any]]:
        return self._engine.step(action)


def factory(*, config: dict | None = None, **kwargs) -> FuturesEnvironment:
    cfg = dict(config or {})
    prices = resolve_prices(cfg.get("context"), cfg.get("prices"))
    engine = FuturesEnvironmentEngine(
        prices,
        initial_margin=float(cfg.get("initial_margin", 10_000.0)),
        leverage=float(cfg.get("leverage", 5.0)),
        fee_rate=float(cfg.get("fee_rate", 0.0005)),
        maintenance_margin_ratio=float(cfg.get("maintenance_margin_ratio", 0.05)),
    )
    return FuturesEnvironment(engine)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
