"""Resolve market data for observation plugins (Phase 8)."""

from __future__ import annotations

from quant_platform.core.context import PipelineContext
from quant_platform.market_structure.bars import Bar
from quant_platform.market_structure.source import resolve_bars


def resolve_observation_bars(ctx: PipelineContext) -> list[Bar]:
    return resolve_bars(ctx)
