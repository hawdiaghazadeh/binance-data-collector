"""SMC/ICT strategy plugin (Phase 12)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.strategies.smc import evaluate_smc_signals
from quant_platform.strategies.source import current_bar_index

PLUGIN_METADATA = PluginMetadata(
    name="smc_ict",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="SMC/ICT skeleton strategy from BOS, FVG, and order block context",
    input_types=["market_structure", "fvg", "order_blocks"],
    output_types=["strategy_signals"],
    registry_group="platform.strategies",
)


class SmcIctStrategy:
    def __init__(self, lookback: int = 1) -> None:
        self._lookback = lookback
        self._last_signals: list[dict[str, Any]] = []

    def on_bar(self, ctx: PipelineContext) -> None:
        self._last_signals = self._evaluate(ctx)
        ctx.emit(DataEnvelope(type_key="strategy_signals", payload=self._last_signals))

    def signals(self, ctx: PipelineContext) -> list[Any]:
        if self._last_signals:
            return list(self._last_signals)
        return self._evaluate(ctx)

    def _evaluate(self, ctx: PipelineContext) -> list[dict[str, Any]]:
        structure_env = ctx.optional("market_structure")
        fvg_env = ctx.optional("fvg")
        order_blocks_env = ctx.optional("order_blocks")
        return evaluate_smc_signals(
            market_structure=structure_env.payload if structure_env is not None else None,
            fvg=fvg_env.payload if fvg_env is not None else None,
            order_blocks=order_blocks_env.payload if order_blocks_env is not None else None,
            current_index=current_bar_index(ctx),
            lookback=self._lookback,
        )


def factory(*, lookback: int = 1, config: dict | None = None, **kwargs) -> SmcIctStrategy:
    if config and "lookback" in config:
        lookback = int(config["lookback"])
    return SmcIctStrategy(lookback=lookback)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
