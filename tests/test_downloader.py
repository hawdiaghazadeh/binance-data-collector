"""Unit tests for downloader components."""

from __future__ import annotations

import re

import httpx
import pytest
import respx

from services.downloader.discovery import (
    _keys_to_monthly_files,
    _parse_s3_listing,
    build_download_url,
    discover_monthly_files,
    local_zip_path,
)
from services.shared.config import AppConfig
from services.shared.models import MonthlyFile


SAMPLE_S3_LISTING_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>data.binance.vision</Name>
  <Prefix>data/futures/um/monthly/klines/BTCUSDT/1h/</Prefix>
  <IsTruncated>false</IsTruncated>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2020-01.zip</Key>
    <Size>37271</Size>
  </Contents>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2020-01.zip.CHECKSUM</Key>
    <Size>89</Size>
  </Contents>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2020-02.zip</Key>
    <Size>35268</Size>
  </Contents>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2021-01.zip</Key>
    <Size>40000</Size>
  </Contents>
</ListBucketResult>
"""


@pytest.fixture
def app_config() -> AppConfig:
    return AppConfig(
        symbols=["BTCUSDT"],
        timeframes=["1h"],
        paths={"download_dir": "/tmp/downloads", "logs_dir": "/tmp/logs", "state_dir": "/tmp/state"},
    )


@pytest.fixture
def monthly_file() -> MonthlyFile:
    return MonthlyFile(symbol="BTCUSDT", timeframe="1h", year=2021, month=1)


def test_parse_s3_listing() -> None:
    keys, is_truncated, marker = _parse_s3_listing(SAMPLE_S3_LISTING_XML)
    assert len(keys) == 4
    assert is_truncated is False
    assert marker is None
    assert keys[0].endswith("BTCUSDT-1h-2020-01.zip")


def test_keys_to_monthly_files_filters_checksums() -> None:
    keys, _, _ = _parse_s3_listing(SAMPLE_S3_LISTING_XML)
    files = _keys_to_monthly_files(keys, "BTCUSDT", "1h")
    assert len(files) == 3
    assert all(f.filename.endswith(".zip") for f in files)
    assert not any(".CHECKSUM" in f.filename for f in files)


def test_monthly_file_filename(monthly_file: MonthlyFile) -> None:
    assert monthly_file.filename == "BTCUSDT-1h-2021-01.zip"
    assert monthly_file.checksum_filename == "BTCUSDT-1h-2021-01.zip.CHECKSUM"


def test_monthly_file_sort_key() -> None:
    f1 = MonthlyFile(symbol="BTCUSDT", timeframe="1h", year=2020, month=12)
    f2 = MonthlyFile(symbol="BTCUSDT", timeframe="1h", year=2021, month=1)
    assert f1.sort_key() < f2.sort_key()


def test_build_download_url(app_config: AppConfig, monthly_file: MonthlyFile) -> None:
    url = build_download_url(app_config, monthly_file)
    assert "BTCUSDT" in url
    assert "1h" in url
    assert url.endswith("BTCUSDT-1h-2021-01.zip")


def test_local_zip_path(app_config: AppConfig, monthly_file: MonthlyFile) -> None:
    path = local_zip_path(app_config, monthly_file)
    assert path.replace("\\", "/").endswith("BTCUSDT/1h/BTCUSDT-1h-2021-01.zip")


@pytest.mark.asyncio
@respx.mock
async def test_discover_monthly_files(app_config: AppConfig) -> None:
    url = re.compile(r".*data\.binance\.vision.*prefix=.*BTCUSDT.*1h.*")
    respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_S3_LISTING_XML))

    async with httpx.AsyncClient() as client:
        files = await discover_monthly_files(client, app_config, "BTCUSDT", "1h")

    assert len(files) == 3
    assert files[0].year == 2020 and files[0].month == 1
    assert files[-1].year == 2021 and files[-1].month == 1


@pytest.mark.asyncio
@respx.mock
async def test_discover_monthly_files_sorted_oldest_first(app_config: AppConfig) -> None:
    url = re.compile(r".*data\.binance\.vision.*")
    respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_S3_LISTING_XML))

    async with httpx.AsyncClient() as client:
        files = await discover_monthly_files(client, app_config, "BTCUSDT", "1h")

    for i in range(1, len(files)):
        assert files[i].sort_key() >= files[i - 1].sort_key()
