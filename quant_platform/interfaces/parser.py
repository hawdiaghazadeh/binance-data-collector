"""Parser protocol."""

from __future__ import annotations

from typing import Any, Iterable, Protocol, runtime_checkable


@runtime_checkable
class ParserProtocol(Protocol):
    def parse_csv_stream(self, data: bytes, *, symbol: str, timeframe: str) -> Any: ...
    def parse_zip_klines(
        self, zip_path: Any, symbol: str, timeframe: str, *, validate_gaps: bool = True
    ) -> Any: ...
