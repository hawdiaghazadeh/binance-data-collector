"""Ablation and leakage evaluation plugin (G36)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.evaluation.ablation import AblationRunner, LeakageChecker, LeakageConfig
from quant_platform.rl_product.registry import RL_GROUP


PLUGIN_METADATA = PluginMetadata(
    name="ablation_eval",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Ablation A/B/C runner with mandatory context leakage checks",
    input_types=["training_config", "episodes"],
    output_types=["ablation_results", "leakage_results"],
    registry_group=RL_GROUP,
)


class AblationEvalPlugin:
    def __init__(self, runner: AblationRunner | None = None) -> None:
        self._runner = runner or AblationRunner()

    def run(self, config: dict[str, Any], episodes: list) -> dict[str, Any]:
        return self._runner.run(config, episodes)

    def check_leakage(
        self,
        *,
        price_only: dict[str, float],
        full_context: dict[str, float],
        context_only: dict[str, float],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from quant_platform.rl_product.evaluation.ablation import _metrics_from_variant

        checker = LeakageChecker(LeakageConfig.from_config(config or {}))
        return checker.check(
            price_only=_metrics_from_variant(price_only),
            full_context=_metrics_from_variant(full_context),
            context_only=_metrics_from_variant(context_only),
        )


def factory(**kwargs) -> AblationEvalPlugin:
    return AblationEvalPlugin()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
