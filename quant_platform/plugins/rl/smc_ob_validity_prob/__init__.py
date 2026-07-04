"""SMC order block validity hint plugin."""

from __future__ import annotations

from quant_platform.plugins.rl._hint_plugin import build_hint_plugin
from quant_platform.rl_product.perception.smc import compute_ob_validity

PLUGIN_METADATA, factory = build_hint_plugin(
    name="smc_ob_validity_prob",
    family="smc",
    hint_name="ob_validity",
    description="Order block proximity validity (normalized, no raw levels)",
    compute=compute_ob_validity,
    default_options={"displacement_pct": 0.005},
)

__all__ = ["PLUGIN_METADATA", "factory"]
