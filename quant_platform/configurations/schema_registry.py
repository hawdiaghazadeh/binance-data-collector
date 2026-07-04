"""Configuration schema registry (Phase 21)."""

from __future__ import annotations

from typing import Any

from quant_platform.core.config import validate_plugin_config

DEFAULT_PLATFORM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "symbols": {"type": "array"},
        "timeframes": {"type": "array"},
        "plugins": {"type": "object"},
        "downloader": {"type": "object"},
        "importer": {"type": "object"},
        "database": {"type": "object"},
    },
}

PLUGIN_CONFIG_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string"},
        "enabled": {"type": "boolean"},
        "config": {"type": "object"},
    },
}


class SchemaRegistry:
    def __init__(self) -> None:
        self._schemas: dict[str, dict[str, Any]] = {
            "platform": DEFAULT_PLATFORM_SCHEMA,
            "plugin": PLUGIN_CONFIG_SCHEMA,
        }

    def register(self, name: str, schema: dict[str, Any]) -> None:
        self._schemas[name] = schema

    def get(self, name: str) -> dict[str, Any]:
        if name not in self._schemas:
            raise KeyError(f"Unknown configuration schema: {name}")
        return self._schemas[name]

    def validate(self, config: dict[str, Any], schema_name: str) -> dict[str, Any]:
        schema = self.get(schema_name)
        return validate_plugin_config(config, schema)


def resolve_schema_name(config: dict[str, Any], default: str = "platform") -> str:
    schema_name = config.get("$schema")
    if isinstance(schema_name, str) and schema_name:
        return schema_name
    if "name" in config and "config" in config:
        return "plugin"
    return default
