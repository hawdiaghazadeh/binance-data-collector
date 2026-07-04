"""Observation schema v1.0 — block budget enforcement."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ObservationSchema:
    obs_dim: int = 128
    context_dims: int = 16
    portfolio_dims: int = 14
    reserved_dims: int = 8
    price_action_min_ratio: float = 0.70
    context_dims_max: int = 32
    schema_version: str = "1.0"
    window: int = 64

    @property
    def price_dims(self) -> int:
        return self.obs_dim - self.context_dims - self.portfolio_dims - self.reserved_dims

    @classmethod
    def from_config(cls, config: dict) -> ObservationSchema:
        obs = config.get("observation", config)
        return cls(
            obs_dim=int(obs.get("dim", obs.get("obs_dim", 128))),
            context_dims=int(obs.get("context_dims", 16)),
            portfolio_dims=int(obs.get("portfolio_dims", 14)),
            reserved_dims=int(obs.get("reserved_dims", 8)),
            price_action_min_ratio=float(obs.get("price_action_min_ratio", 0.70)),
            context_dims_max=int(obs.get("context_dims_max", 32)),
            schema_version=str(obs.get("schema_version", "1.0")),
            window=int(obs.get("window", 64)),
        )

    def validate_budget(self) -> None:
        if self.schema_version != "1.0":
            raise ValueError(f"unsupported schema_version: {self.schema_version}")
        if self.obs_dim < 32:
            raise ValueError("obs_dim must be >= 32")
        if self.context_dims < 1 or self.context_dims > self.context_dims_max:
            raise ValueError(f"context_dims must be in [1, {self.context_dims_max}]")
        if self.context_dims > 0.25 * self.obs_dim:
            raise ValueError("context_dims exceeds 25% of obs_dim")
        min_price = int(self.price_action_min_ratio * self.obs_dim)
        if self.price_dims < min_price:
            raise ValueError(
                f"price_dims {self.price_dims} < {min_price} "
                f"({self.price_action_min_ratio:.0%} of obs_dim)"
            )
        total = self.price_dims + self.context_dims + self.portfolio_dims + self.reserved_dims
        if total != self.obs_dim:
            raise ValueError(f"block dims sum to {total}, expected obs_dim {self.obs_dim}")

    def block_slices(self) -> dict[str, slice]:
        start = 0
        price = slice(start, start := start + self.price_dims)
        context = slice(start, start := start + self.context_dims)
        portfolio = slice(start, start := start + self.portfolio_dims)
        reserved = slice(start, start + self.reserved_dims)
        return {
            "price_action": price,
            "context": context,
            "portfolio": portfolio,
            "reserved": reserved,
        }
