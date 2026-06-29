"""Tests for importer worker ordering."""

from pathlib import Path

from services.importer.worker import zip_chronological_key


def test_zip_chronological_key_sorts_oldest_first() -> None:
    paths = [
        Path("BTCUSDT/1h/BTCUSDT-1h-2021-03.zip"),
        Path("BTCUSDT/1h/BTCUSDT-1h-2020-12.zip"),
        Path("ETHUSDT/1h/ETHUSDT-1h-2020-01.zip"),
        Path("BTCUSDT/1h/BTCUSDT-1h-2021-01.zip"),
    ]
    sorted_paths = sorted(paths, key=zip_chronological_key)
    assert sorted_paths[0].name == "BTCUSDT-1h-2020-12.zip"
    assert sorted_paths[1].name == "BTCUSDT-1h-2021-01.zip"
    assert sorted_paths[2].name == "BTCUSDT-1h-2021-03.zip"
    assert sorted_paths[3].name == "ETHUSDT-1h-2020-01.zip"
