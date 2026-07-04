"""Data provider protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DataProviderProtocol(Protocol):
    def discover_files(self, symbol: str, timeframe: str) -> list[Any]: ...
    def build_download_url(self, file_info: Any) -> str: ...
    def create_worker(self) -> Any: ...
