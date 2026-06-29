"""Structured logging setup for pipeline services."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import structlog


def setup_logging(
    service_name: str,
    logs_dir: Path,
    level: str = "INFO",
    json_logs: bool = False,
    log_to_file: bool = True,
) -> structlog.stdlib.BoundLogger:
    """
    Configure structlog with console and optional file handlers.

    Creates separate log files per service plus shared error and statistics logs.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, level.upper(), logging.INFO)

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=False))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_to_file:
        _add_file_handler(root, logs_dir / f"{service_name}.log", log_level, formatter)
        _add_file_handler(root, logs_dir / "errors.log", logging.ERROR, formatter)
        stats_handler = _add_file_handler(
            root, logs_dir / "statistics.log", logging.INFO, formatter
        )
        stats_handler.addFilter(_StatisticsFilter())

    logger = structlog.get_logger(service_name)
    logger.info("logging_initialized", service=service_name, level=level)
    return logger


def _add_file_handler(
    root: logging.Logger,
    path: Path,
    level: int,
    formatter: logging.Formatter,
) -> logging.Handler:
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(formatter)
    root.addHandler(handler)
    return handler


class _StatisticsFilter(logging.Filter):
    """Route statistics events to the statistics log file."""

    def filter(self, record: logging.LogRecord) -> bool:
        return getattr(record, "statistics", False) or "statistics" in record.getMessage().lower()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)
