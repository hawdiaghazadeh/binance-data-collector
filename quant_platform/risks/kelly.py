"""Kelly criterion risk sizing (Phase 13)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.context import PipelineContext
from quant_platform.risks.source import resolve_exposure, resolve_trade_stats


def compute_kelly_fraction(
    win_rate: float,
    win_loss_ratio: float,
    *,
    cap: float = 0.25,
) -> float:
    if win_loss_ratio <= 0:
        return 0.0
    raw = win_rate - (1.0 - win_rate) / win_loss_ratio
    return max(0.0, min(raw, cap))


def kelly_position_size(
    ctx: PipelineContext,
    *,
    cap: float = 0.25,
    min_fraction: float = 0.0,
) -> float:
    stats = resolve_trade_stats(ctx)
    fraction = compute_kelly_fraction(
        stats["win_rate"],
        stats["win_loss_ratio"],
        cap=cap,
    )
    return max(min_fraction, fraction)


def check_kelly_risk(
    ctx: PipelineContext,
    order: Any,
    *,
    max_exposure: float,
) -> bool:
    if not isinstance(order, dict):
        return False
    side = str(order.get("side", "hold")).lower()
    if side == "hold":
        return True

    size = float(order.get("size", 0.0))
    if size <= 0:
        return False

    stats = resolve_trade_stats(ctx)
    max_kelly = compute_kelly_fraction(stats["win_rate"], stats["win_loss_ratio"])
    if size > max_kelly:
        return False

    exposure = resolve_exposure(ctx)
    return exposure + size <= max_exposure
