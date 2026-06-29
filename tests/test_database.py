"""Unit tests for database module."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from services.database.client import ClickHouseClient
from services.database.schema import ensure_schema
from services.shared.config import DatabaseConfig
from services.shared.models import KlineRow


@pytest.fixture
def db_config() -> DatabaseConfig:
    return DatabaseConfig(
        host="localhost",
        port=8123,
        database="crypto_test",
        table="klines",
        import_state_table="import_state",
    )


@pytest.fixture
def sample_kline() -> KlineRow:
    return KlineRow(
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
        open=29000.0,
        high=29500.0,
        low=28800.0,
        close=29300.0,
        volume=1000.0,
        close_time=datetime(2021, 1, 1, 0, 59, 59, tzinfo=timezone.utc),
        quote_volume=29_000_000.0,
        trade_count=5000,
        taker_buy_volume=500.0,
        taker_buy_quote_volume=14_500_000.0,
    )


def test_kline_row_as_tuple(sample_kline: KlineRow) -> None:
    row = sample_kline.as_tuple()
    assert len(row) == 13
    assert row[0] == "BTCUSDT"
    assert row[1] == "1h"


@patch("services.database.client.clickhouse_connect.get_client")
def test_clickhouse_connect(mock_get_client: MagicMock, db_config: DatabaseConfig) -> None:
    mock_client = MagicMock()
    mock_client.command.return_value = None
    mock_get_client.return_value = mock_client

    db = ClickHouseClient(db_config)
    db.connect()

    mock_get_client.assert_called_once()
    assert mock_client.command.call_count >= 3


@patch("services.database.client.clickhouse_connect.get_client")
def test_insert_klines(mock_get_client: MagicMock, db_config: DatabaseConfig, sample_kline: KlineRow) -> None:
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    db = ClickHouseClient(db_config)
    db.connect()
    count = db.insert_klines([sample_kline])

    assert count == 1
    mock_client.insert.assert_called_once()
    args = mock_client.insert.call_args
    assert "crypto_test.klines" in args[0][0]


@patch("services.database.client.clickhouse_connect.get_client")
def test_is_file_imported(mock_get_client: MagicMock, db_config: DatabaseConfig) -> None:
    mock_client = MagicMock()
    mock_result = MagicMock()
    mock_result.first_row = [1]
    mock_client.query.return_value = mock_result
    mock_get_client.return_value = mock_client

    db = ClickHouseClient(db_config)
    db.connect()

    assert db.is_file_imported("BTCUSDT/1h/BTCUSDT-1h-2021-01.zip") is True


@patch("services.database.client.clickhouse_connect.get_client")
def test_ping_success(mock_get_client: MagicMock, db_config: DatabaseConfig) -> None:
    mock_client = MagicMock()
    mock_client.command.return_value = 1
    mock_get_client.return_value = mock_client

    db = ClickHouseClient(db_config)
    db.connect()
    assert db.ping() is True


def test_ensure_schema_calls_commands() -> None:
    mock_client = MagicMock()
    ensure_schema(mock_client, "crypto", "klines", "import_state")
    assert mock_client.command.call_count == 3


def test_client_not_connected_raises(db_config: DatabaseConfig) -> None:
    db = ClickHouseClient(db_config)
    with pytest.raises(RuntimeError, match="not connected"):
        _ = db.client
