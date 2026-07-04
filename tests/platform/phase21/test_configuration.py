"""Phase 21 configuration tests."""

from __future__ import annotations

import json

import pytest
import yaml

from quant_platform.configurations import (
    ConfigurationPipelineBuilder,
    SchemaRegistry,
    deep_merge,
    load_config_file,
    register_configuration_plugins,
    resolve_inheritance,
    validate_configuration,
)
from quant_platform.core.config import ConfigValidationError
from quant_platform.core.context import DataEnvelope, PipelineContext
from quant_platform.core.manager import PluginManager


class TestConfigurationCompute:
    def test_deep_merge_nested(self):
        base = {"plugins": {"a": {"enabled": True, "config": {"x": 1}}, "b": 2}}
        override = {"plugins": {"a": {"config": {"y": 2}}, "c": 3}}
        merged = deep_merge(base, override)
        assert merged["plugins"]["a"]["enabled"] is True
        assert merged["plugins"]["a"]["config"] == {"x": 1, "y": 2}
        assert merged["plugins"]["b"] == 2
        assert merged["plugins"]["c"] == 3

    def test_resolve_inheritance(self, tmp_path):
        base_path = tmp_path / "base.yaml"
        child_path = tmp_path / "child.yaml"
        yaml.safe_dump({"symbols": ["BTCUSDT"], "timeframes": ["1h"]}, base_path.open("w"))
        yaml.safe_dump(
            {"extends": "base.yaml", "symbols": ["ETHUSDT"], "plugins": {"rule_based": {"enabled": True}}},
            child_path.open("w"),
        )
        resolved = resolve_inheritance(load_config_file(child_path), base_dir=tmp_path)
        assert resolved["symbols"] == ["ETHUSDT"]
        assert resolved["timeframes"] == ["1h"]
        assert resolved["plugins"]["rule_based"]["enabled"] is True

    def test_load_json_and_toml(self, tmp_path):
        json_path = tmp_path / "app.json"
        json_path.write_text(json.dumps({"symbols": ["BTCUSDT"]}), encoding="utf-8")
        assert load_config_file(json_path)["symbols"] == ["BTCUSDT"]

        toml_path = tmp_path / "app.toml"
        toml_path.write_text('[database]\nhost = "localhost"\n', encoding="utf-8")
        assert load_config_file(toml_path)["database"]["host"] == "localhost"

    def test_schema_registry_validates_plugin_config(self):
        registry = SchemaRegistry()
        validated = registry.validate({"name": "rule_based", "enabled": True}, "plugin")
        assert validated["name"] == "rule_based"

    def test_schema_registry_rejects_missing_required(self):
        registry = SchemaRegistry()
        with pytest.raises(ConfigValidationError, match="Missing required"):
            registry.validate({"enabled": True}, "plugin")

    def test_validate_configuration_with_custom_schema(self):
        registry = SchemaRegistry()
        registry.register(
            "custom",
            {"type": "object", "required": ["mode"], "properties": {"mode": {"type": "string"}}},
        )
        result = validate_configuration({"mode": "paper"}, registry, schema_name="custom")
        assert result["mode"] == "paper"


class TestConfigurationRegistry:
    def test_schema_config_plugin(self, tmp_path):
        manager = PluginManager()
        register_configuration_plugins(manager)
        plugin = manager.get("platform.configurations", "schema_config")
        config_path = tmp_path / "platform.yaml"
        yaml.safe_dump({"symbols": ["BTCUSDT"], "timeframes": ["1h"]}, config_path.open("w"))
        validated = plugin.load_and_validate(config_path)
        assert validated["symbols"] == ["BTCUSDT"]

    def test_schema_config_inheritance_via_plugin(self, tmp_path):
        manager = PluginManager()
        register_configuration_plugins(manager)
        plugin = manager.get("platform.configurations", "schema_config")
        base_path = tmp_path / "base.yaml"
        child_path = tmp_path / "child.yaml"
        yaml.safe_dump({"symbols": ["BTCUSDT"]}, base_path.open("w"))
        yaml.safe_dump({"extends": "base.yaml", "timeframes": ["4h"]}, child_path.open("w"))
        validated = plugin.load_and_validate(child_path)
        assert validated["symbols"] == ["BTCUSDT"]
        assert validated["timeframes"] == ["4h"]

    def test_configuration_pipeline_builder(self, tmp_path):
        manager = PluginManager()
        register_configuration_plugins(manager)
        builder = ConfigurationPipelineBuilder(manager)
        config_path = tmp_path / "pipeline.yaml"
        yaml.safe_dump({"symbols": ["ETHUSDT"]}, config_path.open("w"))
        ctx = PipelineContext()
        ctx.emit(
            DataEnvelope(
                type_key="configuration_request",
                payload={"path": str(config_path)},
            )
        )
        graph = builder.build_graph()
        graph.execute(ctx)
        validated = ctx.require("validated_config").payload
        assert validated["symbols"] == ["ETHUSDT"]
