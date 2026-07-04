"""Plugin config validation against JSON Schema."""

from __future__ import annotations

from typing import Any


class ConfigValidationError(Exception):
    """Raised when plugin config fails validation."""


def validate_plugin_config(config: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Validate config against a JSON Schema subset (required fields + types)."""
    if not schema:
        return config

    required = schema.get("required", [])
    properties = schema.get("properties", {})

    for field in required:
        if field not in config:
            raise ConfigValidationError(f"Missing required config field: {field}")

    for key, value in config.items():
        if key in properties:
            expected = properties[key].get("type")
            if expected and not _type_matches(value, expected):
                raise ConfigValidationError(
                    f"Config field '{key}' expected type {expected}, got {type(value).__name__}"
                )

    return config


def _type_matches(value: Any, expected: str) -> bool:
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    py_type = type_map.get(expected)
    if py_type is None:
        return True
    return isinstance(value, py_type)
