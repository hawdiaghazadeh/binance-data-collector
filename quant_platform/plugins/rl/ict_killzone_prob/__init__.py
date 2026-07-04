"""ICT killzone probability hint plugin."""

from __future__ import annotations

from quant_platform.plugins.rl._hint_plugin import build_hint_plugin
from quant_platform.rl_product.perception.ict import compute_killzone_prob

PLUGIN_METADATA, factory = build_hint_plugin(
    name="ict_killzone_prob",
    family="ict",
    hint_name="killzone_p",
    description="ICT killzone overlap probability from bar timestamp",
    compute=compute_killzone_prob,
)

__all__ = ["PLUGIN_METADATA", "factory"]
