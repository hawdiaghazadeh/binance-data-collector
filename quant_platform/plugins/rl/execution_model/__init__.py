"""Execution model plugin — simple fee/spread/slippage MVP (G33)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.env.execution import ExecutionConfig, SimpleExecutionModel
from quant_platform.rl_product.registry import RL_GROUP

PLUGIN_METADATA = PluginMetadata(
    name="execution_model",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="MVP execution model with fee, spread, and slippage",
    input_types=["order", "market_state"],
    output_types=["fill_result"],
    registry_group=RL_GROUP,
)


def factory(*, config: dict | None = None, **kwargs) -> SimpleExecutionModel:
    cfg = ExecutionConfig.from_config(config or {})
    return SimpleExecutionModel(cfg)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
