from __future__ import annotations

import logging
import logging.config
import os
from typing import Any


_CONFIGURED = False


def configure_logging(*, level: str | None = None) -> None:
    """Configure application logging.

    Uses stdlib logging only. Safe to call multiple times.
    """

    global _CONFIGURED
    if _CONFIGURED:
        return

    resolved_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()

    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": resolved_level,
            }
        },
        "root": {
            "handlers": ["console"],
            "level": resolved_level,
        },
    }

    logging.config.dictConfig(config)
    _CONFIGURED = True
