"""Resolve OHLC bars for market structure plugins (Phase 6)."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.indicators.source import resolve_klines
from quant_platform.market_structure.bars import Bar, to_bars


def resolve_bars(ctx: PipelineContext) -> list[Bar]:
    ohlc_env = ctx.optional("ohlc")
    if ohlc_env is not None:
        return to_bars(list(ohlc_env.payload))
    return to_bars(resolve_klines(ctx))
