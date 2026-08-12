"""
AI-LSC — Main window protocol.

Defines the interface that all UI page widgets expect from their parent
(main window) via a ``typing.Protocol``.  This decouples the pages from
the concrete ``AILocalStackControl`` god class so they can be tested and
refactored independently.

Every ``self.parent`` / ``self.main`` attribute access in the page widgets
is documented here.  During Phase 2 extraction the widgets continue to
receive the concrete main window; in Phase 3 the main window formally
implements this protocol.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ai_lsc.registry.manager import RegistryManager
    from ai_lsc.runtime.executor import RuntimeExecutor
    from PySide6.QtWidgets import QStackedWidget

    # Forward-declared opaque widget type used by the protocol below.
    # Imported lazily so the protocol module stays importable in test
    # environments that do not have PySide6 installed.
    try:
        from ai_lsc.ui.pages.skills_console import SkillsConsole
        _SkillsConsoleWidget = SkillsConsole
    except ImportError:
        _SkillsConsoleWidget = object  # fallback for non-GUI envs


@runtime_checkable
class MainWindowProtocol(Protocol):
    """Minimal interface that every UI page widget expects from its parent.

    Attributes
    ----------
    base_dir : str
    tools_root : str
    models_root : str
    workspaces_root : str
    logs_root : str
    exports_root : str
    config_root : str
    skills_root : str
    datasets_root : str
    base_bin_dir : str
    dtach_bin : str | None
    registry_mgr : RegistryManager
    nav_stack : QStackedWidget
    skills_console_tab : SkillsConsole
    runtime : RuntimeExecutor
    """

    # ── Paths (read-only) ──────────────────────────────────────────────
    base_dir: str
    tools_root: str
    models_root: str
    workspaces_root: str
    logs_root: str
    exports_root: str
    config_root: str
    skills_root: str
    datasets_root: str
    base_bin_dir: str
    dtach_bin: str | None

    # ── Services ─────────────────────────────────────────────────────
    # M-25: replace bare ``object`` annotations with TYPE_CHECKING
    # imports so static type checkers can actually verify the protocol.
    registry_mgr: "RegistryManager"
    nav_stack: "QStackedWidget"
    skills_console_tab: "_SkillsConsoleWidget"
    runtime: "RuntimeExecutor"

    # ── Methods ───────────────────────────────────────────────────────
    def log(self, message: str, source: str = "") -> None: ...
    def refresh_all_models(self) -> None: ...
    def verify_and_watch(self, log_file: str) -> None: ...
    def sync_chat_workspace_dropdown(self) -> None: ...
    def _populate_services(self) -> None: ...
    def finalize_stack_export(self, backend: str) -> None: ...
