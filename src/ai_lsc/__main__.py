"""AI Local Stack Control — console entry point.

Invoked via the ``ai-lsc`` script (registered in pyproject.toml) or
``python -m ai_lsc``.  Launches the PySide6 desktop application.
"""

import os
import sys


def main() -> int:
    """Launch the AI-LSC desktop application and return the exit code."""
    # PySide6 is a required dependency as of v3.0 — if it's missing we fail
    # loudly rather than falling back to a degraded mode.
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

    from ai_lsc.constants import BASE_DIR
    from ai_lsc.utils.logging import setup_logging

    # DO-06: initialise logging before any Qt objects are created
    log_dir = os.path.join(BASE_DIR, "logs")
    setup_logging(log_dir=log_dir)

    from ai_lsc.ui.main_window import AILocalStackControl

    app = QApplication.instance() or QApplication(sys.argv)
    window = AILocalStackControl()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
