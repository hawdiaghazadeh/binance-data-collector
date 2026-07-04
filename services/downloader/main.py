"""Downloader service entry point."""

from __future__ import annotations

import asyncio
import signal
import sys

import httpx
from tqdm import tqdm

from quant_platform.bootstrap import bootstrap_pipeline
from services.shared.config import load_config
from services.shared.logging import setup_logging


async def run_downloader() -> int:
    """Main async entry point for the downloader service."""
    config = load_config()
    logger = setup_logging(
        service_name="downloader",
        logs_dir=config.paths.logs_path,
        level=config.logging.level,
        json_logs=config.logging.json_logs,
        log_to_file=config.logging.log_to_file,
    )

    config.paths.download_path.mkdir(parents=True, exist_ok=True)
    config.paths.state_path.mkdir(parents=True, exist_ok=True)

    runtime = bootstrap_pipeline(config)
    provider = runtime.data_provider
    worker = provider.create_worker()
    loop = asyncio.get_running_loop()

    def _handle_signal() -> None:
        logger.info("signal_received")
        worker.request_shutdown()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            signal.signal(sig, lambda *_: worker.request_shutdown())

    timeout = httpx.Timeout(config.downloader.request_timeout_seconds)
    headers = {"User-Agent": config.binance.user_agent}

    all_files = []
    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        logger.info(
            "discovery_started",
            symbols=len(config.symbols),
            timeframes=len(config.timeframes),
        )

        for symbol in config.symbols:
            for timeframe in config.timeframes:
                if worker.is_shutdown:
                    break
                try:
                    files = await provider.discover_files(client, symbol, timeframe)
                    all_files.extend(files)
                except Exception as exc:
                    logger.error(
                        "discovery_failed",
                        symbol=symbol,
                        timeframe=timeframe,
                        error=str(exc),
                    )

        logger.info("download_started", total_files=len(all_files))

        with tqdm(total=len(all_files), desc="Downloading", unit="file") as pbar:
            original_download = worker.download_file

            async def tracked_download(client, monthly_file):
                result = await original_download(client, monthly_file)
                pbar.update(1)
                return result

            worker.download_file = tracked_download  # type: ignore[method-assign]
            await worker.download_all(client, all_files)

    worker.stats.log_summary(logger)

    if worker.stats.failed > 0:
        logger.error("downloader_finished_with_errors", failed=worker.stats.failed)
        return 1

    logger.info("downloader_finished_successfully")
    return 0


def main() -> None:
    """CLI entry point."""
    exit_code = asyncio.run(run_downloader())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
