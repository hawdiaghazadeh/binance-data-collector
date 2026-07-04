"""RTM range compression probability hint plugin."""

from __future__ import annotations

from quant_platform.plugins.rl._hint_plugin import build_hint_plugin
from quant_platform.rl_product.perception.rtm import compute_compression_prob

PLUGIN_METADATA, factory = build_hint_plugin(
    name="rtm_compression_prob",
    family="rtm",
    hint_name="compression_p",
    description="Volatility compression probability (short/long ATR ratio)",
    compute=compute_compression_prob,
    default_options={"short": 5, "long": 20},
)

__all__ = ["PLUGIN_METADATA", "factory"]
