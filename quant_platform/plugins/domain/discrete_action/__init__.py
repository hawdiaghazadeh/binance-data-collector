"""Reference domain plugin: discrete_action."""

from __future__ import annotations

from typing import Any
from quant_platform.core.context import DataEnvelope, PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("discrete_action", "platform.actions")


class DiscreteAction:

    def sample(self, ctx: PipelineContext) -> str:
        return "hold"

    def apply(self, ctx: PipelineContext, action: Any) -> None:
        ctx.emit(DataEnvelope(type_key="action", payload=action))


def factory(**kwargs) -> DiscreteAction:
    return DiscreteAction()


attach_factory_metadata(factory, PLUGIN_METADATA)
