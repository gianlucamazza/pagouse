"""Structured logging via stdlib logging, configured by PAGOUSE_LOG env var."""

from __future__ import annotations

import logging
import os

_LOG_LEVELS = os.environ.get("PAGOUSE_LOG", "warning").lower()
_LOG_LEVEL = getattr(logging, _LOG_LEVELS.upper(), logging.WARNING)

logger = logging.getLogger("pagouse")


def setup(verbose: bool = False) -> logging.Logger:
    """Configure the root pagouse logger and return it."""
    level = logging.DEBUG if verbose else _LOG_LEVEL
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    return logger
