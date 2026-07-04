"""Frozen RL product graph — compile once at startup (expanded G31+)."""

from __future__ import annotations

import hashlib
import json
from typing import Any


class RLProductGraph:
    """Deterministic compile target; no runtime plugin discovery in training loop."""

    __slots__ = ("config", "schema_hash")

    def __init__(self, config: dict[str, Any], *, schema_hash: str) -> None:
        self.config = config
        self.schema_hash = schema_hash

    @classmethod
    def compile(cls, config: dict[str, Any]) -> RLProductGraph:
        payload = json.dumps(config, sort_keys=True, default=str)
        schema_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return cls(config, schema_hash=schema_hash)
