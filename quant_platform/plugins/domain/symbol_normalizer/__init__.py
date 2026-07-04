"""Symbol and timeframe normalizer plugin (Phase 4)."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.normalizations.symbol import normalize_kline_rows

PLUGIN_METADATA = PluginMetadata(
    name="symbol_normalizer",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Normalize exchange symbol and timeframe on kline rows",
    input_types=["klines"],
    output_types=["klines"],
    registry_group="platform.normalizations",
)


class SymbolNormalizer:
    def normalize(self, ctx: PipelineContext) -> None:
        klines_env = ctx.require("klines")
        rows = list(klines_env.payload)
        normalized = normalize_kline_rows(rows)
        ctx.emit(
            DataEnvelope(
                type_key="klines",
                payload=normalized,
                metadata={**klines_env.metadata, "normalized": True},
            )
        )


def factory(**kwargs) -> SymbolNormalizer:
    return SymbolNormalizer()


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
