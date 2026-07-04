"""Reference domain plugin: candle_observation."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("candle_observation", "platform.observations")


class CandleObservation:

    def build(self, ctx: PipelineContext) -> dict:
        klines = ctx.optional("klines")
        obs = {"candles": klines.payload if klines else []}
        ctx.emit(DataEnvelope(type_key="observation", payload=obs))
        return obs


def factory(**kwargs) -> CandleObservation:
    return CandleObservation()


attach_factory_metadata(factory, PLUGIN_METADATA)
