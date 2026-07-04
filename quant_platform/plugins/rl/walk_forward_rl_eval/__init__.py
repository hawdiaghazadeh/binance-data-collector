"""Walk-forward RL evaluation plugin (G36)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.evaluation.walk_forward import WalkForwardRLEvaluator
from quant_platform.rl_product.registry import RL_GROUP


PLUGIN_METADATA = PluginMetadata(
    name="walk_forward_rl_eval",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Walk-forward RL evaluation with OOS Sharpe, max drawdown, and win rate",
    input_types=["training_config", "episodes"],
    output_types=["evaluation_results"],
    registry_group=RL_GROUP,
)


class WalkForwardRLEvalPlugin:
    def __init__(self, evaluator: WalkForwardRLEvaluator | None = None) -> None:
        self._evaluator = evaluator or WalkForwardRLEvaluator()

    def evaluate(self, config: dict[str, Any], episodes: list) -> dict[str, Any]:
        return self._evaluator.evaluate(config, episodes)


def factory(**kwargs) -> WalkForwardRLEvalPlugin:
    return WalkForwardRLEvalPlugin()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
