"""G36 evaluation test helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from quant_platform.rl_product.protocols import Episode
from services.shared.models import KlineRow


def make_episode(
    count: int = 40,
    *,
    episode_id: str = "ep_0",
    vol_scale: float = 0.2,
    start_idx: int = 0,
    split: str = "train",
) -> Episode:
    base = datetime(2022, 1, 1, tzinfo=timezone.utc) + timedelta(hours=start_idx * count)
    bars = []
    for i in range(count):
        open_time = base + timedelta(hours=i)
        close = 100.0 + (start_idx + i) * vol_scale
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
        split=split,  # type: ignore[arg-type]
        start_idx=start_idx,
    )


def make_episode_set(count: int = 8, *, bar_count: int = 30) -> list[Episode]:
    return [
        make_episode(bar_count, episode_id=f"ep_{i}", vol_scale=0.15 + i * 0.05, start_idx=i * 100)
        for i in range(count)
    ]


def eval_config(**overrides) -> dict:
    cfg = {
        "training": {
            "market": "futures",
            "initial_equity": 10_000.0,
            "rollout_steps": 8,
            "total_timesteps": 24,
            "seed": 11,
        },
        "observation": {"dim": 128, "context_dims": 16, "schema_version": "1.0"},
        "perception": {"master_gate": 1.0},
        "execution": {"fee_bps": 10, "spread_bps": 5, "slippage_bps": 3},
        "reward": {"clip_sigma": 5.0, "max_context_reward_weight": 0.05},
        "evaluation": {
            "walk_forward_folds": 4,
            "train_timesteps": 24,
            "leakage": {
                "max_context_sharpe_uplift_pct": 15,
                "context_only_must_not_beat_baseline": True,
            },
            "ablation_runs": ["price_only", "full_context", "gate_sweep"],
        },
        "agent": {
            "price_trunk_hidden": [32, 16],
            "context_trunk_hidden": [8, 4],
            "portfolio_trunk_hidden": [8, 4],
            "total_timesteps": 24,
            "ppo_epochs": 1,
        },
    }
    cfg.update(overrides)
    return cfg
