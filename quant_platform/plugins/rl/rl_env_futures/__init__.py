"""Futures RL environment plugin (G33)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.env.bridge import RLEnvironmentBridge
from quant_platform.rl_product.env.execution import SimpleExecutionModel
from quant_platform.rl_product.graph import RLProductGraph
from quant_platform.rl_product.protocols import Episode
from quant_platform.rl_product.registry import RL_GROUP

PLUGIN_METADATA = PluginMetadata(
    name="rl_env_futures",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="RL environment bridge for futures market with price-action observations",
    input_types=["episode", "training_config"],
    output_types=["rl_env"],
    registry_group=RL_GROUP,
)


class RlEnvFuturesPlugin:
    def __init__(self, graph: RLProductGraph | None = None) -> None:
        self._graph = graph

    def create(
        self,
        episode: Episode,
        *,
        config: dict | None = None,
        initial_equity: float = 10_000.0,
        leverage: float = 5.0,
        execution: SimpleExecutionModel | None = None,
    ) -> RLEnvironmentBridge:
        cfg = config or {}
        graph = self._graph or RLProductGraph.compile(cfg)
        training = cfg.get("training", cfg)
        equity = float(training.get("initial_equity", initial_equity))
        lev = float(training.get("leverage", leverage))
        return RLEnvironmentBridge(
            episode,
            graph,
            execution=execution or SimpleExecutionModel(),
            market="futures",
            initial_equity=equity,
            leverage=lev,
            config=cfg,
        )


def factory(*, config: dict | None = None, **kwargs) -> RlEnvFuturesPlugin:
    graph = RLProductGraph.compile(config) if config else None
    return RlEnvFuturesPlugin(graph=graph)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
