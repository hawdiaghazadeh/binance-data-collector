"""Reference domain plugin: schema_config."""

from __future__ import annotations

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("schema_config", "platform.configurations")


class SchemaConfiguration:

    def validate(self, config: dict) -> dict:
        return config


def factory(**kwargs) -> SchemaConfiguration:
    return SchemaConfiguration()


attach_factory_metadata(factory, PLUGIN_METADATA)
