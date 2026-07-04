"""Reference domain plugin: standard_rl_train."""

from __future__ import annotations

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("standard_rl_train", "platform.training_pipelines")


class StandardRlTraining:

    def run(self, config: dict) -> dict:
        return {"status": "completed", "epochs": config.get("epochs", 1)}


def factory(**kwargs) -> StandardRlTraining:
    return StandardRlTraining()


attach_factory_metadata(factory, PLUGIN_METADATA)
