"""Configuration pipeline builder — Phase 21."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.execution_graph import CompiledExecutionGraph, ExecutionStep
from quant_platform.core.manager import PluginManager
from quant_platform.registries.domain import CONFIGURATION_GROUP


class ConfigurationPipelineBuilder:
    def __init__(self, manager: PluginManager) -> None:
        self._manager = manager

    def validate(
        self,
        ctx: PipelineContext,
        config: dict[str, Any],
        *,
        schema_name: str | None = None,
        configuration_name: str = "schema_config",
        base_dir: Path | None = None,
    ) -> dict[str, Any]:
        plugin = self._manager.get(CONFIGURATION_GROUP, configuration_name)
        if base_dir is not None and hasattr(plugin, "validate_with_base"):
            validated = plugin.validate_with_base(config, schema_name=schema_name, base_dir=base_dir)
        elif schema_name:
            validated = plugin.validate(config, schema_name=schema_name)
        else:
            validated = plugin.validate(config)
        ctx.emit(DataEnvelope(type_key="validated_config", payload=validated))
        return validated

    def load_file(
        self,
        ctx: PipelineContext,
        path: str | Path,
        *,
        schema_name: str | None = None,
        configuration_name: str = "schema_config",
    ) -> dict[str, Any]:
        plugin = self._manager.get(CONFIGURATION_GROUP, configuration_name)
        if hasattr(plugin, "load_and_validate"):
            validated = plugin.load_and_validate(path, schema_name=schema_name)
        else:
            from quant_platform.configurations.loader import load_config_file

            validated = plugin.validate(load_config_file(path), schema_name=schema_name)
        ctx.emit(DataEnvelope(type_key="validated_config", payload=validated))
        return validated

    def build_graph(self, *, configuration_name: str = "schema_config") -> CompiledExecutionGraph:
        def handler(ctx: PipelineContext) -> None:
            request = ctx.require("configuration_request").payload
            if "path" in request:
                self.load_file(
                    ctx,
                    request["path"],
                    schema_name=request.get("schema_name"),
                    configuration_name=configuration_name,
                )
            else:
                self.validate(
                    ctx,
                    dict(request.get("config", {})),
                    schema_name=request.get("schema_name"),
                    configuration_name=configuration_name,
                    base_dir=Path(request["base_dir"]) if request.get("base_dir") else None,
                )

        return CompiledExecutionGraph(
            (
                ExecutionStep(
                    plugin_name="configuration",
                    handler=handler,
                    registry_group=CONFIGURATION_GROUP,
                ),
            )
        )


def register_configuration_plugins(manager: PluginManager) -> None:
    from quant_platform.plugins.domain.schema_config import PLUGIN_METADATA as SCHEMA_META
    from quant_platform.plugins.domain.schema_config import factory as schema_factory

    reg = manager.registry(CONFIGURATION_GROUP)
    if SCHEMA_META.name not in {m.name for m in reg.list_plugins()}:
        reg.register(SCHEMA_META, schema_factory)
