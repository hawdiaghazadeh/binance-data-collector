"""Fixed fractional risk sizing (Phase 13)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.risks.source import resolve_equity, resolve_exposure


def fixed_position_size(
    ctx: PipelineContext,
    *,
    risk_fraction: float,
    max_size: float = 1.0,
) -> float:
    if risk_fraction <= 0:
        return 0.0
    equity = resolve_equity(ctx)
    if equity <= 0:
        return 0.0
    return min(risk_fraction, max_size)


def check_fixed_risk(
    ctx: PipelineContext,
    order: Any,
    *,
    max_exposure: float,
    max_order_size: float = 1.0,
) -> bool:
    if not isinstance(order, dict):
        return False
    side = str(order.get("side", "hold")).lower()
    if side == "hold":
        return True

    size = float(order.get("size", 0.0))
    if size <= 0 or size > max_order_size:
        return False

    exposure = resolve_exposure(ctx)
    return exposure + size <= max_exposure
