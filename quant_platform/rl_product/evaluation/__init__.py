"""RL product evaluation layer (G36)."""

from quant_platform.rl_product.evaluation.ablation import AblationRunner, LeakageChecker, LeakageConfig
from quant_platform.rl_product.evaluation.evaluator import EvalOptions, PolicyEvaluator
from quant_platform.rl_product.evaluation.metrics import EvalMetrics, aggregate_metrics, summarize_equity_curve
from quant_platform.rl_product.evaluation.replay import assert_deterministic_replay, replay_observation_sequence
from quant_platform.rl_product.evaluation.walk_forward import WalkForwardConfig, WalkForwardRLEvaluator

__all__ = [
    "AblationRunner",
    "EvalMetrics",
    "EvalOptions",
    "LeakageChecker",
    "LeakageConfig",
    "PolicyEvaluator",
    "WalkForwardConfig",
    "WalkForwardRLEvaluator",
    "aggregate_metrics",
    "assert_deterministic_replay",
    "replay_observation_sequence",
    "summarize_equity_curve",
]
