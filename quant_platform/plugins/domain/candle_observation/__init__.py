"""Candle observation plugin (Phase 8)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.observations.candle import build_candle_observation
from quant_platform.observations.source import resolve_observation_bars

PLUGIN_METADATA = PluginMetadata(
    name="candle_observation",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Normalized OHLC window observation for RL agents",
    input_types=["klines", "ohlc"],
    output_types=["candle_observation"],
    registry_group="platform.observations",
)


class CandleObservation:
    def __init__(self, window: int = 10) -> None:
        self._window = window

    def build(self, ctx: PipelineContext) -> dict[str, Any]:
        bars = resolve_observation_bars(ctx)
        observation = build_candle_observation(bars, window=self._window)
        ctx.emit(
            DataEnvelope(
                type_key="candle_observation",
                payload=observation,
                metadata={"window": self._window},
            )
        )
        return observation


def factory(*, window: int = 10, config: dict | None = None, **kwargs) -> CandleObservation:
    if config and "window" in config:
        window = int(config["window"])
    return CandleObservation(window=window)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
