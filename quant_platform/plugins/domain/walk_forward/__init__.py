"""Reference domain plugin: walk_forward."""

from __future__ import annotations

from typing import Any

from quant_platform.plugins.domain._helpers import attach_factory_metadata, reference_meta

PLUGIN_METADATA = reference_meta("walk_forward", "platform.evaluation_pipelines")


class WalkForwardEval:

    def evaluate(self, model: Any, data: Any) -> dict:
        return {"score": 0.0}


def factory(**kwargs) -> WalkForwardEval:
    return WalkForwardEval()


attach_factory_metadata(factory, PLUGIN_METADATA)
