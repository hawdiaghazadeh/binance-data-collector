"""Importer service entry point."""

from __future__ import annotations

import signal
import sys

from services.database.client import ClickHouseClient
from services.importer.worker import ImportWorker
from services.shared.config import load_config
from services.shared.logging import setup_logging


def run_importer() -> int:
    """Main entry point for the importer service."""
    config = load_config()
    logger = setup_logging(
        service_name="importer",
        logs_dir=config.paths.logs_path,
        level=config.logging.level,
        json_logs=config.logging.json_logs,
        log_to_file=config.logging.log_to_file,
    )

    db = ClickHouseClient(config.database)
    worker = ImportWorker(config, db)

    def _handle_signal(*_) -> None:
        logger.info("signal_received")
        worker.request_shutdown()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        logger.info("waiting_for_database", host=config.database.host)
        _wait_for_database(db, max_retries=30, delay=2.0)

        db.connect()
        stats = worker.run()
        stats.log_summary(logger)

        if stats.failed > 0:
            logger.error("importer_finished_with_errors", failed=stats.failed)
            return 1

        logger.info("importer_finished_successfully")
        return 0

    finally:
        db.close()


def _wait_for_database(db: ClickHouseClient, max_retries: int, delay: float) -> None:
    """Block until ClickHouse is reachable."""
    import time

    for attempt in range(1, max_retries + 1):
        try:
            db.connect()
            if db.ping():
                return
        except Exception:
            pass
        finally:
            db.close()

        time.sleep(delay)

    raise ConnectionError(
        f"ClickHouse not available after {max_retries} retries"
    )


def main() -> None:
    """CLI entry point."""
    sys.exit(run_importer())


if __name__ == "__main__":
    main()
