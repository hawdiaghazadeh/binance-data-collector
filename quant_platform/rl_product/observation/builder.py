"""Price-action-first observation builder (G32)."""

from __future__ import annotations

from typing import Any, Sequence

from quant_platform.rl_product.observation.portfolio import build_portfolio_block
from quant_platform.rl_product.observation.price_action import build_price_action_block
from quant_platform.rl_product.observation.schema import ObservationSchema
from quant_platform.rl_product.observation.vector import ObservationVector
from quant_platform.rl_product.perception.pipeline import PerceptionPipeline
from services.shared.models import KlineRow


class PriceActionObservationBuilder:
    """Assemble price (≥70%), context, portfolio, and reserved blocks."""

    __slots__ = ("_schema", "_perception")

    def __init__(
        self,
        schema: ObservationSchema,
        *,
        perception: PerceptionPipeline | None = None,
    ) -> None:
        schema.validate_budget()
        self._schema = schema
        self._perception = perception or PerceptionPipeline(context_dims=schema.context_dims)

    @property
    def schema(self) -> ObservationSchema:
        return self._schema

    @classmethod
    def from_config(cls, config: dict, *, perception: PerceptionPipeline | None = None) -> PriceActionObservationBuilder:
        schema = ObservationSchema.from_config(config)
        return cls(schema, perception=perception)

    def validate_budget(self) -> None:
        self._schema.validate_budget()

    def build(
        self,
        bars: Sequence[KlineRow],
        t: int,
        *,
        portfolio: dict[str, Any] | None = None,
        config: dict | None = None,
    ) -> ObservationVector:
        if t < 0 or t >= len(bars):
            raise ValueError("t out of range")

        price = build_price_action_block(
            bars,
            t,
            price_dims=self._schema.price_dims,
            window=self._schema.window,
        )
        context = self._build_context(bars, t, config=config)
        portfolio_vec = build_portfolio_block(portfolio, portfolio_dims=self._schema.portfolio_dims)
        reserved = [0.0] * self._schema.reserved_dims

        values = price + context + portfolio_vec + reserved
        if len(values) != self._schema.obs_dim:
            raise RuntimeError(f"observation length mismatch: {len(values)} != {self._schema.obs_dim}")

        return ObservationVector.from_values(values, schema=self._schema, step_index=t)

    def _build_context(
        self,
        bars: Sequence[KlineRow],
        t: int,
        *,
        config: dict | None,
    ) -> list[float]:
        cfg = config or {}
        context = self._perception.step(bars, t, cfg)
        dims = self._schema.context_dims
        if len(context) < dims:
            context = context + [0.0] * (dims - len(context))
        return context[:dims]

    def context_block_zeros(self, bars: Sequence[KlineRow], t: int, *, config: dict | None = None) -> bool:
        obs = self.build(bars, t, config=config)
        return all(v == 0.0 for v in obs.block("context"))
