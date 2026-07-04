"""Standard RL training loop (Phase 15)."""

from __future__ import annotations

from typing import Any, Protocol


class ReplayBufferLike(Protocol):
    def add(self, transition: Any) -> None: ...
    def sample(self, batch_size: int) -> list[Any]: ...
    def __len__(self) -> int: ...


class RLAlgorithmLike(Protocol):
    def train_step(self, batch: list[Any]) -> dict[str, Any]: ...


def run_training_loop(
    config: dict[str, Any],
    *,
    buffer: ReplayBufferLike,
    algorithm: RLAlgorithmLike,
) -> dict[str, Any]:
    transitions = config.get("transitions", [])
    if isinstance(transitions, list):
        for transition in transitions:
            buffer.add(transition)

    epochs = int(config.get("epochs", 1))
    batch_size = int(config.get("batch_size", 32))
    steps: list[dict[str, Any]] = []

    for _ in range(epochs):
        batch = buffer.sample(batch_size)
        steps.append(algorithm.train_step(batch))

    return {
        "status": "completed",
        "epochs": epochs,
        "batch_size": batch_size,
        "buffer_size": len(buffer),
        "steps": steps,
        "final_loss": float(steps[-1].get("loss", 0.0)) if steps else 0.0,
    }
