"""Live trading session helpers (Phase 19)."""

from __future__ import annotations

from typing import Any

from quant_platform.paper_trading.source import closes_from_bars, session_config


def live_session_config(
    *,
    strategy: Any,
    exchange: Any,
    bars: list[Any] | None = None,
    symbol: str = "BTCUSDT",
    initial_cash: float = 10_000.0,
    fee_rate: float = 0.001,
    slippage_bps: float = 5.0,
    risk_fraction: float = 0.02,
) -> dict[str, Any]:
    config = session_config(
        strategy=strategy,
        bars=bars or [],
        symbol=symbol,
        initial_cash=initial_cash,
        fee_rate=fee_rate,
        slippage_bps=slippage_bps,
        risk_fraction=risk_fraction,
    )
    config["exchange"] = exchange
    return config


def resolve_live_price(exchange: Any, symbol: str, *, fallback: float) -> float:
    if exchange is None:
        return fallback
    if hasattr(exchange, "fetch_ticker"):
        ticker = exchange.fetch_ticker(symbol)
        return float(ticker["price"])
    if hasattr(exchange, "fetch_ticker_price"):
        ticker = exchange.fetch_ticker_price(symbol)
        return float(ticker["price"])
    return fallback
