"""BOS and CHoCH market structure plugin (Phase 6)."""

from __future__ import annotations

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.plugin import PluginMetadata
from quant_platform.market_structure.bos_choch import detect_bos_choch
from quant_platform.market_structure.source import resolve_bars

PLUGIN_METADATA = PluginMetadata(
    name="bos_choch",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Detect Break of Structure and Change of Character from swing points",
    input_types=["klines", "ohlc"],
    output_types=["market_structure"],
    registry_group="platform.market_structures",
)


class BosChoChAnalyzer:
    def __init__(self, swing_lookback: int = 2) -> None:
        self._swing_lookback = swing_lookback

    def analyze(self, ctx: PipelineContext) -> None:
        bars = resolve_bars(ctx)
        bos, choch = detect_bos_choch(bars, swing_lookback=self._swing_lookback)
        ctx.emit(
            DataEnvelope(
                type_key="market_structure",
                payload={"bos": bos, "choch": choch},
                metadata={"swing_lookback": self._swing_lookback},
            )
        )


def factory(*, swing_lookback: int = 2, config: dict | None = None, **kwargs) -> BosChoChAnalyzer:
    if config and "swing_lookback" in config:
        swing_lookback = int(config["swing_lookback"])
    return BosChoChAnalyzer(swing_lookback=swing_lookback)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
