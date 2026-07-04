"""Reference domain plugin: direction_label."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("direction_label", "platform.labels")


class DirectionLabel:

    def generate(self, ctx: PipelineContext) -> None:
        ctx.emit(DataEnvelope(type_key="labels", payload={"direction": "neutral"}))


def factory(**kwargs) -> DirectionLabel:
    return DirectionLabel()


attach_factory_metadata(factory, PLUGIN_METADATA)
