"""Central logging setup for production bot runs."""

from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


class JsonFormatter(logging.Formatter):
    """Small JSON formatter for structured production logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(log_file: str, level: str = "INFO", fmt: str | None = None) -> None:
    """Configure console and rotating-file logging once."""
    log_level = getattr(logging, str(level).upper(), logging.INFO)
    log_format = fmt or "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    root = logging.getLogger()
    root.setLevel(log_level)

    formatter: logging.Formatter
    if str(log_format).lower() == "json":
        formatter = JsonFormatter()
    else:
        try:
            formatter = logging.Formatter(log_format)
        except ValueError:
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handlers: list[logging.Handler] = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True) if path.parent != Path(".") else None
        file_handler = RotatingFileHandler(
            path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root.handlers.clear()
    for handler in handlers:
        root.addHandler(handler)
