"""Configuration file loading (Phase 21)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_config_file(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    suffix = file_path.suffix.lower()
    text = file_path.read_text(encoding="utf-8")

    if suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(text)
    elif suffix == ".json":
        payload = json.loads(text)
    elif suffix == ".toml":
        import tomllib

        payload = tomllib.loads(text)
    else:
        raise ValueError(f"Unsupported configuration format: {suffix}")

    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ValueError("Configuration root must be an object")
    return dict(payload)
