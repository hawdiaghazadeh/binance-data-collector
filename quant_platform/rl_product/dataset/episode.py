"""Episode builder — chronological windows with train/val/test split."""

from __future__ import annotations

from services.shared.models import KlineRow

from quant_platform.rl_product.protocols import Episode, EpisodeSplit


class EpisodeBuilder:
    """Split a loaded bar series into fixed-length episodes."""

    @staticmethod
    def build(
        bars: list[KlineRow],
        *,
        symbol: str,
        timeframe: str,
        episode_length: int,
        stride: int | None = None,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
    ) -> list[Episode]:
        if episode_length < 2:
            raise ValueError("episode_length must be >= 2")
        if not bars:
            return []
        if stride is None:
            stride = episode_length
        if stride < 1:
            raise ValueError("stride must be >= 1")
        if train_ratio + val_ratio >= 1.0:
            raise ValueError("train_ratio + val_ratio must be < 1.0")

        windows: list[tuple[int, tuple[KlineRow, ...]]] = []
        idx = 0
        while idx + episode_length <= len(bars):
            window = tuple(bars[idx : idx + episode_length])
            windows.append((idx, window))
            idx += stride

        if not windows:
            return []

        n = len(windows)
        n_train = max(1, int(n * train_ratio))
        n_val = max(0, int(n * val_ratio))
        n_test = n - n_train - n_val
        if n_test < 0:
            n_test = 0
            n_val = n - n_train

        episodes: list[Episode] = []
        for i, (start_idx, window) in enumerate(windows):
            if i < n_train:
                split: EpisodeSplit = "train"
            elif i < n_train + n_val:
                split = "val"
            else:
                split = "test"
            episode_id = f"{symbol}_{timeframe}_{start_idx}_{split}"
            episodes.append(
                Episode(
                    episode_id=episode_id,
                    symbol=symbol,
                    timeframe=timeframe,
                    bars=window,
                    split=split,
                    start_idx=start_idx,
                )
            )
        return episodes

    @staticmethod
    def build_from_config(bars: list[KlineRow], config: dict) -> list[Episode]:
        training = config.get("training", config)
        symbol = str(training["symbol"])
        timeframe = str(training["timeframe"])
        episode_length = int(training.get("episode_length", 500))
        stride = training.get("episode_stride")
        dataset = config.get("dataset", {})
        return EpisodeBuilder.build(
            bars,
            symbol=symbol,
            timeframe=timeframe,
            episode_length=episode_length,
            stride=int(stride) if stride is not None else None,
            train_ratio=float(dataset.get("train_ratio", 0.70)),
            val_ratio=float(dataset.get("val_ratio", 0.15)),
        )
