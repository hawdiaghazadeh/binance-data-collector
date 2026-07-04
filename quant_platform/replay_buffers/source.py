"""Replay buffer transition helpers (Phase 15)."""

from __future__ import annotations

from typing import Any


def normalize_transition(transition: Any) -> dict[str, Any]:
    if isinstance(transition, dict):
        return {
            "state": transition.get("state"),
            "action": transition.get("action"),
            "reward": float(transition.get("reward", 0.0)),
            "next_state": transition.get("next_state"),
            "done": bool(transition.get("done", False)),
        }
    return {
        "state": transition,
        "action": None,
        "reward": 0.0,
        "next_state": None,
        "done": False,
    }
