"""Walk-forward evaluation (Phase 16)."""

from __future__ import annotations

from typing import Any

from quant_platform.evaluation_pipelines.fold import evaluate_fold
from quant_platform.evaluation_pipelines.source import normalize_series


def build_walk_forward_folds(
    series: list[Any],
    *,
    train_size: int,
    test_size: int,
    step: int | None = None,
) -> list[tuple[list[Any], list[Any]]]:
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size and test_size must be > 0")

    stride = step or test_size
    folds: list[tuple[list[Any], list[Any]]] = []
    start = 0
    while start + train_size + test_size <= len(series):
        train = series[start : start + train_size]
        test = series[start + train_size : start + train_size + test_size]
        folds.append((train, test))
        start += stride
    return folds


def evaluate_walk_forward(
    model: Any,
    data: Any,
    *,
    train_size: int = 20,
    test_size: int = 5,
    step: int | None = None,
) -> dict[str, Any]:
    series = normalize_series(data)
    folds = build_walk_forward_folds(
        series,
        train_size=train_size,
        test_size=test_size,
        step=step,
    )
    fold_results = [evaluate_fold(model, train, test) for train, test in folds]
    scores = [float(result["score"]) for result in fold_results]
    mean_score = sum(scores) / len(scores) if scores else 0.0

    return {
        "method": "walk_forward",
        "folds": len(fold_results),
        "fold_results": fold_results,
        "scores": scores,
        "mean_score": mean_score,
        "score": mean_score,
    }
