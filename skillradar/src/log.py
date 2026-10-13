"""Logger ghi ra logs/<tên>.log và stderr."""

import logging
import sys

from src.config import LOG_DIR


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    LOG_DIR.mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    for h in (logging.FileHandler(LOG_DIR / f"{name}.log", encoding="utf-8"),
              logging.StreamHandler(sys.stderr)):
        h.setFormatter(fmt)
        logger.addHandler(h)
    logger.setLevel(logging.INFO)
    return logger
