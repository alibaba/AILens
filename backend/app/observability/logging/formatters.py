"""Custom logging formatters for structured output."""

import logging
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Structured formatter for development and debugging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured fields."""
        timestamp = datetime.utcfromtimestamp(record.created).isoformat()
        base_msg = f"{timestamp} | {record.levelname:8} | {record.name:15} | {record.getMessage()}"

        # Add extra fields
        extras = []
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in {
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "message",
                }:
                    extras.append(f"{key}={value}")

        if extras:
            base_msg += " | " + " ".join(extras)

        # Add exception if present
        if record.exc_info:
            base_msg += "\n" + self.formatException(record.exc_info)

        return base_msg
