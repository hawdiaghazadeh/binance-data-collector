"""Deterministic episode replay for train/deploy parity (G36)."""

from __future__ import annotations

import random
from typing import Any

from quant_platform.rl_product.env.bridge import RLEnvironmentBridge
from quant_platform.rl_product.graph import RLProductGraph
from quant_platform.rl_product.protocols import Episode


def replay_observation_sequence(
    episode: Episode,
    graph: RLProductGraph,
    *,
    seed: int | None = None,
    max_steps: int | None = None,
) -> list[list[float]]:
    """Replay fixed actions from seed and return observation sequence."""
    rng = random.Random(seed)
    training = graph.config.get("training", graph.config)
    env = RLEnvironmentBridge(
        episode,
        graph,
        market=str(training.get("market", "futures")),
        initial_equity=float(training.get("initial_equity", 10_000.0)),
        leverage=float(training.get("leverage", 5.0)),
        config=graph.config,
    )
    obs, _ = env.reset()
    sequence = [list(obs)]
    done = False
    steps = 0
    limit = max_steps if max_steps is not None else len(episode.bars) - 1

    while not done and steps < limit:
        action = rng.uniform(-0.5, 0.5)
        obs, _reward, done, _info = env.step(action)
        sequence.append(list(obs))
        steps += 1
    return sequence


def sequences_equal(a: list[list[float]], b: list[list[float]], *, tol: float = 1e-6) -> bool:
    if len(a) != len(b):
        return False
    for row_a, row_b in zip(a, b, strict=True):
        if len(row_a) != len(row_b):
            return False
        for left, right in zip(row_a, row_b, strict=True):
            if abs(left - right) > tol:
                return False
    return True


def assert_deterministic_replay(
    episode: Episode,
    graph: RLProductGraph,
    *,
    seed: int = 42,
) -> dict[str, Any]:
    first = replay_observation_sequence(episode, graph, seed=seed)
    second = replay_observation_sequence(episode, graph, seed=seed)
    return {
        "deterministic": sequences_equal(first, second),
        "steps": len(first),
        "obs_dim": len(first[0]) if first else 0,
    }
