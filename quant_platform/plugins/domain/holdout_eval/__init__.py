"""Holdout evaluation plugin (Phase 16)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.evaluation_pipelines.holdout import evaluate_holdout

PLUGIN_METADATA = PluginMetadata(
    name="holdout_eval",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Single train/test holdout evaluation over return or price series",
    input_types=["model", "returns", "series"],
    output_types=["evaluation_results"],
    registry_group="platform.evaluation_pipelines",
)


class HoldoutEval:
    def __init__(self, *, train_ratio: float = 0.8) -> None:
        self._train_ratio = train_ratio

    def evaluate(self, model: Any, data: Any) -> dict[str, Any]:
        return evaluate_holdout(model, data, train_ratio=self._train_ratio)


def factory(
    *,
    train_ratio: float = 0.8,
    config: dict | None = None,
    **kwargs,
) -> HoldoutEval:
    if config and "train_ratio" in config:
        train_ratio = float(config["train_ratio"])
    return HoldoutEval(train_ratio=train_ratio)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
