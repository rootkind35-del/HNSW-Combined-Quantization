"""Utility functions for logging, timing, and stream generation."""

import logging
import sys
import time
from contextlib import contextmanager
from typing import Generator, Iterable, List


def get_logger(name: str = "ann_data", level: int = logging.INFO) -> logging.Logger:
    """Creates a configured logger with standard formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        # Ensure stdout handles unicode without crashing on Windows cp1252
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


@contextmanager
def timer(name: str, logger: logging.Logger = None):
    """Context manager to measure execution time."""
    start_time = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start_time
    msg = f"Operation '{name}' finished in {elapsed:.4f} seconds"
    if logger:
        logger.info(msg)
    else:
        print(msg)


def chunk_stream(iterable: Iterable[str], chunk_size: int) -> Generator[List[str], None, None]:
    """Splits an iterable stream into fixed-size chunks without loading entire data into RAM."""
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
