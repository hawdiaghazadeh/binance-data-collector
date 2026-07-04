"""Ablation A/B/C runner and leakage checks (G36)."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Literal

from quant_platform.rl_product.evaluation.evaluator import EvalOptions, PolicyEvaluator
from quant_platform.rl_product.evaluation.metrics import EvalMetrics
from quant_platform.rl_product.evaluation.walk_forward import WalkForwardRLEvaluator
from quant_platform.rl_product.protocols import Episode
from quant_platform.rl_product.training.loop import OnlineTrainingLoop

AblationVariant = Literal["price_only", "full_context", "gate_sweep", "context_only"]


@dataclass(frozen=True, slots=True)
class LeakageConfig:
    max_context_sharpe_uplift_pct: float = 15.0
    context_only_must_not_beat_baseline: bool = True
    context_only_trade_ratio_max: float = 0.05

    @classmethod
    def from_config(cls, config: dict) -> LeakageConfig:
        evaluation = config.get("evaluation", config)
        leakage = evaluation.get("leakage", {})
        return cls(
            max_context_sharpe_uplift_pct=float(leakage.get("max_context_sharpe_uplift_pct", 15.0)),
            context_only_must_not_beat_baseline=bool(
                leakage.get("context_only_must_not_beat_baseline", True)
            ),
            context_only_trade_ratio_max=float(leakage.get("context_only_trade_ratio_max", 0.05)),
        )


def _variant_config(base: dict[str, Any], variant: AblationVariant) -> dict[str, Any]:
    config = copy.deepcopy(base)
    perception = config.setdefault("perception", {})
    evaluation = config.setdefault("evaluation", {})
    ablation = evaluation.setdefault("ablation", {})
    observation = config.setdefault("observation", {})

    if variant == "price_only":
        perception["master_gate"] = 0.0
        ablation["context_only"] = False
    elif variant == "full_context":
        perception["master_gate"] = 1.0
        ablation["context_only"] = False
    elif variant == "gate_sweep":
        perception["master_gate"] = 1.0
        perception["gate_smc"] = 0.5
        perception["gate_rtm"] = 0.5
        perception["gate_ict"] = 0.5
        ablation["context_only"] = False
    elif variant == "context_only":
        observation["test_mode"] = True
        ablation["context_only"] = True
        perception["master_gate"] = 1.0
    return config


def context_sharpe_uplift_pct(price_only: EvalMetrics, full_context: EvalMetrics) -> float:
    if abs(price_only.sharpe) < 1e-9:
        return abs(full_context.sharpe) * 100.0
    return ((full_context.sharpe - price_only.sharpe) / abs(price_only.sharpe)) * 100.0


class LeakageChecker:
    """Mandatory context leakage hardening checks (plan §15.2)."""

    def __init__(self, config: LeakageConfig | None = None) -> None:
        self._config = config or LeakageConfig()

    def check(
        self,
        *,
        price_only: EvalMetrics,
        full_context: EvalMetrics,
        context_only: EvalMetrics,
        context_only_entropy: float = 0.0,
    ) -> dict[str, Any]:
        cfg = self._config
        uplift_pct = context_sharpe_uplift_pct(price_only, full_context)
        uplift_pass = uplift_pct <= cfg.max_context_sharpe_uplift_pct

        context_only_sharpe_fail = context_only.sharpe <= 0.0
        context_only_dd_fail = (
            price_only.max_drawdown > 0
            and context_only.max_drawdown > price_only.max_drawdown * 2.0
        )
        context_only_pass = context_only_sharpe_fail or context_only_dd_fail
        if cfg.context_only_must_not_beat_baseline:
            context_only_pass = context_only_pass and full_context.sharpe >= context_only.sharpe

        trade_ratio = context_only.trade_count / max(price_only.trade_count, 1)
        no_trade_signal = trade_ratio < cfg.context_only_trade_ratio_max or context_only_entropy < 0.01

        return {
            "context_uplift_pct": uplift_pct,
            "context_uplift_pass": uplift_pass,
            "context_only_sharpe": context_only.sharpe,
            "context_only_max_drawdown": context_only.max_drawdown,
            "context_only_pass": context_only_pass,
            "context_only_trade_ratio": trade_ratio,
            "context_only_no_trade_signal": no_trade_signal,
            "all_pass": uplift_pass and context_only_pass,
        }


class AblationRunner:
    """Run ablation variants A/B/C and optional leakage validation."""

    DEFAULT_VARIANTS: tuple[AblationVariant, ...] = ("price_only", "full_context", "gate_sweep")

    def __init__(
        self,
        *,
        walk_forward: WalkForwardRLEvaluator | None = None,
        evaluator: PolicyEvaluator | None = None,
        leakage: LeakageChecker | None = None,
    ) -> None:
        self._walk_forward = walk_forward or WalkForwardRLEvaluator(evaluator=evaluator)
        self._evaluator = evaluator or PolicyEvaluator()
        self._leakage = leakage

    def run(
        self,
        config: dict[str, Any],
        episodes: list[Episode],
        *,
        variants: tuple[AblationVariant, ...] | None = None,
        include_context_only: bool = True,
    ) -> dict[str, Any]:
        evaluation = config.get("evaluation", config)
        runs = tuple(evaluation.get("ablation_runs", variants or self.DEFAULT_VARIANTS))
        train_timesteps = int(
            evaluation.get(
                "train_timesteps",
                config.get("training", {}).get("total_timesteps", 64),
            )
        )

        results: dict[str, Any] = {"variants": {}, "train_timesteps": train_timesteps}
        for variant in runs:
            if variant not in {"price_only", "full_context", "gate_sweep", "context_only"}:
                continue
            variant_config = _variant_config(config, variant)  # type: ignore[arg-type]
            variant_config.setdefault("training", {})["total_timesteps"] = train_timesteps
            if variant == "context_only" and not include_context_only:
                continue
            if variant == "context_only":
                results["variants"][variant] = self._run_context_only(variant_config, episodes)
            else:
                wf = self._walk_forward.evaluate(variant_config, episodes)
                results["variants"][variant] = wf

        if include_context_only and "context_only" not in results["variants"]:
            ctx_config = _variant_config(config, "context_only")
            ctx_config.setdefault("training", {})["total_timesteps"] = train_timesteps
            results["variants"]["context_only"] = self._run_context_only(ctx_config, episodes)

        if self._leakage or "leakage" in evaluation:
            checker = self._leakage or LeakageChecker(LeakageConfig.from_config(config))
            price_only = _metrics_from_variant(results["variants"].get("price_only", {}))
            full_context = _metrics_from_variant(results["variants"].get("full_context", {}))
            context_only = _metrics_from_variant(results["variants"].get("context_only", {}))
            ctx_cfg = _variant_config(config, "context_only")
            graph = OnlineTrainingLoop.compile(ctx_cfg, episodes[:1]).graph
            loop = OnlineTrainingLoop.compile(ctx_cfg, episodes)
            loop.run(total_timesteps=train_timesteps)
            entropy = self._evaluator.action_entropy_mean(
                loop._trainer,  # noqa: SLF001
                graph,
                episodes[:2],
                options=EvalOptions(zero_price=True),
            )
            results["leakage"] = checker.check(
                price_only=price_only,
                full_context=full_context,
                context_only=context_only,
                context_only_entropy=entropy,
            )
        return results

    def _run_context_only(self, config: dict[str, Any], episodes: list[Episode]) -> dict[str, Any]:
        train_timesteps = int(config.get("training", {}).get("total_timesteps", 64))
        loop = OnlineTrainingLoop.compile(config, episodes)
        loop.run(total_timesteps=train_timesteps)
        metrics = self._evaluator.evaluate_episodes(
            loop._trainer,  # noqa: SLF001
            loop.graph,
            episodes[-max(1, len(episodes) // 4) :],
            options=EvalOptions(zero_price=True),
        )
        return {
            "method": "context_only",
            "oos_sharpe": metrics.sharpe,
            "oos_max_drawdown": metrics.max_drawdown,
            "oos_win_rate": metrics.win_rate,
            "trade_count": metrics.trade_count,
        }


def _metrics_from_variant(payload: dict[str, Any]) -> EvalMetrics:
    if not payload:
        return EvalMetrics()
    return EvalMetrics(
        sharpe=float(payload.get("oos_sharpe", payload.get("oos_sharpe_mean", 0.0))),
        max_drawdown=float(payload.get("oos_max_drawdown", 0.0)),
        win_rate=float(payload.get("oos_win_rate", payload.get("oos_win_rate_mean", 0.0))),
        trade_count=int(payload.get("trade_count", 0)),
    )
