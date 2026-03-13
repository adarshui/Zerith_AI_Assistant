"""
Zerith AI — Logger
Rich-formatted logging to console and file.
"""

import logging
import sys
from pathlib import Path
from rich.logging import RichHandler
from rich.console import Console

console = Console()

# ── Log directory ────────────────────────────────────────
LOG_DIR = Path(__file__).resolve().parent.parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "zerith.log"


def get_logger(name: str = "zerith") -> logging.Logger:
    """Return a configured logger with rich console + file output."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)

    # ── Console handler (rich) ───────────────────────────
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        markup=True,
    )
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_fmt)

    # ── File handler ─────────────────────────────────────
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


# Pre-built logger for quick imports
log = get_logger()
