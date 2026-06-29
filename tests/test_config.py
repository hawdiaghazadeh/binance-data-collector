"""Unit tests for configuration loader."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from services.shared.config import AppConfig, load_config


@pytest.fixture
def sample_config_file(tmp_path: Path) -> Path:
    config = {
        "symbols": ["btcusdt", "ethusdt"],
        "timeframes": ["1h", "1d"],
        "paths": {
            "download_dir": str(tmp_path / "downloads"),
            "logs_dir": str(tmp_path / "logs"),
            "state_dir": str(tmp_path / "state"),
        },
        "database": {
            "host": "localhost",
            "port": 8123,
            "database": "crypto_test",
        },
        "downloader": {"max_concurrent": 4, "retry_count": 3},
        "importer": {"max_workers": 2, "batch_size": 1000},
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(config), encoding="utf-8")
    return path


def test_load_config_from_yaml(sample_config_file: Path) -> None:
    config = load_config(sample_config_file)
    assert isinstance(config, AppConfig)
    assert config.symbols == ["BTCUSDT", "ETHUSDT"]
    assert config.timeframes == ["1h", "1d"]
    assert config.database.host == "localhost"
    assert config.database.database == "crypto_test"
    assert config.downloader.max_concurrent == 4
    assert config.importer.batch_size == 1000


def test_symbols_normalized_to_uppercase(sample_config_file: Path) -> None:
    config = load_config(sample_config_file)
    assert all(s.isupper() for s in config.symbols)


def test_paths_properties(sample_config_file: Path) -> None:
    config = load_config(sample_config_file)
    assert config.paths.download_path.name == "downloads"
    assert config.paths.logs_path.name == "logs"


def test_config_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/config.yaml")


def test_env_override_symbols(sample_config_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYMBOLS", "SOLUSDT,AVAXUSDT")
    config = load_config(sample_config_file)
    assert config.symbols == ["SOLUSDT", "AVAXUSDT"]


def test_env_override_database_host(sample_config_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE__HOST", "clickhouse-prod")
    config = load_config(sample_config_file)
    assert config.database.host == "clickhouse-prod"


def test_default_config_values() -> None:
    config = AppConfig()
    assert config.downloader.max_concurrent == 8
    assert config.importer.batch_size == 50_000
    assert config.database.compression is True
