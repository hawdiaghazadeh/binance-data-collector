"""Configuration inheritance helpers (Phase 21)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quant_platform.configurations.loader import load_config_file


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in {"extends", "inherits"}:
            continue
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def resolve_inheritance(
    config: dict[str, Any],
    *,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    working = dict(config)
    parents = working.pop("extends", None)
    if parents is None:
        parents = working.pop("inherits", None)
    if not parents:
        return working

    if isinstance(parents, str):
        parents = [parents]

    merged: dict[str, Any] = {}
    root = base_dir or Path(".")
    for parent in parents:
        parent_path = Path(parent)
        if not parent_path.is_absolute():
            parent_path = root / parent_path
        parent_config = load_config_file(parent_path)
        parent_config = resolve_inheritance(parent_config, base_dir=parent_path.parent)
        merged = deep_merge(merged, parent_config)

    return deep_merge(merged, working)
