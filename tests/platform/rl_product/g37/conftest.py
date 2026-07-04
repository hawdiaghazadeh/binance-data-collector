"""G37 deploy test helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from quant_platform.rl_product.protocols import Episode
from services.shared.models import KlineRow


def make_kline_rows(count: int = 40, *, start: float = 100.0, step: float = 0.3) -> list[KlineRow]:
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    rows: list[KlineRow] = []
    for i in range(count):
        open_time = base + timedelta(hours=i)
        close = start + i * step
        rows.append(
            KlineRow(
                symbol="BTCUSDT",
                timeframe="1h",
                open_time=open_time,
                open=close - 0.5,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=100.0 + i,
                close_time=open_time + timedelta(hours=1),
                quote_volume=close * 100,
                trade_count=10,
                taker_buy_volume=50.0,
                taker_buy_quote_volume=close * 50,
            )
        )
    return rows


def make_episode(count: int = 40) -> Episode:
    bars = tuple(make_kline_rows(count))
    return Episode(
        episode_id="deploy_ep",
        symbol="BTCUSDT",
        timeframe="1h",
        bars=bars,
        split="test",
        start_idx=0,
    )


def deploy_config(**overrides) -> dict:
    cfg = {
        "training": {
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "market": "spot",
            "initial_equity": 10_000.0,
            "rollout_steps": 8,
            "total_timesteps": 16,
            "seed": 3,
        },
        "observation": {"dim": 128, "context_dims": 16, "schema_version": "1.0"},
        "perception": {"master_gate": 1.0},
        "execution": {"fee_bps": 10, "spread_bps": 5, "slippage_bps": 3},
        "reward": {"max_context_reward_weight": 0.05},
        "deploy": {"live_approved": False},
        "agent": {
            "price_trunk_hidden": [32, 16],
            "context_trunk_hidden": [8, 4],
            "portfolio_trunk_hidden": [8, 4],
            "total_timesteps": 16,
            "ppo_epochs": 1,
        },
    }
    cfg.update(overrides)
    return cfg
