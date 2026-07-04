"""Holdout evaluation (Phase 16)."""

from __future__ import annotations

from typing import Any

from quant_platform.evaluation_pipelines.fold import evaluate_fold
from quant_platform.evaluation_pipelines.source import normalize_series


def evaluate_holdout(
    model: Any,
    data: Any,
    *,
    train_ratio: float = 0.8,
) -> dict[str, Any]:
    if not 0.0 < train_ratio < 1.0:
        raise ValueError("train_ratio must be between 0 and 1")

    series = normalize_series(data)
    if len(series) < 2:
        return {
            "method": "holdout",
            "score": 0.0,
            "mean_score": 0.0,
            "train_size": len(series),
            "test_size": 0,
            "folds": 0,
        }

    split = max(1, int(len(series) * train_ratio))
    train = series[:split]
    test = series[split:]
    if not test:
        train = series[:-1]
        test = series[-1:]

    result = evaluate_fold(model, train, test)
    score = float(result["score"])
    return {
        "method": "holdout",
        "train_size": len(train),
        "test_size": len(test),
        "folds": 1,
        "fold_results": [result],
        "scores": [score],
        "mean_score": score,
        "score": score,
    }
