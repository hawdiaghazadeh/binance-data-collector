"""Importer storage interfaces for testability and plugin adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Sequence

from services.shared.models import KlineRow


class KlineStorage(Protocol):
    """Kline persistence operations used by ImportWorker."""

    def insert_klines(self, rows: Sequence[KlineRow]) -> int: ...
    def is_file_imported(self, file_path: str) -> bool: ...
    def mark_file_imported(
        self,
        file_path: str,
        symbol: str,
        timeframe: str,
        year: int,
        month: int,
        rows_inserted: int,
    ) -> None: ...
    def remove_file_import_state(self, file_path: str) -> None: ...
    def delete_month_klines(
        self,
        symbol: str,
        timeframe: str,
        year: int,
        month: int,
    ) -> None: ...


class StoragePool(Protocol):
    """Thread-local or shared pool that yields KlineStorage handles."""

    def get(self) -> KlineStorage: ...
    def connect(self) -> None: ...
    def close(self) -> None: ...
    def ping(self) -> bool: ...
