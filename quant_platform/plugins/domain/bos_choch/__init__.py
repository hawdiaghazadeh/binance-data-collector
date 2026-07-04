"""Reference domain plugin: bos_choch."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("bos_choch", "platform.market_structures")


class BosChoChAnalyzer:

    def analyze(self, ctx: PipelineContext) -> None:
        ctx.emit(DataEnvelope(type_key="market_structure", payload={"bos": [], "choch": []}))


def factory(**kwargs) -> BosChoChAnalyzer:
    return BosChoChAnalyzer()


attach_factory_metadata(factory, PLUGIN_METADATA)
