"""RL product registry singleton (G30+)."""

from __future__ import annotations

from quant_platform.core.registry import BaseRegistry
from quant_platform.rl_product.registry import RL_GROUP

rl_registry = BaseRegistry.get_instance(RL_GROUP)

__all__ = ["RL_GROUP", "rl_registry"]
