"""Schema-driven configuration plugin (Phase 21)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quant_platform.configurations.schema_registry import SchemaRegistry
from quant_platform.configurations.validate import load_and_validate_configuration, validate_configuration
from quant_platform.core.plugin import PluginMetadata

PLUGIN_METADATA = PluginMetadata(
    name="schema_config",
    version="1.0.0",
    platform_version_compatibility=">=1.0.0,<2.0.0",
    description="Schema registry with YAML/JSON/TOML load and config inheritance",
    input_types=["configuration_request"],
    output_types=["validated_config"],
    registry_group="platform.configurations",
)


class SchemaConfiguration:
    def __init__(self, registry: SchemaRegistry | None = None) -> None:
        self._registry = registry or SchemaRegistry()

    def validate(self, config: dict[str, Any], schema_name: str | None = None) -> dict[str, Any]:
        return validate_configuration(config, self._registry, schema_name=schema_name)

    def validate_with_base(
        self,
        config: dict[str, Any],
        *,
        schema_name: str | None = None,
        base_dir: Path | None = None,
    ) -> dict[str, Any]:
        return validate_configuration(
            config,
            self._registry,
            schema_name=schema_name,
            base_dir=base_dir,
        )

    def load_and_validate(self, path: str | Path, schema_name: str | None = None) -> dict[str, Any]:
        return load_and_validate_configuration(path, self._registry, schema_name=schema_name)

    def register_schema(self, name: str, schema: dict[str, Any]) -> None:
        self._registry.register(name, schema)


def factory(**kwargs) -> SchemaConfiguration:
    registry = kwargs.get("registry")
    return SchemaConfiguration(registry=registry if isinstance(registry, SchemaRegistry) else None)


factory.PLUGIN_METADATA = PLUGIN_METADATA  # type: ignore[attr-defined]
