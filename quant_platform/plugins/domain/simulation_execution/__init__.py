"""Reference domain plugin: simulation_execution."""

from __future__ import annotations

from typing import Any
from quant_platform.core.context import PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("simulation_execution", "platform.executions")


class SimulationExecution:

    def execute_order(self, ctx: PipelineContext, order: Any) -> dict:
        return {"status": "filled", "order": order}


def factory(**kwargs) -> SimulationExecution:
    return SimulationExecution()


attach_factory_metadata(factory, PLUGIN_METADATA)
