"""Perception pipeline orchestrator (G31)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Sequence

from quant_platform.rl_product.perception._helpers import HintEnvelope, visible_bars
from quant_platform.rl_product.perception.compressor import PerceptionCompressor
from quant_platform.rl_product.perception.gate import FeatureGate, GateConfig
from quant_platform.rl_product.perception.ict import (
    compute_killzone_prob,
    compute_premium_discount,
    compute_session_prob,
)
from quant_platform.rl_product.perception.rtm import (
    compute_compression_prob,
    compute_flip_prob,
    compute_sd_strength,
    compute_sweep_prob,
)
from quant_platform.rl_product.perception.smc import (
    compute_bos_prob,
    compute_choch_prob,
    compute_fvg_fill_prob,
    compute_ob_validity,
)
from services.shared.models import KlineRow

HintFn = Callable[[Sequence[Any]], HintEnvelope]

DEFAULT_HINT_COMPUTERS: dict[str, HintFn] = {
    "bos_p": compute_bos_prob,
    "choch_p": compute_choch_prob,
    "ob_validity": compute_ob_validity,
    "fvg_fill_p": compute_fvg_fill_prob,
    "sd_strength": compute_sd_strength,
    "sweep_p": compute_sweep_prob,
    "compression_p": compute_compression_prob,
    "flip_p": compute_flip_prob,
    "session_p": compute_session_prob,
    "killzone_p": compute_killzone_prob,
    "premium_discount": compute_premium_discount,
}


class PerceptionPipeline:
    """Run hint detectors on bars[0:t+1], compress, and gate."""

    __slots__ = ("_compressor", "_gate", "_computers")

    def __init__(
        self,
        *,
        context_dims: int = 16,
        gate: FeatureGate | None = None,
        computers: dict[str, HintFn] | None = None,
    ) -> None:
        self._compressor = PerceptionCompressor(context_dims=context_dims)
        self._gate = gate or FeatureGate()
        self._computers = computers or dict(DEFAULT_HINT_COMPUTERS)

    @property
    def compressor(self) -> PerceptionCompressor:
        return self._compressor

    @property
    def gate(self) -> FeatureGate:
        return self._gate

    def compute_hints(self, bars: Sequence[KlineRow], t: int) -> dict[str, HintEnvelope]:
        view = visible_bars(bars, t)
        envelopes: dict[str, HintEnvelope] = {}
        for name, fn in self._computers.items():
            envelopes[name] = fn(view)
        return envelopes

    def step(self, bars: Sequence[KlineRow], t: int, config: dict | None = None) -> list[float]:
        cfg = config or {}
        observation = cfg.get("observation", cfg)
        context_dims = int(observation.get("context_dims", self._compressor.context_dims))
        if context_dims != self._compressor.context_dims:
            self._compressor = PerceptionCompressor(context_dims=context_dims)

        self._gate.update(GateConfig.from_config(cfg))
        envelopes = self.compute_hints(bars, t)
        hint_values = {name: env.value for name, env in envelopes.items()}
        raw = self._compressor.compress(visible_bars(bars, t), hint_values)
        return self._gate.apply(raw, context_dims=context_dims)
