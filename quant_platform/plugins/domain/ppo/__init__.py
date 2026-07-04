"""Reference domain plugin: ppo."""

from __future__ import annotations

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("ppo", "platform.rl_algorithms")


class PpoAlgorithm:

    def train_step(self, batch: list) -> dict:
        return {"loss": 0.0, "batch_size": len(batch)}


def factory(**kwargs) -> PpoAlgorithm:
    return PpoAlgorithm()


attach_factory_metadata(factory, PLUGIN_METADATA)
