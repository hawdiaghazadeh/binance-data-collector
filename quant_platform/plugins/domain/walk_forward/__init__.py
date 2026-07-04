"""Walk-forward evaluation plugin (Phase 16)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.evaluation_pipelines.walk_forward import evaluate_walk_forward

PLUGIN_METADATA = PluginMetadata(
    name="walk_forward",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Walk-forward cross-validation over return or price series",
    input_types=["model", "returns", "series"],
    output_types=["evaluation_results"],
    registry_group="platform.evaluation_pipelines",
)


class WalkForwardEval:
    def __init__(
        self,
        *,
        train_size: int = 20,
        test_size: int = 5,
        step: int | None = None,
    ) -> None:
        self._train_size = train_size
        self._test_size = test_size
        self._step = step

    def evaluate(self, model: Any, data: Any) -> dict[str, Any]:
        return evaluate_walk_forward(
            model,
            data,
            train_size=self._train_size,
            test_size=self._test_size,
            step=self._step,
        )


def factory(
    *,
    train_size: int = 20,
    test_size: int = 5,
    step: int | None = None,
    config: dict | None = None,
    **kwargs,
) -> WalkForwardEval:
    if config:
        train_size = int(config.get("train_size", train_size))
        test_size = int(config.get("test_size", test_size))
        if "step" in config:
            step = int(config["step"])
    return WalkForwardEval(train_size=train_size, test_size=test_size, step=step)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
