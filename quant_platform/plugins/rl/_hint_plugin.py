"""Factory helper for RL perception hint plugins."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from quant_platform.core.plugin import PluginMetadata
from quant_platform.rl_product.perception._helpers import HintEnvelope
from quant_platform.rl_product.registry import RL_GROUP
from services.shared.models import KlineRow


class PerceptionHintPlugin:
    """Timestamp-safe hint plugin: compute on bars[0:t+1]."""

    __slots__ = ("_compute", "_hint_name", "_family", "_options")

    def __init__(
        self,
        *,
        family: str,
        hint_name: str,
        compute: Callable[..., HintEnvelope],
        **options: Any,
    ) -> None:
        self._family = family
        self._hint_name = hint_name
        self._compute = compute
        self._options = options

    @property
    def hint_name(self) -> str:
        return self._hint_name

    @property
    def family(self) -> str:
        return self._family

    def compute(self, bars: list[KlineRow], *, t: int | None = None) -> HintEnvelope:
        if t is None:
            t = len(bars) - 1
        view = list(bars[: t + 1])
        return self._compute(view, **self._options)

    def run(self, bars: list[KlineRow], *, t: int | None = None) -> HintEnvelope:
        return self.compute(bars, t=t)


def build_hint_plugin(
    *,
    name: str,
    family: str,
    hint_name: str,
    description: str,
    compute: Callable[..., HintEnvelope],
    default_options: dict[str, Any] | None = None,
) -> tuple[PluginMetadata, Callable[..., PerceptionHintPlugin]]:
    meta = PluginMetadata(
        name=name,
        version="1.0.0",
        platform_version_compatibility=">=1.0.0,<2.0.0",
        description=description,
        input_types=["klines", "bars"],
        output_types=["perception_hint"],
        registry_group=RL_GROUP,
    )

    def factory(*, config: dict | None = None, **kwargs) -> PerceptionHintPlugin:
        options = dict(default_options or {})
        if config:
            options.update({k: v for k, v in config.items() if k not in ("master_gate", "gate_smc")})
        options.update(kwargs)
        return PerceptionHintPlugin(family=family, hint_name=hint_name, compute=compute, **options)

    factory.PLUGIN_METADATA = meta  # type: ignore[attr-defined]
    return meta, factory
