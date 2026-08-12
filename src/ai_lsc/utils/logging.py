"""
AI-LSC — Centralised logging.

The monolith did not use ``logging`` at all; messages were appended to
a QTextEdit via Qt signals.  This module sets up a root logger that
*also* writes to a rotating file so we get persistent logs even when
the GUI is not running.

Usage::

    from ai_lsc.utils.logging import get_logger

    log = get_logger("service_row")
    log.info("Ollama started on port 11434")
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logging(
    log_dir: str | Path | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configure the root ``ai_lsc`` logger with console + file output.

    Parameters
    ----------
    log_dir:
        Directory for the log file.  If *None*, logs go to console only.
    level:
        Logging verbosity.
    """
    root = logging.getLogger("ai_lsc")
    root.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if root.handlers:
        return root

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)-20s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # File handler (optional)
    if log_dir is not None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(
            log_dir / "ai_lsc.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=3,
            encoding="utf-8",
        )
        fh.setLevel(level)
        fh.setFormatter(fmt)
        root.addHandler(fh)

    return root


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``ai_lsc`` namespace.

    ``name`` should be the module or component name, e.g. ``"registry"``
    or ``"service_row"``.
    """
    return logging.getLogger(f"ai_lsc.{name}")
