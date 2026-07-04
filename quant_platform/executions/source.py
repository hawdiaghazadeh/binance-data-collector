"""Execution context helpers (Phase 13)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.indicators.compute import extract_closes, row_close
from quant_platform.indicators.source import resolve_klines


def resolve_price(ctx: PipelineContext) -> float:
    price_env = ctx.optional("price")
    if price_env is not None:
        return float(price_env.payload)

    ohlc_env = ctx.optional("ohlc")
    if ohlc_env is not None and ohlc_env.payload:
        return row_close(ohlc_env.payload[-1])

    closes = extract_closes(resolve_klines(ctx))
    if not closes:
        raise ValueError("price unavailable: emit klines, ohlc, or price")
    return float(closes[-1])


def normalize_order(order: Any, *, default_symbol: str = "BTCUSDT") -> dict[str, Any]:
    if isinstance(order, dict):
        side = str(order.get("side", "hold")).lower()
        if side == "long":
            side = "buy"
        elif side == "short":
            side = "sell"
        return {
            "symbol": str(order.get("symbol", default_symbol)),
            "side": side,
            "size": float(order.get("size", 0.0)),
        }
    if isinstance(order, str):
        side = order.lower()
        if side == "long":
            side = "buy"
        elif side == "short":
            side = "sell"
        return {"symbol": default_symbol, "side": side, "size": 0.0 if side == "hold" else 1.0}
    raise TypeError(f"Unsupported order type: {type(order)!r}")
