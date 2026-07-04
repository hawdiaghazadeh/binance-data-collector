"""SMC/ICT strategy signal generation (Phase 12)."""

from __future__ import annotations

from typing import Any


def evaluate_smc_signals(
    *,
    market_structure: dict[str, Any] | None = None,
    fvg: list[dict[str, Any]] | None = None,
    order_blocks: list[dict[str, Any]] | None = None,
    current_index: int,
    lookback: int = 1,
) -> list[dict[str, Any]]:
    """Generate skeleton SMC/ICT signals from market structure envelopes."""
    signals: list[dict[str, Any]] = []
    min_index = max(current_index - lookback, 0)

    if market_structure is not None:
        for bucket in ("bos", "choch"):
            for event in market_structure.get(bucket, []):
                event_index = int(event.get("index", -1))
                if event_index < min_index or event_index > current_index:
                    continue
                kind = str(event.get("kind", ""))
                side = "buy" if kind.startswith("bullish") else "sell"
                signals.append(
                    {
                        "side": side,
                        "reason": kind,
                        "source": "smc_ict",
                        "index": event_index,
                        "level": event.get("level"),
                        "strength": 1.0 if bucket == "bos" else 0.8,
                    }
                )

    if fvg is not None:
        for gap in fvg:
            gap_index = int(gap.get("index", -1))
            if gap_index < min_index or gap_index > current_index:
                continue
            direction = str(gap.get("direction", ""))
            side = "buy" if direction == "bullish" else "sell"
            signals.append(
                {
                    "side": side,
                    "reason": "fvg",
                    "source": "smc_ict",
                    "index": gap_index,
                    "top": gap.get("top"),
                    "bottom": gap.get("bottom"),
                    "strength": 0.7,
                }
            )

    if order_blocks is not None:
        for block in order_blocks:
            block_index = int(block.get("index", -1))
            displacement_index = int(block.get("displacement_index", block_index))
            if displacement_index < min_index or displacement_index > current_index:
                continue
            direction = str(block.get("direction", ""))
            side = "buy" if direction == "bullish" else "sell"
            signals.append(
                {
                    "side": side,
                    "reason": "order_block",
                    "source": "smc_ict",
                    "index": block_index,
                    "high": block.get("high"),
                    "low": block.get("low"),
                    "strength": 0.9,
                }
            )

    return signals
