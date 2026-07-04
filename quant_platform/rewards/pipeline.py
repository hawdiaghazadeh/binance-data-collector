"""Dynamic reward pipeline builder — Phase 9."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import REWARD_GROUP


class RewardPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def calculate(
        self,
        ctx: PipelineContext,
        reward_names: list[str],
        *,
        weights: list[float] | None = None,
    ) -> float:
        if weights is not None and len(weights) != len(reward_names):
            raise ValueError("weights length must match reward_names length")

        total = 0.0
        components: dict[str, float] = {}
        for index, name in enumerate(reward_names):
            reward = self._manager.get(REWARD_GROUP, name)
            value = float(reward.calculate(ctx))
            weight = 1.0 if weights is None else float(weights[index])
            components[name] = value
            total += value * weight

        ctx.emit(
            DataEnvelope(
                type_key="reward",
                payload={"total": total, "components": components},
            )
        )
        return total

    def build_graph(
        self,
        reward_names: list[str],
        *,
        weights: list[float] | None = None,
    ) -> CompiledExecutionGraph:
        names = list(reward_names)
        weight_values = list(weights) if weights is not None else None

        def handler(ctx: PipelineContext) -> None:
            self.calculate(ctx, names, weights=weight_values)

        return CompiledExecutionGraph(
            (
                ExecutionStep(
                    plugin_name="reward_pipeline",
                    handler=handler,
                    registry_group=REWARD_GROUP,
                ),
            )
        )

    def run(
        self,
        ctx: PipelineContext,
        reward_names: list[str],
        *,
        weights: list[float] | None = None,
    ) -> float:
        return self.calculate(ctx, reward_names, weights=weights)


def register_reward_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.drawdown_penalty import PLUGIN_METADATA as DRAWDOWN_META
    from quant_platform.plugins.domain.drawdown_penalty import factory as drawdown_factory
    from quant_platform.plugins.domain.profit_reward import PLUGIN_METADATA as PROFIT_META
    from quant_platform.plugins.domain.profit_reward import factory as profit_factory
    from quant_platform.plugins.domain.sharpe_reward import PLUGIN_METADATA as SHARPE_META
    from quant_platform.plugins.domain.sharpe_reward import factory as sharpe_factory

    reg = manager.registry(REWARD_GROUP)
    for meta, factory in [
        (PROFIT_META, profit_factory),
        (SHARPE_META, sharpe_factory),
        (DRAWDOWN_META, drawdown_factory),
    ]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
