"""
Centralized logging for AgriSense AI.
"""
import logging
import sys
from pathlib import Path

from .config import settings

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Formatter
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Console handler
import io
console_handler = logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'))
console_handler.setFormatter(formatter)

# File handler
file_handler = logging.FileHandler(LOG_DIR / "agrisense.log")
file_handler.setFormatter(formatter)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
