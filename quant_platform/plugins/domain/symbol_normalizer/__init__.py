"""Reference domain plugin: symbol_normalizer."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("symbol_normalizer", "platform.normalizations")


class SymbolNormalizer:

    def normalize(self, ctx: PipelineContext) -> None:
        for key in list(ctx.keys()):
            env = ctx.require(key)
            if isinstance(env.payload, list) and env.payload and isinstance(env.payload[0], dict):
                normalized = [
                    {**row, "symbol": str(row.get("symbol", "")).upper()} for row in env.payload
                ]
                ctx.emit(DataEnvelope(type_key=key, payload=normalized, metadata=env.metadata))


def factory(**kwargs) -> SymbolNormalizer:
    return SymbolNormalizer()


attach_factory_metadata(factory, PLUGIN_METADATA)
