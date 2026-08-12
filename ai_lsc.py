#!/usr/bin/env python3
"""AI Local Stack Control v3.1 — Ankh of Jah

Direct launcher.  Run from the project root:

    python ai_lsc.py

No pip install, no entry-point scripts, no ~/.local pollution.
Reads .env (created by bootstrap.sh) for AI_LSC_BASE_DIR, then
points sys.path at src/ and calls main().

Works wherever it sits — fully portable.
"""
from __future__ import annotations

import os
import sys

# ── Resolve project root (works from any cwd) ──────────────────
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# ── Load .env file for AI_LSC_BASE_DIR (before any ai_lsc imports) ──
# Bootstrap writes this.  If missing, constants.py falls back to /mnt/AI
# or the AI_LSC_BASE_DIR env var.
_ENV_FILE = os.path.join(_PROJECT_ROOT, ".env")
if os.path.isfile(_ENV_FILE):
    with open(_ENV_FILE) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                if _key.strip() == "AI_LSC_BASE_DIR" and _val.strip():
                    os.environ.setdefault("AI_LSC_BASE_DIR", _val.strip())


def main() -> int:
    """Launch the AI-LSC desktop application."""
    # PySide6 required
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "PySide6 is required but not installed.\n\n"
            "  source .venv/bin/activate\n"
            "  pip install PySide6>=6.6\n\n"
            "  Or re-run:  bash bootstrap.sh",
            file=sys.stderr,
        )
        return 1

    from ai_lsc.ui.main_window import AILocalStackControl

    app = QApplication.instance() or QApplication(sys.argv)
    window = AILocalStackControl()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
