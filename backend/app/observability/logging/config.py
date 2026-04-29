"""Logging configuration for structured logging with structured output."""

import logging
import sys
from typing import Optional

import structlog

from .formatters import StructuredFormatter


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "structured",
    log_file_path: Optional[str] = None,
    access_log_file_path: Optional[str] = None,
    error_log_file_path: Optional[str] = None,
) -> None:
    """Setup structured logging for the application."""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure root logger
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Setup application logger
    app_logger = logging.getLogger("ailens")
    if log_file_path:
        app_handler = logging.FileHandler(log_file_path)
        app_handler.setFormatter(StructuredFormatter())
        app_logger.addHandler(app_handler)

    # Setup access logger
    access_logger = logging.getLogger("access")
    access_logger.setLevel(logging.INFO)
    if access_log_file_path:
        access_handler = logging.FileHandler(access_log_file_path)
        access_handler.setFormatter(StructuredFormatter())
        access_logger.addHandler(access_handler)

    # Setup error logger
    error_logger = logging.getLogger("error")
    error_logger.setLevel(logging.ERROR)
    if error_log_file_path:
        error_handler = logging.FileHandler(error_log_file_path)
        error_handler.setFormatter(StructuredFormatter())
        error_logger.addHandler(error_handler)

    # Prevent duplicate logging
    access_logger.propagate = False
    error_logger.propagate = False


def get_access_logger() -> structlog.stdlib.BoundLogger:
    """Get the access logger instance."""
    return structlog.get_logger("access")


def get_error_logger() -> structlog.stdlib.BoundLogger:
    """Get the error logger instance."""
    return structlog.get_logger("error")


def get_app_logger() -> structlog.stdlib.BoundLogger:
    """Get the application logger instance."""
    return structlog.get_logger("ailens")
