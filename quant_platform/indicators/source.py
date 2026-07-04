"""Resolve kline/close series for indicator plugins (Phase 5)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import EnvelopeNotFoundError, PipelineContext
from quant_platform.indicators.compute import extract_closes, row_close


def fetch_klines_from_storage(
    storage_backend: Any,
    *,
    symbol: str,
    timeframe: str,
    limit: int = 500,
) -> list[Any]:
    fetch = getattr(storage_backend, "fetch_klines", None)
    if fetch is None:
        raise RuntimeError("Storage backend does not support fetch_klines")
    return fetch(symbol=symbol, timeframe=timeframe, limit=limit)


def resolve_klines(ctx: PipelineContext) -> list[Any]:
    query_env = ctx.optional("indicator_query")
    if query_env is not None:
        payload = query_env.payload
        storage_env = ctx.require("storage_backend")
        return fetch_klines_from_storage(
            storage_env.payload,
            symbol=str(payload["symbol"]),
            timeframe=str(payload["timeframe"]),
            limit=int(payload.get("limit", 500)),
        )

    klines_env = ctx.optional("klines")
    if klines_env is not None:
        return list(klines_env.payload)

    raise EnvelopeNotFoundError("Required klines or indicator_query + storage_backend not found")


def resolve_closes(ctx: PipelineContext) -> list[float]:
    ohlc_env = ctx.optional("ohlc")
    if ohlc_env is not None:
        return [row_close(bar) for bar in ohlc_env.payload]

    return extract_closes(resolve_klines(ctx))
