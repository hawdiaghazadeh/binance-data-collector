"""Reference domain plugin: ema_indicator."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("ema_indicator", "platform.indicators")


class EmaIndicator:

    def compute(self, ctx: PipelineContext) -> None:
        ohlc = ctx.optional("ohlc")
        if ohlc:
            closes = [bar["close"] for bar in ohlc.payload]
            ema = sum(closes[-min(20, len(closes)):]) / min(20, len(closes)) if closes else 0.0
            ctx.emit(DataEnvelope(type_key="ema", payload={"ema20": ema}))


def factory(**kwargs) -> EmaIndicator:
    return EmaIndicator()


attach_factory_metadata(factory, PLUGIN_METADATA)
