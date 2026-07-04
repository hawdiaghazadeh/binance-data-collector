"""Resolve price series for environment plugins (Phase 11)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.environments.common import extract_closes
from quant_platform.indicators.source import resolve_klines


def resolve_prices(ctx: PipelineContext | None, prices: list[float] | None) -> list[float]:
    if prices is not None:
        return list(prices)
    if ctx is None:
        raise ValueError("Either prices or PipelineContext with klines is required")

    klines_env = ctx.optional("klines")
    if klines_env is not None:
        return extract_closes(list(klines_env.payload))
    return extract_closes(resolve_klines(ctx))
