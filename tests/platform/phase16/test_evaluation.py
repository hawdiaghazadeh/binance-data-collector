"""Phase 16 evaluation pipeline tests."""

from __future__ import annotations

import pytest

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager
from quant_platform.evaluation_pipelines.holdout import evaluate_holdout
from quant_platform.evaluation_pipelines.pipeline import EvaluationPipelineBuilder, register_evaluation_plugins
from quant_platform.evaluation_pipelines.source import extract_returns
from quant_platform.evaluation_pipelines.walk_forward import build_walk_forward_folds, evaluate_walk_forward
from quant_platform.rewards.sharpe import compute_sharpe_ratio


def _returns(count: int) -> list[dict[str, float]]:
    return [{"return": 0.01 * (index + 1)} for index in range(count)]


class _RecordingModel:
    def __init__(self) -> None:
        self.fit_calls = 0
        self.predict_calls = 0

    def fit(self, train: list) -> None:
        self.fit_calls += 1

    def predict(self, test: list) -> list[float]:
        self.predict_calls += 1
        return extract_returns(test)


class TestEvaluationCompute:
    def test_extract_returns_from_closes(self):
        data = [{"close": 100.0}, {"close": 110.0}, {"close": 99.0}]
        returns = extract_returns(data)
        assert returns[0] == pytest.approx(0.1)
        assert returns[1] == pytest.approx(-0.1)

    def test_build_walk_forward_folds(self):
        series = list(range(30))
        folds = build_walk_forward_folds(series, train_size=10, test_size=5, step=5)
        assert len(folds) == 4
        assert len(folds[0][0]) == 10
        assert len(folds[0][1]) == 5

    def test_evaluate_walk_forward(self):
        result = evaluate_walk_forward(
            _RecordingModel(),
            _returns(30),
            train_size=10,
            test_size=5,
            step=5,
        )
        assert result["method"] == "walk_forward"
        assert result["folds"] == 4
        assert result["score"] == pytest.approx(result["mean_score"])

    def test_evaluate_holdout(self):
        result = evaluate_holdout(_RecordingModel(), _returns(10), train_ratio=0.8)
        assert result["method"] == "holdout"
        assert result["train_size"] == 8
        assert result["test_size"] == 2
        assert result["score"] == pytest.approx(compute_sharpe_ratio([0.09, 0.1]))


class TestEvaluationRegistry:
    def test_walk_forward_plugin(self):
        manager = PluginManager()
        register_evaluation_plugins(manager)
        evaluator = manager.get(
            "platform.evaluation_pipelines",
            "walk_forward",
            config={"train_size": 8, "test_size": 4, "step": 4},
        )
        result = evaluator.evaluate(None, _returns(20))
        assert result["folds"] >= 1
        assert "score" in result

    def test_holdout_eval_plugin(self):
        manager = PluginManager()
        register_evaluation_plugins(manager)
        evaluator = manager.get("platform.evaluation_pipelines", "holdout_eval")
        result = evaluator.evaluate(_RecordingModel(), _returns(12))
        assert result["method"] == "holdout"
        assert result["folds"] == 1

    def test_evaluation_pipeline_builder(self):
        manager = PluginManager()
        register_evaluation_plugins(manager)
        builder = EvaluationPipelineBuilder(manager)
        ctx = PipelineContext()
        model = _RecordingModel()
        results = builder.run(ctx, model, _returns(24), ["walk_forward", "holdout_eval"])
        assert "walk_forward" in results
        assert "holdout_eval" in results
        assert ctx.require("evaluation_results").payload == results
