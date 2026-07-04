"""quant-train CLI — RL product training orchestrator (G35)."""

from __future__ import annotations

import argparse
import json
import os
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


def _load_clickhouse_episodes(config: dict[str, Any], *, app_config_path: Path) -> list:
    from quant_platform.plugins.rl.training_dataset import TrainingDatasetPlugin
    from services.database.client import ClickHouseClient
    from services.shared.config import load_config as load_app_config

    app_cfg = load_app_config(app_config_path)
    db = ClickHouseClient(app_cfg.database)
    db.connect(ensure_schema_exists=False)
    try:
        plugin = TrainingDatasetPlugin(storage_backend=db)
        episodes = plugin.load_episodes(config)
    finally:
        db.close()
    if not episodes:
        raise ValueError(
            "no episodes loaded from ClickHouse — verify train_start/train_end and imported klines"
        )
    return episodes


def load_episodes(
    config: dict[str, Any],
    *,
    app_config_path: Path | None = None,
) -> list:
    dataset = config.get("dataset", {})
    if dataset.get("synthetic", True):
        return _build_synthetic_episodes(config)
    path = app_config_path or Path(os.environ.get("CONFIG_PATH", "config/config.yaml"))
    return _load_clickhouse_episodes(config, app_config_path=path)


def run_train(
    config: dict[str, Any],
    *,
    steps: int | None = None,
    checkpoint_dir: Path | None = None,
    app_config_path: Path | None = None,
) -> dict:
    episodes = load_episodes(config, app_config_path=app_config_path)
    loop = OnlineTrainingLoop.compile(config, episodes, checkpoint_dir=checkpoint_dir)
    metrics = loop.run(total_timesteps=steps)
    return {
        "timesteps": metrics.timesteps,
        "updates": metrics.updates,
        "episodes": metrics.episodes,
        "last_loss": metrics.last_loss,
        "graph_schema_hash": loop.graph_schema_hash,
        "episode_count": len(episodes),
        "synthetic": config.get("dataset", {}).get("synthetic", True),
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
    train_parser.add_argument(
        "--app-config",
        type=Path,
        default=None,
        help="App config with database section (default: CONFIG_PATH or config/config.yaml)",
    )

    args = parser.parse_args(argv)
    if args.command == "train":
        config = load_config(args.config)
        result = run_train(
            config,
            steps=args.steps,
            checkpoint_dir=args.checkpoint_dir,
            app_config_path=args.app_config,
        )
        print(json.dumps(result, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
