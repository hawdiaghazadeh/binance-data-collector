"""Feature gate — family-level context masking."""

from __future__ import annotations

from dataclasses import dataclass

from quant_platform.rl_product.perception.compressor import SLOT_FAMILIES, SLOT_NAMES_16


@dataclass(frozen=True, slots=True)
class GateConfig:
    master_gate: float = 1.0
    gate_smc: float = 1.0
    gate_rtm: float = 1.0
    gate_ict: float = 1.0

    @classmethod
    def from_config(cls, config: dict) -> GateConfig:
        perception = config.get("perception", config)
        return cls(
            master_gate=float(perception.get("master_gate", 1.0)),
            gate_smc=float(perception.get("gate_smc", 1.0)),
            gate_rtm=float(perception.get("gate_rtm", 1.0)),
            gate_ict=float(perception.get("gate_ict", 1.0)),
        )


class FeatureGate:
    """Apply master and per-family gates to compressed context vector."""

    __slots__ = ("_config",)

    def __init__(self, config: GateConfig | None = None) -> None:
        self._config = config or GateConfig()

    @property
    def config(self) -> GateConfig:
        return self._config

    def family_multiplier(self, family: str) -> float:
        if self._config.master_gate <= 0.0:
            return 0.0
        if family == "smc":
            return self._config.master_gate * self._config.gate_smc
        if family == "rtm":
            return self._config.master_gate * self._config.gate_rtm
        if family == "ict":
            return self._config.master_gate * self._config.gate_ict
        return self._config.master_gate

    def apply(self, context: list[float], *, context_dims: int | None = None) -> list[float]:
        dims = context_dims or len(context)
        if self._config.master_gate <= 0.0:
            return [0.0] * dims

        out = list(context[:dims])
        while len(out) < dims:
            out.append(0.0)

        slot_names = SLOT_NAMES_16 if dims <= 16 else SLOT_NAMES_16 + [f"reserved_{i}" for i in range(16, dims)]
        for i, name in enumerate(slot_names[:dims]):
            family = SLOT_FAMILIES.get(name, "meta")
            mult = self.family_multiplier(family)
            out[i] = out[i] * mult

        gate_mask_idx = slot_names.index("gate_mask") if "gate_mask" in slot_names else -1
        if 0 <= gate_mask_idx < dims:
            active = sum(
                1.0
                for f in (self._config.gate_smc, self._config.gate_rtm, self._config.gate_ict)
                if f > 0
            ) / 3.0
            out[gate_mask_idx] = active * self._config.master_gate
        return out

    def update(self, config: GateConfig) -> None:
        self._config = config
