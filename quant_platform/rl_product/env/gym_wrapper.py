"""Gymnasium-compatible wrapper for RL environment bridge."""

from __future__ import annotations

from typing import Any, SupportsFloat

from quant_platform.rl_product.env.bridge import RLEnvironmentBridge
from quant_platform.rl_product.observation.schema import ObservationSchema


class GymnasiumRLEnv:
    """Thin Gymnasium Env adapter over RLEnvironmentBridge."""

    metadata = {"render_modes": []}

    def __init__(self, bridge: RLEnvironmentBridge) -> None:
        self._bridge = bridge
        schema = ObservationSchema.from_config(bridge.graph.config)
        self._obs_dim = schema.obs_dim
        self._init_spaces()

    @property
    def bridge(self) -> RLEnvironmentBridge:
        return self._bridge

    def _init_spaces(self) -> None:
        try:
            from gymnasium import spaces
        except ImportError as exc:
            raise ImportError("gymnasium is required for GymnasiumRLEnv") from exc

        self.observation_space = spaces.Box(
            low=-5.0,
            high=5.0,
            shape=(self._obs_dim,),
            dtype="float32",
        )
        if self._bridge.market == "spot":
            self.action_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype="float32")
        else:
            self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype="float32")

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
        if seed is not None:
            try:
                import random

                random.seed(seed)
            except ImportError:
                pass
        obs, info = self._bridge.reset()
        return obs, info

    def step(self, action: SupportsFloat | list[float]):
        if isinstance(action, (list, tuple)):
            value = float(action[0])
        else:
            value = float(action)
        obs, reward, terminated, info = self._bridge.step(value)
        return obs, reward, terminated, False, info

    def close(self) -> None:
        return None
