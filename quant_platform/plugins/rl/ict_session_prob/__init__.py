"""ICT session probability hint plugin."""

from __future__ import annotations

from quant_platform.plugins.rl._hint_plugin import build_hint_plugin
from quant_platform.rl_product.perception.ict import compute_session_prob

PLUGIN_METADATA, factory = build_hint_plugin(
    name="ict_session_prob",
    family="ict",
    hint_name="session_p",
    description="ICT session weight from bar timestamp (UTC)",
    compute=compute_session_prob,
)

__all__ = ["PLUGIN_METADATA", "factory"]
