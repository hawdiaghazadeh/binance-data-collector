"""Strategy context helpers (Phase 12)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.indicators.compute import extract_closes, row_close
from quant_platform.indicators.source import resolve_klines


def resolve_closes(ctx: PipelineContext) -> list[float]:
    ohlc_env = ctx.optional("ohlc")
    if ohlc_env is not None:
        return [row_close(bar) for bar in ohlc_env.payload]
    return extract_closes(resolve_klines(ctx))


def resolve_indicator_series(ctx: PipelineContext, key: str) -> list[Any] | None:
    envelope = ctx.optional(key)
    if envelope is None:
        return None
    payload = envelope.payload
    if isinstance(payload, list):
        return payload
    return None


def current_bar_index(ctx: PipelineContext) -> int:
    closes = resolve_closes(ctx)
    return max(len(closes) - 1, 0)
