"""G33 environment test helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from quant_platform.rl_product.protocols import Episode
from services.shared.models import KlineRow


def kline(*, close: float, index: int = 0, volume: float = 1000.0) -> KlineRow:
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    open_time = base + timedelta(hours=index)
    return KlineRow(
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=open_time,
        open=close - 0.5,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=volume,
        close_time=open_time + timedelta(hours=1) - timedelta(seconds=1),
        quote_volume=close * volume,
        trade_count=10,
        taker_buy_volume=volume / 2,
        taker_buy_quote_volume=close * volume / 2,
    )


def trending_episode(count: int = 50) -> Episode:
    bars = tuple(kline(close=100.0 + i * 0.5, index=i) for i in range(count))
    return Episode(
        episode_id="test_ep",
        symbol="BTCUSDT",
        timeframe="1h",
        bars=bars,
        split="train",
        start_idx=0,
    )


def default_config(**overrides) -> dict:
    cfg = {
        "training": {"symbol": "BTCUSDT", "timeframe": "1h", "initial_equity": 10_000.0},
        "observation": {"dim": 128, "context_dims": 16, "schema_version": "1.0"},
        "perception": {"master_gate": 1.0},
        "execution": {"fee_bps": 10, "spread_bps": 5, "slippage_bps": 3},
        "reward": {
            "drawdown_penalty_weight": 0.15,
            "sharpe_component_weight": 0.10,
            "max_context_reward_weight": 0.05,
        },
    }
    cfg.update(overrides)
    return cfg
