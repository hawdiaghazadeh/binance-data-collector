"""Feature registry (Phase 3)."""

from __future__ import annotations

from quant_platform.core.registry import BaseRegistry
from quant_platform.interfaces.feature import FeatureProtocol

FEATURE_GROUP = "platform.features"
feature_registry: BaseRegistry[FeatureProtocol] = BaseRegistry.get_instance(FEATURE_GROUP)
