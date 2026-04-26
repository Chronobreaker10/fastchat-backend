from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DEFAULT_FORMAT = (
    "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
)


def setup_logger(
    file_name: str, level: int = logging.INFO, log_format: str | None = None
) -> logging.Logger:
    if not Path("logs").exists():
        Path("logs").mkdir()

    handler = RotatingFileHandler(
        f"logs/{file_name}.log",
        maxBytes=10485760,
        backupCount=20,
    )
    if log_format:
        handler.setFormatter(logging.Formatter(LOG_DEFAULT_FORMAT))
    handler.setLevel(level)
    logger = logging.getLogger(file_name)
    logger.addHandler(handler)
    return logger


app_errors_logger = setup_logger("app_errors", logging.ERROR, LOG_DEFAULT_FORMAT)
access_logger = setup_logger("access", logging.WARNING)
