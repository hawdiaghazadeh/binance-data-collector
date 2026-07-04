"""quant-train CLI — RL product training orchestrator (G35)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from quant_platform.rl_product.training.loop import OnlineTrainingLoop


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif path.suffix == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"unsupported config format: {path.suffix}")
    if not isinstance(data, dict):
        raise ValueError("config root must be a mapping")
    return data


def _build_synthetic_episodes(config: dict[str, Any]) -> list:
    """Fallback episodes for CLI/dev when no storage backend is configured."""
    from datetime import datetime, timedelta, timezone

    from quant_platform.rl_product.protocols import Episode
    from services.shared.models import KlineRow

    training = config.get("training", config)
    length = int(training.get("episode_length", 64))
    base = datetime(2022, 1, 1, tzinfo=timezone.utc)
    bars = []
    for i in range(length):
        open_time = base + timedelta(hours=i)
        close = 100.0 + i * 0.2
        bars.append(
            KlineRow(
                symbol=str(training.get("symbol", "BTCUSDT")),
                timeframe=str(training.get("timeframe", "1h")),
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
    return [
        Episode(
            episode_id="synthetic_0",
            symbol=str(training.get("symbol", "BTCUSDT")),
            timeframe=str(training.get("timeframe", "1h")),
            bars=tuple(bars),
            split="train",
            start_idx=0,
        )
    ]


def run_train(config: dict[str, Any], *, steps: int | None = None, checkpoint_dir: Path | None = None) -> dict:
    episodes = _build_synthetic_episodes(config)
    if config.get("dataset", {}).get("synthetic", True) is False:
        raise NotImplementedError("ClickHouse dataset loading is configured for G30 plugin path only")
    loop = OnlineTrainingLoop.compile(config, episodes, checkpoint_dir=checkpoint_dir)
    metrics = loop.run(total_timesteps=steps)
    return {
        "timesteps": metrics.timesteps,
        "updates": metrics.updates,
        "episodes": metrics.episodes,
        "last_loss": metrics.last_loss,
        "graph_schema_hash": loop.graph_schema_hash,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quant-train", description="RL product training CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    train_parser = sub.add_parser("train", help="Run online PPO training")
    train_parser.add_argument("--config", type=Path, required=True, help="Training YAML/JSON config")
    train_parser.add_argument("--steps", type=int, default=None, help="Override total timesteps")
    train_parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path(".quant_platform/checkpoints"),
        help="Directory for periodic checkpoints",
    )

    args = parser.parse_args(argv)
    if args.command == "train":
        config = load_config(args.config)
        result = run_train(config, steps=args.steps, checkpoint_dir=args.checkpoint_dir)
        print(json.dumps(result, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
