"""Reference domain plugin: spot_env."""

from __future__ import annotations

from typing import Any

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("spot_env", "platform.environments")


class SpotEnvironment:

    def reset(self) -> dict:
        return {"balance": 10000.0}

    def step(self, action: Any) -> tuple[dict, float, bool, dict]:
        return {"balance": 10000.0}, 0.0, False, {}


def factory(**kwargs) -> SpotEnvironment:
    return SpotEnvironment()


attach_factory_metadata(factory, PLUGIN_METADATA)
