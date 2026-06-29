"""Pydantic configuration models and YAML loader."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class BinanceConfig(BaseModel):
    """Binance Vision data source settings."""

    base_url: str = "https://data.binance.vision/data/futures/um/monthly/klines"
    listing_url: str = "https://data.binance.vision"
    s3_listing_url: str = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
    user_agent: str = "crypto-pipeline/1.0"


class PathsConfig(BaseModel):
    """Filesystem paths for downloads, logs, and state."""

    download_dir: str = "/downloads"
    logs_dir: str = "/logs"
    state_dir: str = "/downloads/.state"

    @property
    def download_path(self) -> Path:
        return Path(self.download_dir)

    @property
    def logs_path(self) -> Path:
        return Path(self.logs_dir)

    @property
    def state_path(self) -> Path:
        return Path(self.state_dir)


class DatabaseConfig(BaseModel):
    """ClickHouse connection and table settings."""

    host: str = "localhost"
    port: int = 8123
    native_port: int = 9000
    user: str = "default"
    password: str = ""
    database: str = "crypto"
    table: str = "klines"
    import_state_table: str = "import_state"
    connect_timeout: int = 30
    send_receive_timeout: int = 300
    compression: bool = True


class DownloaderConfig(BaseModel):
    """Downloader concurrency, retry, and network settings."""

    max_concurrent: int = Field(default=8, ge=1, le=64)
    retry_count: int = Field(default=5, ge=0, le=20)
    retry_backoff_seconds: float = Field(default=2.0, ge=0.1)
    retry_backoff_multiplier: float = Field(default=2.0, ge=1.0)
    request_timeout_seconds: float = Field(default=120.0, ge=5.0)
    verify_checksum: bool = True
    chunk_size_bytes: int = Field(default=1_048_576, ge=8192)


class ImporterConfig(BaseModel):
    """Importer worker, batching, and validation settings."""

    max_workers: int = Field(default=4, ge=1, le=32)
    batch_size: int = Field(default=50_000, ge=100)
    retry_count: int = Field(default=3, ge=0, le=20)
    retry_backoff_seconds: float = Field(default=2.0, ge=0.1)
    delete_after_import: bool = False
    validate_gaps: bool = True


class LoggingConfig(BaseModel):
    """Structured logging configuration."""

    level: str = "INFO"
    json_logs: bool = False
    log_to_file: bool = True


class AppConfig(BaseModel):
    """Root application configuration."""

    binance: BinanceConfig = Field(default_factory=BinanceConfig)
    symbols: list[str] = Field(default_factory=list)
    timeframes: list[str] = Field(default_factory=list)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    downloader: DownloaderConfig = Field(default_factory=DownloaderConfig)
    importer: ImporterConfig = Field(default_factory=ImporterConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @field_validator("symbols", mode="before")
    @classmethod
    def normalize_symbols(cls, value: list[str]) -> list[str]:
        return [s.strip().upper() for s in value if s.strip()]

    @field_validator("timeframes", mode="before")
    @classmethod
    def normalize_timeframes(cls, value: list[str]) -> list[str]:
        return [t.strip() for t in value if t.strip()]


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override dict into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """
    Load configuration from YAML file with optional environment overrides.

    Environment variable CONFIG_PATH overrides the default config file location.
    Individual settings can be overridden via nested env vars using double
    underscores, e.g. DATABASE__HOST=localhost.
    """
    path = Path(config_path or os.environ.get("CONFIG_PATH", "config/config.yaml"))
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open(encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    env_overrides = _env_overrides_from_prefix()
    if env_overrides:
        raw = _deep_merge(raw, env_overrides)

    return AppConfig.model_validate(raw)


def _env_overrides_from_prefix() -> dict[str, Any]:
    """Build nested dict from environment variables like DATABASE__HOST."""
    prefixes = ("BINANCE", "PATHS", "DATABASE", "DOWNLOADER", "IMPORTER", "LOGGING")
    list_keys = {"SYMBOLS", "TIMEFRAMES"}
    overrides: dict[str, Any] = {}

    for key, value in os.environ.items():
        upper = key.upper()
        if upper in list_keys:
            overrides[upper.lower()] = [item.strip() for item in value.split(",") if item.strip()]
            continue

        for prefix in prefixes:
            prefix_token = f"{prefix}__"
            if upper.startswith(prefix_token):
                section = prefix.lower()
                field_name = upper[len(prefix_token) :].lower()
                overrides.setdefault(section, {})
                overrides[section][field_name] = _coerce_env_value(value)

    return overrides


def _coerce_env_value(value: str) -> bool | int | float | str:
    """Coerce string environment values to appropriate Python types."""
    lower = value.lower()
    if lower in ("true", "false"):
        return lower == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
