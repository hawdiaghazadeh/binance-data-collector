"""Policy inference — checkpoint load with graph hash validation (G37)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quant_platform.rl_product.agent.checkpoint import load_checkpoint
from quant_platform.rl_product.agent.network import ActorCriticModule
from quant_platform.rl_product.graph import RLProductGraph
from quant_platform.rl_product.observation.schema import ObservationSchema


class GraphHashMismatchError(ValueError):
    """Raised when deploy graph hash does not match training checkpoint."""


@dataclass(slots=True)
class PolicyInferenceEngine:
    """Frozen-graph policy inference for train/deploy parity."""

    graph: RLProductGraph
    model: ActorCriticModule
    metadata: dict[str, Any]

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: str | Path,
        config: dict[str, Any],
        *,
        strict_hash: bool = True,
        map_location: str | None = "cpu",
    ) -> PolicyInferenceEngine:
        graph = RLProductGraph.compile(config)
        model, metadata = load_checkpoint(checkpoint_path, config=config, map_location=map_location)
        expected = str(metadata.get("graph_schema_hash", ""))
        if strict_hash and expected and graph.schema_hash != expected:
            raise GraphHashMismatchError(
                f"graph schema hash mismatch: deploy={graph.schema_hash} checkpoint={expected}"
            )
        return cls(graph=graph, model=model, metadata=metadata)

    @property
    def graph_schema_hash(self) -> str:
        return self.graph.schema_hash

    @property
    def schema(self) -> ObservationSchema:
        return self.graph.observation.schema

    def act(
        self,
        observation: list[float],
        *,
        deterministic: bool = True,
        zero_context: bool = False,
        zero_price: bool = False,
    ) -> float:
        import torch

        obs = torch.as_tensor(observation, dtype=torch.float32).unsqueeze(0)
        action, _, _ = self.model.act(
            obs,
            deterministic=deterministic,
            zero_context=zero_context,
            zero_price=zero_price,
        )
        return float(action.squeeze().detach())

    def build_observation(
        self,
        bars: list,
        t: int,
        portfolio: dict[str, Any],
        *,
        price: float | None = None,
    ) -> list[float]:
        vector = self.graph.build_observation(bars, t, _portfolio_from_dict(portfolio), price=price)
        return vector.to_list()


def _portfolio_from_dict(data: dict[str, Any]):
    from quant_platform.rl_product.env.portfolio import PortfolioTracker

    market = str(data.get("market", "spot"))
    initial = float(data.get("initial_equity", data.get("equity", 10_000.0)))
    leverage = float(data.get("leverage", 1.0))
    tracker = PortfolioTracker.initial(market=market, initial_equity=initial, leverage=leverage)
    tracker.cash = float(data.get("cash", initial))
    tracker.position = float(data.get("position", 0.0))
    tracker.entry_price = float(data.get("entry_price", 0.0))
    tracker.peak_equity = float(data.get("peak_equity", initial))
    tracker._prev_equity = float(data.get("equity", initial))  # noqa: SLF001
    tracker.trade_count = int(data.get("trade_count", 0))
    return tracker
