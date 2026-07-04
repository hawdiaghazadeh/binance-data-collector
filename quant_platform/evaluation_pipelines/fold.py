"""Shared fold evaluation helpers (Phase 16)."""

from __future__ import annotations

from typing import Any

from quant_platform.evaluation_pipelines.source import extract_returns
from quant_platform.rewards.sharpe import compute_sharpe_ratio


def evaluate_fold(model: Any, train: list[Any], test: list[Any]) -> dict[str, float | int]:
    train_returns = extract_returns(train)
    test_returns = extract_returns(test)

    if hasattr(model, "fit"):
        model.fit(train)

    if callable(model):
        model(train, test)
    elif hasattr(model, "predict"):
        model.predict(test)
    elif isinstance(model, dict) and callable(model.get("predict")):
        model["predict"](test)

    score = compute_sharpe_ratio(test_returns)
    return {
        "score": score,
        "test_sharpe": score,
        "test_samples": len(test_returns),
        "train_samples": len(train_returns),
    }
