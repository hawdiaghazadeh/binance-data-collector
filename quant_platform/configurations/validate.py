"""Configuration validation helpers (Phase 21)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quant_platform.configurations.inheritance import resolve_inheritance
from quant_platform.configurations.loader import load_config_file
from quant_platform.configurations.schema_registry import SchemaRegistry, resolve_schema_name


def validate_configuration(
    config: dict[str, Any],
    registry: SchemaRegistry,
    *,
    schema_name: str | None = None,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    resolved = resolve_inheritance(config, base_dir=base_dir)
    name = schema_name or resolve_schema_name(resolved)
    return registry.validate(resolved, name)


def load_and_validate_configuration(
    path: str | Path,
    registry: SchemaRegistry,
    *,
    schema_name: str | None = None,
) -> dict[str, Any]:
    file_path = Path(path)
    config = load_config_file(file_path)
    return validate_configuration(
        config,
        registry,
        schema_name=schema_name,
        base_dir=file_path.parent,
    )
