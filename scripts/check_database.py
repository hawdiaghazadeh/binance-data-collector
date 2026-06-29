"""Pipeline health and statistics checks."""

from __future__ import annotations

import sys

from services.database.client import ClickHouseClient
from services.shared.config import load_config
from services.shared.logging import setup_logging


def main() -> int:
    config = load_config()
    logger = setup_logging(
        service_name="scripts",
        logs_dir=config.paths.logs_path,
        level=config.logging.level,
    )

    db = ClickHouseClient(config.database)
    try:
        db.connect()
        if not db.ping():
            logger.error("clickhouse_ping_failed")
            return 1

        total = db.count_rows()
        logger.info("database_status", statistics=True, total_rows=total)

        for symbol in config.symbols[:3]:
            for tf in config.timeframes[:2]:
                count = db.count_rows(symbol=symbol, timeframe=tf)
                if count:
                    logger.info(
                        "symbol_timeframe_count",
                        statistics=True,
                        symbol=symbol,
                        timeframe=tf,
                        rows=count,
                    )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
