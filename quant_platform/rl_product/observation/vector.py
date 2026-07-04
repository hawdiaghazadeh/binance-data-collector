"""Fixed-size observation vector (float32-compatible)."""

from __future__ import annotations

import array
import hashlib
import json
from dataclasses import dataclass
from typing import Any

from quant_platform.rl_product.observation.schema import ObservationSchema


@dataclass(frozen=True, slots=True)
class ObservationVector:
    """Schema-tagged observation; stored as float32 array."""

    data: array.array
    schema: ObservationSchema
    step_index: int

    def __post_init__(self) -> None:
        if self.data.typecode != "f":
            raise TypeError("data must be float32 array.array('f')")
        if len(self.data) != self.schema.obs_dim:
            raise ValueError(f"obs length {len(self.data)} != obs_dim {self.schema.obs_dim}")

    @classmethod
    def from_values(cls, values: list[float], *, schema: ObservationSchema, step_index: int) -> ObservationVector:
        finite = [0.0 if (v != v or abs(v) == float("inf")) else float(v) for v in values]
        buf = array.array("f", finite)
        return cls(data=buf, schema=schema, step_index=step_index)

    def to_list(self) -> list[float]:
        return list(self.data)

    def block(self, name: str) -> list[float]:
        sl = self.schema.block_slices()[name]
        return list(self.data[sl])

    @property
    def schema_hash(self) -> str:
        payload = {
            "obs_dim": self.schema.obs_dim,
            "context_dims": self.schema.context_dims,
            "portfolio_dims": self.schema.portfolio_dims,
            "reserved_dims": self.schema.reserved_dims,
            "schema_version": self.schema.schema_version,
        }
        text = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def metadata(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema.schema_version,
            "schema_hash": self.schema_hash,
            "obs_dim": self.schema.obs_dim,
            "step_index": self.step_index,
        }
