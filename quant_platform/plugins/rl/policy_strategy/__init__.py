"""RL policy strategy plugin — deploy hook (G37)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.registries.domain import STRATEGY_GROUP
from quant_platform.rl_product.inference.policy_inference import PolicyInferenceEngine
from quant_platform.rl_product.inference.strategy import PolicyStrategy
from quant_platform.rl_product.registry import RL_GROUP


PLUGIN_METADATA = PluginMetadata(
    name="policy_strategy",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="RL policy StrategyProtocol — obs → policy → action for backtest/paper/live",
    input_types=["checkpoint_path", "training_config", "klines"],
    output_types=["strategy_signals"],
    registry_group=RL_GROUP,
)

STRATEGY_PLUGIN_METADATA = PluginMetadata(
    name="policy_strategy",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="RL policy StrategyProtocol — obs → policy → action for backtest/paper/live",
    input_types=["checkpoint_path", "training_config", "klines"],
    output_types=["strategy_signals"],
    registry_group=STRATEGY_GROUP,
)


class PolicyStrategyPlugin:
    def __init__(self, strategy: PolicyStrategy | None = None) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> PolicyStrategy | None:
        return self._strategy

    def build(
        self,
        checkpoint_path: str | Path,
        config: dict[str, Any],
        *,
        strict_hash: bool = True,
    ) -> PolicyStrategy:
        engine = PolicyInferenceEngine.from_checkpoint(checkpoint_path, config, strict_hash=strict_hash)
        self._strategy = PolicyStrategy(engine)
        return self._strategy

    def on_bar(self, ctx: PipelineContext) -> None:
        if self._strategy is None:
            raise RuntimeError("policy_strategy not loaded — call build() or pass checkpoint_path to factory")
        self._strategy.on_bar(ctx)

    def signals(self, ctx: PipelineContext) -> list[Any]:
        if self._strategy is None:
            raise RuntimeError("policy_strategy not loaded — call build() or pass checkpoint_path to factory")
        return self._strategy.signals(ctx)


def factory(
    *,
    checkpoint_path: str | Path | None = None,
    config: dict | None = None,
    strict_hash: bool = True,
    **kwargs,
) -> PolicyStrategy | PolicyStrategyPlugin:
    if checkpoint_path is not None and config is not None:
        engine = PolicyInferenceEngine.from_checkpoint(checkpoint_path, config, strict_hash=strict_hash)
        return PolicyStrategy(engine)
    plugin = PolicyStrategyPlugin()
    if checkpoint_path is not None and config is not None:
        plugin.build(checkpoint_path, config, strict_hash=strict_hash)
    return plugin


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
factory.STRATEGY_PLUGIN_METADATA = STRATEGY_PLUGIN_METADATA  # type: ignore[attr-defined]
