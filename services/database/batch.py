"""Pure helpers for ClickHouse batch insert payloads."""

from __future__ import annotations

from typing import Sequence

from services.shared.models import KlineRow


def klines_to_tuples(rows: Sequence[KlineRow]) -> list[tuple]:
    """Convert kline rows to insert tuples without side effects."""
    return [row.as_tuple() for row in rows]
