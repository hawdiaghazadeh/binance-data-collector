"""G35 training test helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from quant_platform.rl_product.protocols import Episode
from services.shared.models import KlineRow


def make_episode(count: int = 40, *, episode_id: str = "ep_0", vol_scale: float = 0.2) -> Episode:
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    bars = []
    for i in range(count):
        open_time = base + timedelta(hours=i)
        close = 100.0 + i * vol_scale
        bars.append(
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
    return Episode(
        episode_id=episode_id,
        symbol="BTCUSDT",
        timeframe="1h",
        bars=tuple(bars),
        split="train",
        start_idx=0,
    )


def train_config(**overrides) -> dict:
    cfg = {
        "training": {
            "market": "futures",
            "initial_equity": 10_000.0,
            "rollout_steps": 16,
            "total_timesteps": 32,
            "seed": 7,
        },
        "observation": {"dim": 128, "context_dims": 16, "schema_version": "1.0"},
        "perception": {"master_gate": 1.0},
        "execution": {"fee_bps": 10, "spread_bps": 5, "slippage_bps": 3},
        "reward": {"clip_sigma": 5.0, "max_context_reward_weight": 0.05},
        "agent": {
            "price_trunk_hidden": [32, 16],
            "context_trunk_hidden": [8, 4],
            "portfolio_trunk_hidden": [8, 4],
            "total_timesteps": 32,
            "ppo_epochs": 1,
            "entropy_coef_start": 0.01,
            "entropy_coef_end": 0.005,
            "entropy_coef_min": 0.0005,
        },
    }
    cfg.update(overrides)
    return cfg
