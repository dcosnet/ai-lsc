"""AI-LSC UI sub-package.

All PySide6-dependent UI widgets live here.  If PySide6 is not installed
the sub-package still imports but the concrete widget classes will be ``None``.

Sub-packages
------------
pages
    Individual tab/page widgets (ServiceRow, ChatbotConsole, etc.).
dialogs
    Modal dialogs (StackWizard).
protocol
    :class:`MainWindowProtocol` interface for decoupling pages from
    the concrete main window.
"""

from ai_lsc.ui.protocol import MainWindowProtocol  # noqa: F401

# Lazy re-exports -- guarded so the package is importable without Qt.
try:
    from ai_lsc.ui.main_window import (
        AILocalStackControl,  # noqa: F401
        apply_terminal_theme,  # noqa: F401
    )
except ImportError:
    AILocalStackControl = None  # type: ignore[assignment, misc]
    apply_terminal_theme = None  # type: ignore[assignment, misc]

try:
    from ai_lsc.ui.dialogs.stack_wizard import StackWizard  # noqa: F401
except ImportError:
    StackWizard = None  # type: ignore[assignment, misc]

__all__ = [
    "MainWindowProtocol",
    "AILocalStackControl",
    "apply_terminal_theme",
    "StackWizard",
]
