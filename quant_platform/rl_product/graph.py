"""Frozen RL product graph — compile once at startup (G33+)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from quant_platform.rl_product.env.reward import RewardEngine
from quant_platform.rl_product.observation.builder import PriceActionObservationBuilder
from quant_platform.rl_product.observation.schema import ObservationSchema
from quant_platform.rl_product.observation.vector import ObservationVector
from quant_platform.rl_product.perception.pipeline import PerceptionPipeline
from quant_platform.rl_product.perception._helpers import HintEnvelope
from quant_platform.rl_product.env.portfolio import PortfolioTracker
from services.shared.models import KlineRow


class RLProductGraph:
    """Deterministic compile target; PERCEPTION → OBSERVATION → REWARD handlers frozen."""

    __slots__ = (
        "config",
        "schema_hash",
        "_perception",
        "_observation",
        "_reward",
    )

    def __init__(
        self,
        config: dict[str, Any],
        *,
        schema_hash: str,
        perception: PerceptionPipeline,
        observation: PriceActionObservationBuilder,
        reward: RewardEngine,
    ) -> None:
        self.config = config
        self.schema_hash = schema_hash
        self._perception = perception
        self._observation = observation
        self._reward = reward

    @classmethod
    def compile(cls, config: dict[str, Any]) -> RLProductGraph:
        payload = json.dumps(config, sort_keys=True, default=str)
        schema_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
        schema = ObservationSchema.from_config(config)
        schema.validate_budget()
        perception = PerceptionPipeline(context_dims=schema.context_dims)
        observation = PriceActionObservationBuilder.from_config(config, perception=perception)
        reward = RewardEngine.from_config(config)
        return cls(
            config,
            schema_hash=schema_hash,
            perception=perception,
            observation=observation,
            reward=reward,
        )

    @property
    def perception(self) -> PerceptionPipeline:
        return self._perception

    @property
    def observation(self) -> PriceActionObservationBuilder:
        return self._observation

    @property
    def reward_engine(self) -> RewardEngine:
        return self._reward

    def build_observation(
        self,
        bars: tuple[KlineRow, ...] | list[KlineRow],
        t: int,
        portfolio: PortfolioTracker,
        *,
        price: float | None = None,
    ) -> ObservationVector:
        bar_price = price if price is not None else bars[t].close
        return self._observation.build(
            bars,
            t,
            portfolio=portfolio.to_dict(bar_price),
            config=self.config,
        )

    def run_phases(
        self,
        bars: tuple[KlineRow, ...] | list[KlineRow],
        t: int,
        portfolio: PortfolioTracker,
        *,
        price: float | None = None,
    ) -> tuple[ObservationVector, dict[str, HintEnvelope]]:
        hints = self._perception.compute_hints(bars, t)
        bar_price = price if price is not None else bars[t].close
        obs = self.build_observation(bars, t, portfolio, price=bar_price)
        return obs, hints

    def compute_reward(
        self,
        *,
        step_pnl: float,
        portfolio: PortfolioTracker,
        hint_conf: float = 0.0,
    ) -> tuple[float, dict[str, float]]:
        return self._reward.compute(step_pnl=step_pnl, portfolio=portfolio, hint_conf=hint_conf)
