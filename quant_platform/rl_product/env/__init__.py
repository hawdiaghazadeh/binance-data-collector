"""RL product environment layer (G33)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from quant_platform.rl_product.env.execution import SimpleExecutionModel
from quant_platform.rl_product.env.reward import RewardEngine

if TYPE_CHECKING:
    from quant_platform.rl_product.env.bridge import RLEnvironmentBridge
    from quant_platform.rl_product.env.gym_wrapper import GymnasiumRLEnv

__all__ = [
    "GymnasiumRLEnv",
    "RLEnvironmentBridge",
    "RewardEngine",
    "SimpleExecutionModel",
]


def __getattr__(name: str):
    if name == "RLEnvironmentBridge":
        from quant_platform.rl_product.env.bridge import RLEnvironmentBridge

        return RLEnvironmentBridge
    if name == "GymnasiumRLEnv":
        from quant_platform.rl_product.env.gym_wrapper import GymnasiumRLEnv

        return GymnasiumRLEnv
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
