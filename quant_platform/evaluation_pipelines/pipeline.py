"""Evaluation pipeline builder — Phase 16."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import EVALUATION_PIPELINE_GROUP


class EvaluationPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def run(
        self,
        ctx: PipelineContext,
        model: Any,
        data: Any,
        evaluator_names: list[str],
    ) -> dict[str, dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}
        for name in evaluator_names:
            evaluator = self._manager.get(EVALUATION_PIPELINE_GROUP, name)
            results[name] = evaluator.evaluate(model, data)
        ctx.emit(DataEnvelope(type_key="evaluation_results", payload=results))
        return results

    def build_graph(self, evaluator_names: list[str]) -> CompiledExecutionGraph:
        names = list(evaluator_names)

        def handler(ctx: PipelineContext) -> None:
            request = ctx.require("evaluation_request").payload
            self.run(
                ctx,
                request.get("model"),
                request.get("data"),
                names,
            )

        return CompiledExecutionGraph(
            (
                ExecutionStep(
                    plugin_name="evaluation_pipeline",
                    handler=handler,
                    registry_group=EVALUATION_PIPELINE_GROUP,
                ),
            )
        )


def register_evaluation_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.holdout_eval import PLUGIN_METADATA as HOLDOUT_META
    from quant_platform.plugins.domain.holdout_eval import factory as holdout_factory
    from quant_platform.plugins.domain.walk_forward import PLUGIN_METADATA as WALK_META
    from quant_platform.plugins.domain.walk_forward import factory as walk_factory

    reg = manager.registry(EVALUATION_PIPELINE_GROUP)
    for meta, factory in [(WALK_META, walk_factory), (HOLDOUT_META, holdout_factory)]:
        if meta.name not in {m.name for m in reg.list_plugins()}:
            reg.register(meta, factory)
