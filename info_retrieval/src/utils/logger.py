import logging
import os
from typing import Optional, Union


def get_logger(name: str, level: Optional[Union[int, str]] = None) -> logging.Logger:
    """
    Configure and return a module-level logger.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(log_level)
    logger.propagate = False
    return logger
