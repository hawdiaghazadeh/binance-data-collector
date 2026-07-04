"""ICT premium/discount position hint plugin."""

from __future__ import annotations

from quant_platform.plugins.rl._hint_plugin import build_hint_plugin
from quant_platform.rl_product.perception.ict import compute_premium_discount

PLUGIN_METADATA, factory = build_hint_plugin(
    name="ict_premium_discount_prob",
    family="ict",
    hint_name="premium_discount",
    description="Normalized premium/discount position in recent range",
    compute=compute_premium_discount,
    default_options={"lookback": 20},
)

__all__ = ["PLUGIN_METADATA", "factory"]
