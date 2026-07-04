"""RTM zone flip probability hint plugin."""

from __future__ import annotations

from quant_platform.plugins.rl._hint_plugin import build_hint_plugin
from quant_platform.rl_product.perception.rtm import compute_flip_prob

PLUGIN_METADATA, factory = build_hint_plugin(
    name="rtm_flip_prob",
    family="rtm",
    hint_name="flip_p",
    description="Supply/demand flip probability after sweep and reclaim",
    compute=compute_flip_prob,
    default_options={"lookback": 15},
)

__all__ = ["PLUGIN_METADATA", "factory"]
