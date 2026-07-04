"""RTM supply/demand strength hint plugin."""

from __future__ import annotations

from quant_platform.plugins.rl._hint_plugin import build_hint_plugin
from quant_platform.rl_product.perception.rtm import compute_sd_strength

PLUGIN_METADATA, factory = build_hint_plugin(
    name="rtm_sd_strength",
    family="rtm",
    hint_name="sd_strength",
    description="Supply/demand zone touch strength (Read The Market)",
    compute=compute_sd_strength,
    default_options={"lookback": 20},
)

__all__ = ["PLUGIN_METADATA", "factory"]
