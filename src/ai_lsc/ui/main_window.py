"""AILocalStackControl main window -- master controller.

Central QMainWindow that wires together every extracted page widget,
the sidebar navigation rack, the stacked-page workspace, the dashboard
lifecycle engine, service population, log watching, model discovery,
and config persistence.

Implements :class:`~ai_lsc.ui.protocol.MainWindowProtocol` so that
child page widgets can type-check their parent dependency without
coupling to the concrete class.

Coding standards inherited from the monolith:
  - Max 2 levels of ``if`` depth; use guard clauses, early returns,
    dispatch dictionaries, and arrays otherwise.
  - No ``while`` loops: iterators, list comprehensions, generators,
    ``next()``.
  - Fluid array usage: lookup tables, ``next()`` over ``for/break``.
"""

import json
import os
import subprocess
import tempfile
import threading
from datetime import datetime

from ai_lsc.constants import (
    APP_DISPLAY_NAME,
    APP_ICON_FILE,
    APP_VERSION,
    BASE_DIR,
    CONFIG_FILE,
    GLOBAL_STYLE,
    LOG_COLOR_DEFAULT,
    LOG_SOURCE_COLORS,
    NAV_LAYER_ORDER,
    OLLAMA_SERVER_CANDIDATES,
    PIPELINE_FILE_NAME,
    REQUIRED_DIRS,
    SIDEBAR_TREE_STYLE,
    STATE_FILE_NAME,
    TREE_SKIP_PATTERNS,
)
from ai_lsc.registry.manager import RegistryManager
from ai_lsc.runtime.executor import RuntimeExecutor
try:
    from ai_lsc.skills.resolver import SkillRuntimeResolver
except ImportError:
    SkillRuntimeResolver = None
from ai_lsc.stack.export import ContainerBackend, build_stack_spec
from ai_lsc.utils.ollama import (
    detect_ollama_server_dir,
    ollama_models_dir,
)
from ai_lsc.utils.process import enriched_env, find_binary


def _atomic_write_json(
    path: str | os.PathLike,
    payload: dict | list,
    *,
    indent: int = 4,
    encoding: str = "utf-8",
) -> None:
    """H-03 + M-04: atomically write JSON to *path* via tempfile + fsync +
    rename, with an advisory file lock so two ai-lsc instances cannot
    interleave writes.

    A crash mid-write leaves either the previous file or no file at all,
    never a half-written one.
    """
    import fcntl

    target = os.fspath(path)
    parent = os.path.dirname(target) or "."
    os.makedirs(parent, exist_ok=True)
    # M-04: take an advisory lock on the target file so concurrent
    # writers from another ai-lsc process serialize.  Create a lock file
    # next to the target if the target doesn't yet exist.
    lock_path = target + ".lock"
    lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        tmp_fd, tmp_path = tempfile.mkstemp(
            prefix=".ai-lsc-",
            suffix=".tmp",
            dir=parent,
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding=encoding) as f:
                json.dump(payload, f, indent=indent)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, target)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(lock_fd)

try:
    from PySide6.QtCore import QFileSystemWatcher, Qt, QTimer
    from PySide6.QtGui import QColor, QFont, QIcon, QPalette
    from PySide6.QtWidgets import (
        QApplication,
        QDialog,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QScrollArea,
        QStackedWidget,
        QTableWidget,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

# Page widgets (guarded -- None when PySide6 absent)
try:
    from ai_lsc.ui.dialogs.stack_wizard import StackWizard
    from ai_lsc.ui.pages.chatbot_console import ChatbotConsole
    from ai_lsc.ui.pages.db_manager import DatabaseManager
    from ai_lsc.ui.pages.container_stacks_tab import ContainerStacksTab
    from ai_lsc.ui.pages.datasets_tab import DatasetsTab
    from ai_lsc.ui.pages.git_worktree_tab import GitWorktreeTab
    from ai_lsc.ui.pages.infrastructure_layer_page import (
        InfrastructureLayerPage,
    )
    from ai_lsc.ui.pages.ipc_stack_tab import IpcStackTab
    from ai_lsc.ui.pages.service_row import ServiceRow
    from ai_lsc.ui.pages.settings_page import SettingsPage
    from ai_lsc.ui.pages.skills_console import SkillsConsole
    from ai_lsc.ui.pages.tools_tab import ToolsTab
    from ai_lsc.ui.widgets.pipeline_ticker import PipelineTicker
    from ai_lsc.ui.widgets.workspace_tab import WorkspaceTab
except ImportError:
    ServiceRow = None
    SkillsConsole = None
    DatasetsTab = None
    ChatbotConsole = None
    ToolsTab = None
    DatabaseManager = None
    IpcStackTab = None
    ContainerStacksTab = None
    InfrastructureLayerPage = None
    SettingsPage = None
    GitWorktreeTab = None
    StackWizard = None


def apply_terminal_theme() -> None:
    """Apply Fusion dark palette to the entire application."""
    app = QApplication.instance()
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(22, 22, 22))
    palette.setColor(QPalette.WindowText, QColor(230, 230, 230))
    palette.setColor(QPalette.Base, QColor(14, 14, 14))
    palette.setColor(QPalette.Text, QColor(230, 230, 230))
    palette.setColor(QPalette.Button, QColor(40, 40, 40))
    palette.setColor(QPalette.ButtonText, QColor(230, 230, 230))
    app.setPalette(palette)


if _HAS_QT:

    class AILocalStackControl(QMainWindow):
        """Master controller with managed paths, registry, services, all
        tabs, IPC Stack, container exports, system audit, log
        watching, left navigation rack layout, two-stage lifecycle,
        health panel, per-layer infrastructure pages, and settings.

        v3.0 — Ankh of Jah: Verification UI, ollama server path
        detection, packaging overhaul.
        """

        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle(APP_DISPLAY_NAME)
            self.setMinimumSize(1250, 850)

            if os.path.exists(APP_ICON_FILE):
                self.setWindowIcon(QIcon(APP_ICON_FILE))

            QApplication.instance().setStyleSheet(GLOBAL_STYLE)
            apply_terminal_theme()

            # ── Base paths ───────────────────────────────────────────
            self.base_dir: str = BASE_DIR
            self.tools_root: str = os.path.join(self.base_dir, "tools")
            self.models_root: str = os.path.join(self.base_dir, "models")
            self.logs_root: str = os.path.join(self.base_dir, "logs")
            self.skills_root: str = os.path.join(self.base_dir, "skills")
            self.datasets_root: str = os.path.join(self.base_dir, "datasets")
            self.config_root: str = os.path.join(self.base_dir, "configs")
            self.workspaces_root: str = os.path.join(
                self.base_dir, "workspaces"
            )
            self.exports_root: str = os.path.join(self.base_dir, "exports")

            self._setup_environment_hierarchy()
            self._migrate_legacy_state_files()

            self.dtach_bin: str | None = find_binary("dtach-ng", "dtach")
            # License gate — checks every tool's license before the
            # installer dispatches to a subprocess.  SaaS-blocked
            # tools raise LicenseBlocked; unaccepted licenses raise
            # LicenseAcceptanceRequired (caught by ServiceRow which
            # shows the LicenseAcceptanceDialog).
            from ai_lsc.registry.license_gate import LicenseGate
            self.license_gate = LicenseGate(self.config_root)
            self.runtime = RuntimeExecutor(
                tools_root=self.tools_root,
                models_root=self.models_root,
                workspaces_root=self.workspaces_root,
                logs_root=self.logs_root,
                base_bin_dir=self.base_bin_dir,
                dtach_bin=self.dtach_bin,
                license_gate=self.license_gate,
            )
            self.config_data: dict = self._load_config()
            self.log_offsets: dict[str, int] = {}
            self.watcher = QFileSystemWatcher(self)
            self.watcher.fileChanged.connect(self.handle_live_log_update)

            self.txt_base_dir = QLineEdit(self.base_dir)
            self.txt_base_dir.setReadOnly(True)

            self.registry_mgr = RegistryManager(
                os.path.join(self.base_dir, "registry")
            )
            self.skill_resolver = (
                SkillRuntimeResolver(self.skills_root)
                if SkillRuntimeResolver is not None
                else None
            )

            self.ollama_server_dir: str = detect_ollama_server_dir(self.base_dir)
            self.ollama_models: list[str] = []
            self.aider_models: list[str] = []
            self.services: list = []
            self.is_stack_prepared: bool = False

            self.view_map: dict[str, int] = {}

            # ── First-run: no popup wizard — the main UI IS the wizard.
            # The Infrastructure layers have checkboxes for tool selection.
            # If no pipeline_state.json exists, we create a default one
            # so the app boots into the Monitor view cleanly.
            state_file = os.path.join(self.config_root, STATE_FILE_NAME)
            if not os.path.exists(state_file):
                os.makedirs(self.config_root, exist_ok=True)
                _atomic_write_json(state_file, {
                    "session_name": "ai_lsc",
                    "base_dir": self.base_dir,
                    "active_tools": [],
                    "port_map": {},
                    "stack_ready": False,
                    "source": "first_run",
                })

            # ── Build UI then bootstrap ────────────────────────────────
            self._build_ui()
            self.refresh_models()

            QTimer.singleShot(1200, self.run_system_audit)

            self.status_timer = QTimer(self)
            self.status_timer.timeout.connect(self.poll_services)
            self.status_timer.start(3000)
            QTimer.singleShot(500, self.load_existing_logs)

        # ───────────────────────────────────────────────────────────────
        # Environment setup
        # ───────────────────────────────────────────────────────────────

        def _migrate_legacy_state_files(self) -> None:
            """One-time migration to the canonical configs/ directory.

            v3.1.1b moved app state into <base_dir>/configs/.  Older
            installs kept files in three legacy locations:
              * <base_dir>/config/           (pipeline_state.json, license_approvals.json)
              * <base_dir>/controller_config.json  (config persisted at the root)
            Files are moved only when no newer copy exists in configs/;
            emptied legacy dirs are removed.  Never raises.
            """
            import shutil

            legacy_dir = os.path.join(self.base_dir, "config")
            candidates: list[tuple[str, str]] = []
            if os.path.isdir(legacy_dir):
                for fname in os.listdir(legacy_dir):
                    if fname.endswith(".json"):
                        candidates.append(
                            (os.path.join(legacy_dir, fname), fname)
                        )
            root_cfg = os.path.join(self.base_dir, CONFIG_FILE)
            if os.path.isfile(root_cfg):
                candidates.append((root_cfg, CONFIG_FILE))

            moved: list[str] = []
            for src_path, fname in candidates:
                dst_path = os.path.join(self.config_root, fname)
                try:
                    if not os.path.exists(dst_path):
                        shutil.move(src_path, dst_path)
                        moved.append(fname)
                    elif os.path.getmtime(src_path) > os.path.getmtime(dst_path):
                        # legacy copy is newer — keep it, drop the old one
                        shutil.move(
                            src_path, dst_path + ".legacy.bak"
                        )
                        moved.append(fname + " (kept as .legacy.bak)")
                    else:
                        os.remove(src_path)
                except OSError:
                    continue

            # remove the legacy config/ dir when it is now empty
            try:
                if os.path.isdir(legacy_dir) and not os.listdir(legacy_dir):
                    os.rmdir(legacy_dir)
            except OSError:
                pass

            if moved:
                from ai_lsc.utils.logging import get_logger
                get_logger(__name__).info(
                    "Migrated legacy state files to %s: %s",
                    self.config_root, ", ".join(moved),
                )

        def _setup_environment_hierarchy(self) -> None:
            for d in REQUIRED_DIRS:
                os.makedirs(
                    os.path.join(self.base_dir, d), exist_ok=True
                )
            uv_bin = os.path.join(self.tools_root, ".uv", "bin")
            npm_bin = os.path.join(self.tools_root, "npm_globals", "bin")
            # Deliberately no ~/.local/bin — all managed installs go through tools_root
            self.base_bin_dir = ":".join(
                filter(None, [uv_bin, npm_bin])
            )

        # ───────────────────────────────────────────────────────────────
        # LEFT NAVIGATION RACK LAYOUT
        # ───────────────────────────────────────────────────────────────

        def _build_ui(self) -> None:
            central = QWidget()
            self.setCentralWidget(central)
            main_layout = QHBoxLayout(central)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # --- Left Sidebar ---
            self.sidebar_frame = QFrame()
            self.sidebar_frame.setFixedWidth(260)
            self.sidebar_frame.setStyleSheet(
                "background-color: #111111; border-right: 1px solid #252525;"
            )
            sidebar_layout = QVBoxLayout(self.sidebar_frame)
            sidebar_layout.setContentsMargins(0, 0, 0, 0)

            # Brand header
            brand_frame = QFrame()
            brand_frame.setStyleSheet(
                "background-color: #161616; "
                "border-bottom: 1px solid #252525;"
            )
            brand_layout = QVBoxLayout(brand_frame)
            lbl_logo = QLabel(f"AI-LSC v{APP_VERSION}")
            lbl_logo.setFont(QFont("Segoe UI", 13, QFont.Bold))
            lbl_logo.setStyleSheet(
                "color: #2ecc71; padding: 10px 5px 10px 10px;"
            )
            brand_layout.addWidget(lbl_logo)
            sidebar_layout.addWidget(brand_frame)

            # Base dir control inside sidebar
            base_dir_frame = QFrame()
            base_dir_frame.setStyleSheet(
                "padding: 5px; border-bottom: 1px solid #252525;"
            )
            base_dir_layout = QVBoxLayout(base_dir_frame)
            lbl_base = QLabel("Ecosystem Target Base Directory:")
            lbl_base.setFont(QFont("Segoe UI", 8))
            lbl_base.setStyleSheet("color: #bdc3c7;")
            self.txt_base_dir.setStyleSheet(
                "background-color: #1a1a1a; border: 1px solid #333; "
                "color: #fff; font-family: Consolas;"
            )
            base_dir_layout.addWidget(lbl_base)
            base_dir_layout.addWidget(self.txt_base_dir)
            sidebar_layout.addWidget(base_dir_frame)

            # Navigation tree
            self.nav_tree = QTreeWidget()
            self.nav_tree.setHeaderHidden(True)
            self.nav_tree.setAnimated(True)
            self.nav_tree.setStyleSheet(SIDEBAR_TREE_STYLE)
            self.nav_tree.itemClicked.connect(self.on_nav_item_clicked)
            sidebar_layout.addWidget(self.nav_tree)

            main_layout.addWidget(self.sidebar_frame)

            # --- Right Workspace (ticker on top + page stack below) ---
            # The PipelineTicker sits above the QStackedWidget so it
            # is visible on every page.  It shows the wiring topology
            # of the currently-staged tool set.
            workspace_frame = QFrame()
            workspace_frame.setObjectName("WorkspaceFrame")
            workspace_layout = QVBoxLayout(workspace_frame)
            workspace_layout.setContentsMargins(0, 0, 0, 0)
            workspace_layout.setSpacing(0)

            self.pipeline_ticker = PipelineTicker()
            self.pipeline_ticker.tool_clicked.connect(self._on_ticker_tool_clicked)
            workspace_layout.addWidget(self.pipeline_ticker)

            self.nav_stack = QStackedWidget()
            workspace_layout.addWidget(self.nav_stack)

            main_layout.addWidget(workspace_frame)

            # Build all pages and the navigation tree
            self._build_monitor_page()
            self._build_verification_page()
            self._build_infrastructure_pages()
            self._build_stack_editor_page()
            self._build_container_stacks_page()
            self._build_data_volumes_page()
            self._build_skills_console_page()
            self._build_models_page()
            self._build_datasets_lib_page()
            self._build_stacks_lib_page()
            self._build_workspace_chat_page()
            self._build_workspace_orchestration_page()
            self._build_settings_page()
            self._build_db_manager_page()
            self._build_git_worktree_page()
            self._build_about_page()

            # Refresh ticker + workspace now that pages exist
            self._refresh_pipeline_ticker()
            self._refresh_workspace_tab()

            self._build_rack_navigation()

            # Select the first Infrastructure layer initially
            # (the main UI IS the wizard — show tool selection first)
            first_infra = (
                f"infra_{NAV_LAYER_ORDER[0].lower().replace(' ', '_')}"
                if NAV_LAYER_ORDER
                else "dashboard"
            )
            self.nav_stack.setCurrentIndex(
                self.view_map.get(first_infra, 0)
            )

        def _build_rack_navigation(self) -> None:
            """Populate the left navigation tree with all view targets.

            New layout — the Infrastructure section IS the wizard:
              - Infrastructure (10 layers with tool checkboxes)
              - Stack Editor (templates + flow + lifecycle + compile)
              - Monitor (active metrics only)
              - Verification
              - Deployment Targets
              - Libraries (Models, Datasets, Stacks)
              - Skills, Chat, Workspace, Git Sources, DB Manager, Settings, About
            """
            self.nav_tree.clear()

            # Infrastructure layers (THE WIZARD)
            item_infra = QTreeWidgetItem(self.nav_tree)
            item_infra.setText(0, "   Infrastructure")
            item_infra.setExpanded(True)

            for layer in NAV_LAYER_ORDER:
                child = QTreeWidgetItem(item_infra)
                child.setText(0, f"    {layer}")
                code = f"infra_{layer.lower().replace(' ', '_')}"
                child.setData(0, Qt.UserRole, code)

            # Stack Editor (templates + flow builder + lifecycle)
            item_tools = QTreeWidgetItem(self.nav_tree)
            item_tools.setText(0, "   Stack Editor")
            item_tools.setData(0, Qt.UserRole, "stack_editor")

            # Monitor (active metrics only)
            item_dash = QTreeWidgetItem(self.nav_tree)
            item_dash.setText(0, "   Monitor")
            item_dash.setData(0, Qt.UserRole, "dashboard")

            # Verification
            item_verify = QTreeWidgetItem(self.nav_tree)
            item_verify.setText(0, "   Verification")
            item_verify.setData(0, Qt.UserRole, "verification")

            # Deployment Targets
            item_cont = QTreeWidgetItem(self.nav_tree)
            item_cont.setText(0, "   Deployment Targets")
            item_cont.setData(0, Qt.UserRole, "container_stacks")

            # Libraries
            item_libs = QTreeWidgetItem(self.nav_tree)
            item_libs.setText(0, "   Libraries")
            item_libs.setExpanded(True)

            lib_views = [
                ("Models", "lib_models"),
                ("Datasets", "lib_datasets"),
                ("Stacks", "lib_stacks"),
            ]
            for label, code in lib_views:
                child = QTreeWidgetItem(item_libs)
                child.setText(0, f"    {label}")
                child.setData(0, Qt.UserRole, code)

            # Skills
            item_skills = QTreeWidgetItem(self.nav_tree)
            item_skills.setText(0, "   Skills")
            item_skills.setData(0, Qt.UserRole, "skills_console")

            # Chat
            item_work = QTreeWidgetItem(self.nav_tree)
            item_work.setText(0, "   Chat")
            item_work.setData(0, Qt.UserRole, "workspace_chat")

            # Workspace (peek-style orchestration)
            item_workspace = QTreeWidgetItem(self.nav_tree)
            item_workspace.setText(0, "   Workspace")
            item_workspace.setData(0, Qt.UserRole, "workspace_orchestration")

            # Git Repo Manager
            item_git = QTreeWidgetItem(self.nav_tree)
            item_git.setText(0, "   Git Repo Manager")
            item_git.setData(0, Qt.UserRole, "git_worktree")

            # DB Manager
            item_db = QTreeWidgetItem(self.nav_tree)
            item_db.setText(0, "   DB Manager")
            item_db.setData(0, Qt.UserRole, "db_manager")

            # Settings
            item_set = QTreeWidgetItem(self.nav_tree)
            item_set.setText(0, "   Settings")
            item_set.setData(0, Qt.UserRole, "settings")

            # About
            item_about = QTreeWidgetItem(self.nav_tree)
            item_about.setText(0, "   About")
            item_about.setData(0, Qt.UserRole, "about")

        def on_nav_item_clicked(self, item, column) -> None:
            target = item.data(0, Qt.UserRole)
            if not target or target not in self.view_map:
                return
            self.nav_stack.setCurrentIndex(self.view_map[target])

            # DB Manager gets the full workspace (hide ticker).
            self.pipeline_ticker.setVisible(target != "db_manager")

            nav_sync_dispatch = {
                "workspace_chat": self.sync_chat_workspace_dropdown,
                "stack_editor": self.ipc_stack_tab.refresh,
                "workspace_orchestration": self._refresh_workspace_tab,
                "db_manager": (
                    self.db_manager_tab.refresh
                    if DatabaseManager is not None
                    else None
                ),
                "git_worktree": (
                    self.git_worktree_tab.refresh
                    if GitWorktreeTab is not None
                    else None
                ),
            }
            handler = nav_sync_dispatch.get(target)
            if handler:
                handler()

            # Refresh infrastructure layer active-services on navigate
            if target and target.startswith("infra_"):
                idx = self.view_map[target]
                page = self.nav_stack.widget(idx)
                if hasattr(page, 'refresh_active_services'):
                    page.refresh_active_services()

        # ───────────────────────────────────────────────────────────────
        # PAGE BUILDERS
        # ───────────────────────────────────────────────────────────────

        def _build_monitor_page(self) -> None:
            """Build the simplified Monitor — active metrics only.

            Shows: health score, active service status rows, and the
            real-time log console.  Lifecycle controls and the wizard
            button have been moved to the Stack Editor.
            """
            page = QWidget()
            layout = QVBoxLayout(page)

            hdr = QHBoxLayout()
            lbl = QLabel("<b>Monitor — Active Metrics</b>")
            lbl.setFont(QFont("Segoe UI", 14))
            hdr.addWidget(lbl)
            hdr.addStretch()

            btn_audit = QPushButton("Run System Audit")
            btn_audit.clicked.connect(self.run_system_audit)
            hdr.addWidget(btn_audit)
            layout.addLayout(hdr)

            # Health Score Panel
            self.health_card = QFrame()
            self.health_card.setStyleSheet(
                "background-color: #161616; border: 1px solid #27ae60; "
                "border-radius: 6px; padding: 10px;"
            )
            health_layout = QVBoxLayout(self.health_card)

            health_header = QHBoxLayout()
            self.lbl_health_score = QLabel(
                "Stack Health: <b>--</b>"
            )
            self.lbl_health_score.setFont(QFont("Segoe UI", 12))
            self.lbl_health_score.setStyleSheet("color: #2ecc71;")
            health_header.addWidget(self.lbl_health_score)
            health_header.addStretch()
            health_layout.addLayout(health_header)

            self.lbl_health_details = QLabel(
                "No active services."
            )
            self.lbl_health_details.setFont(QFont("Consolas", 9))
            self.lbl_health_details.setStyleSheet("color: #bdc3c7;")
            self.lbl_health_details.setWordWrap(True)
            health_layout.addWidget(self.lbl_health_details)
            layout.addWidget(self.health_card)

            # Active Services Row (only shows RUNNING services)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; }")
            scroll_content = QWidget()
            self.services_layout = QVBoxLayout(scroll_content)
            self.services_layout.addStretch()
            scroll.setWidget(scroll_content)
            layout.addWidget(scroll, stretch=2)

            # Telemetry Log Console
            lbl_log_hdr = QLabel(
                "<b>System Log Console</b>"
            )
            layout.addWidget(lbl_log_hdr)

            self.log_box = QTextEdit()
            self.log_box.setFont(QFont("Consolas", 10))
            self.log_box.setReadOnly(True)
            self.log_box.document().setMaximumBlockCount(800)
            self.log_box.setStyleSheet(
                "background-color: #0d0d0d; color: #cfd8dc; padding: 8px;"
            )
            layout.addWidget(self.log_box, stretch=1)

            idx = self.nav_stack.addWidget(page)
            self.view_map["dashboard"] = idx
            self._populate_services()

        def _build_verification_page(self) -> None:
            """Build the per-tool installation verification dashboard."""
            from ai_lsc.ui.pages.verification_tab import VerificationTab

            registry_data = self.registry_mgr.get_all_tools()
            page = VerificationTab(
                registry=registry_data,
                tools_root=self.tools_root,
                base_dir=self.base_dir,
            )
            idx = self.nav_stack.addWidget(page)
            self.view_map["verification"] = idx
            self.verification_tab = page

        def _build_infrastructure_pages(self) -> None:
            """Build a filtered ServiceRow page for each 10-Layer stratum."""
            for layer in NAV_LAYER_ORDER:
                infra_page = InfrastructureLayerPage(self, layer)
                idx = self.nav_stack.addWidget(infra_page)
                code = f"infra_{layer.lower().replace(' ', '_')}"
                self.view_map[code] = idx

        def _build_stack_editor_page(self) -> None:
            """Build the enhanced Stack Editor page.

            Replaces the old _build_tools_registry_page.  The new editor
            combines: template selector, execution flow builder,
            dependency validation, lifecycle engine controls, and compile.
            The separate ToolsTab is no longer needed as a nav target
            (tools are merged into the Infrastructure layer pages).
            """
            self.ipc_stack_tab = IpcStackTab(self)
            self.ipc_stack_tab.refresh()
            idx = self.nav_stack.addWidget(self.ipc_stack_tab)
            self.view_map["stack_editor"] = idx
            # Still create ToolsTab for PipelineTicker jump-to-tool
            # navigation, but do NOT register it in view_map (no nav
            # item for it).
            if ToolsTab is not None:
                self.tools_tab = ToolsTab(self)
                self.tools_tab.refresh()

        def _build_container_stacks_page(self) -> None:
            self.stacks_tab = ContainerStacksTab(self)
            idx = self.nav_stack.addWidget(self.stacks_tab)
            self.view_map["container_stacks"] = idx

        def _build_data_volumes_page(self) -> None:
            self.datasets_tab = DatasetsTab(self)
            idx = self.nav_stack.addWidget(self.datasets_tab)
            self.view_map["data_volumes"] = idx

        def _build_skills_console_page(self) -> None:
            self.skills_console_tab = SkillsConsole(self)
            idx = self.nav_stack.addWidget(self.skills_console_tab)
            self.view_map["skills_console"] = idx

        def _build_models_page(self) -> None:
            page = QWidget()
            layout = QVBoxLayout(page)
            lbl = QLabel("<b>Ecosystem Model Repository Viewer</b>")
            lbl.setFont(QFont("Segoe UI", 14))
            layout.addWidget(lbl)

            self.models_table = QTableWidget(0, 3)
            self.models_table.setHorizontalHeaderLabels([
                "Model Identifier", "Context Window", "Size"
            ])
            self.models_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.Stretch
            )
            layout.addWidget(self.models_table)

            idx = self.nav_stack.addWidget(page)
            self.view_map["lib_models"] = idx

        def _build_datasets_lib_page(self) -> None:
            page = QWidget()
            layout = QVBoxLayout(page)
            lbl = QLabel(
                "<b>Ecosystem Dataset Repository Viewer</b>"
            )
            lbl.setFont(QFont("Segoe UI", 14))
            layout.addWidget(lbl)

            table = QTableWidget(0, 3)
            table.setHorizontalHeaderLabels([
                "Dataset", "Format", "Status"
            ])
            table.horizontalHeader().setSectionResizeMode(
                QHeaderView.Stretch
            )
            layout.addWidget(table)

            idx = self.nav_stack.addWidget(page)
            self.view_map["lib_datasets"] = idx

        def _build_stacks_lib_page(self) -> None:
            page = QWidget()
            layout = QVBoxLayout(page)
            lbl = QLabel(
                "<b>Ecosystem Stack Exports Repository</b>"
            )
            lbl.setFont(QFont("Segoe UI", 14))
            layout.addWidget(lbl)

            self.stacks_lib_list = QStackedWidget()
            # NOTE: monolith used QListWidget here, but the variable
            # name was stacks_lib_list.  Keeping QListWidget semantics.
            from PySide6.QtWidgets import QListWidget
            self.stacks_lib_list = QListWidget()
            layout.addWidget(self.stacks_lib_list)

            idx = self.nav_stack.addWidget(page)
            self.view_map["lib_stacks"] = idx

        def _build_workspace_chat_page(self) -> None:
            self.chatbot_console_tab = ChatbotConsole(self)
            idx = self.nav_stack.addWidget(self.chatbot_console_tab)
            self.view_map["workspace_chat"] = idx

        def _build_workspace_orchestration_page(self) -> None:
            """Peek-style orchestration surface — one sub-tab per
            active tool, web tools embedded via QWebEngineView, CLI
            tools attached via tmux."""
            self.workspace_tab = WorkspaceTab(self)
            self.workspace_tab.start_tool_requested.connect(
                self._on_workspace_start_tool
            )
            idx = self.nav_stack.addWidget(self.workspace_tab)
            self.view_map["workspace_orchestration"] = idx

        # ── PipelineTicker + Workspace refresh ───────────────────────

        def _active_tool_ids(self) -> list[str]:
            """Return the active_tools list from the pipeline state file."""
            state_path = self._get_active_state_file()
            if not state_path:
                return []
            try:
                with open(state_path, encoding="utf-8") as f:
                    return json.load(f).get("active_tools", [])
            except (OSError, ValueError, json.JSONDecodeError):
                return []

        def _refresh_pipeline_ticker(self) -> None:
            """Rebuild the ticker's edges from the active tool set +
            the wiring topology in stack/connections.py."""
            from ai_lsc.ui.widgets.pipeline_ticker import _Edge
            try:
                from ai_lsc.stack.connections import STACK_WIRINGS
            except ImportError:
                STACK_WIRINGS = {}

            active = set(self._active_tool_ids())
            running = {s.tool_id for s in self.services if s.is_running_now()}

            # Pass 1: collect every (consumer, provider, interface_id)
            # triple where both endpoints are in the active set.
            edges: list[_Edge] = []
            tools_with_edges: set[str] = set()
            for tool_id in active:
                wiring = STACK_WIRINGS.get(tool_id)
                if wiring is None:
                    continue
                for conn in wiring.connections:
                    if (
                        conn.target_tool in active
                        and conn.target_tool != tool_id
                    ):
                        edges.append(_Edge(
                            provider=conn.target_tool,
                            consumer=tool_id,
                            interface_id=conn.interface_id,
                            purpose=conn.purpose,
                            running_provider=conn.target_tool in running,
                            running_consumer=tool_id in running,
                        ))
                        tools_with_edges.add(tool_id)
                        tools_with_edges.add(conn.target_tool)

            # Pass 2: any active tool that didn't appear in any edge is
            # an orphan from the ticker's POV (no in-stack wiring to
            # another active tool).  This catches both:
            #   - tools with no STACK_WIRINGS entry at all
            #   - tools with a wiring but all of their connections
            #     target tools that aren't in the active set
            orphans = [tid for tid in active if tid not in tools_with_edges]
            # De-duplicate + sort for stable display
            orphans = sorted(set(orphans))

            self.pipeline_ticker.set_edges(edges, orphans)

        def _on_ticker_tool_clicked(self, tool_id: str) -> None:
            """User clicked a tool pill in the ticker — jump to the
            tool's infrastructure layer page and highlight it."""
            meta = self.registry_mgr.get_tool(tool_id)
            if not meta:
                return
            layer = meta.get("layer", "")
            code = f"infra_{layer.lower().replace(' ', '_')}"
            target_view = code if code in self.view_map else "stack_editor"
            if target_view not in self.view_map:
                return
            self.nav_stack.setCurrentIndex(self.view_map[target_view])
            # If we landed on an infra page, try to highlight the tool
            page = self.nav_stack.widget(self.view_map[target_view])
            if hasattr(page, 'checkboxes') and tool_id in page.checkboxes:
                page.checkboxes[tool_id].setFocus()
            elif hasattr(page, 'highlight_tool'):
                page.highlight_tool(tool_id)

        def _refresh_workspace_tab(self) -> None:
            """Rebuild the Workspace tab's sub-tabs from the active
            tool set."""
            if not hasattr(self, "workspace_tab"):
                return
            active = self._active_tool_ids()
            running = [s.tool_id for s in self.services if s.is_running_now()]
            # Pull port_map from pipeline state
            state_path = self._get_active_state_file()
            port_map: dict[str, int | str] = {}
            if state_path:
                try:
                    with open(state_path, encoding="utf-8") as f:
                        port_map = json.load(f).get("port_map", {})
                except (OSError, ValueError, json.JSONDecodeError):
                    pass
            # Build the registry dict the workspace_tab expects
            registry = {
                tid: self.registry_mgr.get_tool(tid) or {}
                for tid in active
                if not tid.startswith("skill:")
            }
            from ai_lsc.runtime.tmux import TmuxManager
            self.workspace_tab.refresh(
                active_tools=[t for t in active if not t.startswith("skill:")],
                registry=registry,
                running_tools=running,
                port_map=port_map,
                tmux_session=TmuxManager.SESSION,
            )

        def _on_workspace_start_tool(self, tool_id: str) -> None:
            """User clicked 'Start tool' on a workspace sub-tab.
            Find the matching ServiceRow and trigger its start_service."""
            for s in self.services:
                if s.tool_id == tool_id:
                    s.start_service()
                    # Refresh the workspace tab after a short delay
                    # so the newly-started tool's sub-tab switches from
                    # placeholder to live view.
                    QTimer.singleShot(1500, self._refresh_workspace_tab)
                    return

        def _build_settings_page(self) -> None:
            self.settings_page = SettingsPage(self)
            idx = self.nav_stack.addWidget(self.settings_page)
            self.view_map["settings"] = idx

        def _build_db_manager_page(self) -> None:
            if DatabaseManager is not None:
                self.db_manager_tab = DatabaseManager(self)
                idx = self.nav_stack.addWidget(self.db_manager_tab)
                self.view_map["db_manager"] = idx

        def _build_git_worktree_page(self) -> None:
            self.git_worktree_tab = GitWorktreeTab(self)
            idx = self.nav_stack.addWidget(self.git_worktree_tab)
            self.view_map["git_worktree"] = idx

        def _build_about_page(self) -> None:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(30, 20, 30, 20)

            header = QHBoxLayout()
            lbl_title = QLabel("<b>AI-LSC v3.1 — Ankh of Jah</b>")
            lbl_title.setFont(QFont("Segoe UI", 16))
            header.addWidget(lbl_title)
            header.addStretch()
            layout.addLayout(header)

            layout.addSpacing(10)

            about_text = QLabel(
                "<p>AI Local Stack Control is a native-first, metadata-driven "
                "infrastructure manager for local AI systems. It treats AI "
                "software as reusable infrastructure rather than isolated "
                "applications, enabling reproducible deployments, validation, "
                "monitoring, and export of complete AI environments.</p>"
                "<br><br>"
                "<p><b>Intended Work Routines:</b></p>"
                "<ul>"
                "<li><b>Compose</b> — Infrastructure sidebar provides "
                "per-layer tool selection (the main UI is the wizard). "
                "Stack Editor adds templates, flow ordering, and lifecycle "
                "controls.</li>"
                "<li><b>Monitor</b> — Active-metrics dashboard shows "
                "real-time service health and system logs.</li>"
                "<li><b>Manage</b> — Each infrastructure layer shows "
                "active service controls for install, configure, start, "
                "and stop.</li>"
                "<li><b>Export</b> — Deployment Targets compiles validated "
                "stacks to Podman, Docker, or LXC containers.</li>"
                "<li><b>Verify</b> — Verification tab runs compliance checks "
                "on every registered tool.</li>"
                "<li><b>Skills</b> — Skills Console manages Ollama modelfiles "
                "and model capabilities.</li>"
                "</ul>"
                "<br>"
                "<p><b>Architecture:</b> 10-Layer model | Capability-driven | "
                "Metadata-registry | Stack Recipes | Multi-runtime export</p>"
                "<br>"
                "<p>Author: <b>Jeremy Anderson</b> "
                "&lt;info@dcos.net&gt;</p>"
                "<p>Source: "
                "<a href='https://git.dcos.net/dcosnet/ai-lsc' "
                "style='color: #3498db;'>git.dcos.net/dcosnet/ai-lsc</a></p>"
            )
            about_text.setWordWrap(True)
            about_text.setStyleSheet(
                "color: #bdc3c7; font-size: 13px; line-height: 1.6;"
            )
            about_text.setTextFormat(Qt.TextFormat.RichText)
            about_text.setOpenExternalLinks(True)
            layout.addWidget(about_text)
            layout.addStretch()

            idx = self.nav_stack.addWidget(page)
            self.view_map["about"] = idx

        # ───────────────────────────────────────────────────────────────
        # STATE MANAGEMENT
        # ───────────────────────────────────────────────────────────────

        def _get_active_state_file(self) -> str | None:
            """Return the most relevant state file:
            ``pipeline.json`` if it exists, otherwise
            ``pipeline_state.json``."""
            pipe_file = os.path.join(
                self.config_root, PIPELINE_FILE_NAME
            )
            if os.path.exists(pipe_file):
                return pipe_file
            state_file = os.path.join(
                self.config_root, STATE_FILE_NAME
            )
            if os.path.exists(state_file):
                return state_file
            return None

        def _populate_services(self) -> None:
            state_path = self._get_active_state_file()
            if not state_path:
                return

            # Clear existing service rows
            for i in reversed(range(self.services_layout.count())):
                w = self.services_layout.itemAt(i).widget()
                if w:
                    w.setParent(None)
            watches = self.watcher.files()
            if watches:
                self.watcher.removePaths(watches)
            self.log_offsets.clear()
            self.services.clear()

            with open(state_path, encoding="utf-8") as f:
                state = json.load(f)

            for tool_id in state.get("active_tools", []):
                meta = (
                    self.registry_mgr.get_tool(tool_id)
                    if not tool_id.startswith("skill:")
                    else {}
                )
                port = state.get("port_map", {}).get(tool_id)
                row = ServiceRow(self, tool_id, port, meta)
                self.services.append(row)
                self.services_layout.insertWidget(
                    self.services_layout.count() - 1, row
                )
            self.load_existing_logs()
            # Refresh the ticker + workspace tab so they reflect the
            # newly-populated service rows.
            self._refresh_pipeline_ticker()
            self._refresh_workspace_tab()

        # ── Tab/page synchronization ───────────────────────────────────

        def sync_chat_workspace_dropdown(self) -> None:
            checked_skills = (
                self.skills_console_tab.get_checked_skills()
            )
            skills_map = (
                self.skills_console_tab.get_all_skills_map()
            )
            combined = list(dict.fromkeys(
                [m.replace("ollama/", "") for m in self.aider_models]
                + self.ollama_models
                + checked_skills
            ))
            self.chatbot_console_tab.update_dropdown_arrays(
                combined, list(skills_map.keys())
            )

        # ── Ollama port resolution ────────────────────────────────────

        def resolve_ollama_port(self) -> int:
            state_path = self._get_active_state_file()
            if state_path:
                try:
                    with open(state_path) as f:
                        port = (
                            json.load(f)
                            .get("port_map", {})
                            .get("ollama")
                        )
                    if port is not None:
                        return int(port)
                except Exception:
                    pass
            ollama_row = next(
                (s for s in self.services
                 if s.is_ollama and s.txt_port),
                None,
            )
            raw = (
                ollama_row.txt_port.text().strip()
                if ollama_row
                else "11434"
            )
            return int(raw)

        # ── Model discovery (dual source) ──────────────────────────────

        def refresh_models(self) -> None:
            env = enriched_env(self.base_bin_dir)
            try:
                res = subprocess.run(
                    ["aider", "--list-models", "ollama"],
                    capture_output=True, text=True,
                    timeout=4.0, env=env,
                )
                self.aider_models = sorted({
                    line.strip().replace("- ", "")
                    for line in res.stdout.splitlines()
                    if line.strip().startswith("- ")
                })
            except Exception:
                self.aider_models = []

            ollama_env_vars = ollama_models_dir(self.base_dir)
            env["OLLAMA_MODELS"] = ollama_env_vars
            try:
                res = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True, text=True,
                    env=env, timeout=3.0,
                )
                self.ollama_models = [
                    line.split()[0]
                    for line in res.stdout.splitlines()[1:]
                    if line.strip()
                ]
            except Exception:
                self.ollama_models = []

            for s in self.services:
                s.hydrate_models(self.ollama_models, self.aider_models)

        def refresh_all_models(self) -> None:
            self.refresh_models()
            self.sync_chat_workspace_dropdown()
            self._refresh_modelfile_library()

        # ── Polling ───────────────────────────────────────────────────

        def _update_health_score(self) -> None:
            """UX-11: Compute health score from actual service states."""
            if not self.services:
                self.lbl_health_score.setText(
                    "Stack Health: <b>0 tools active</b>"
                )
                self.lbl_health_details.setText(
                    "Select tools from the Infrastructure layers to "
                    "build your stack."
                )
                return
            running = sum(1 for s in self.services if s.is_running_now())
            total = len(self.services)
            pct = int(running / total * 100) if total else 0
            color = (
                "#2ecc71" if pct >= 70
                else "#e67e22" if pct >= 40
                else "#e74c3c"
            )
            self.lbl_health_score.setText(
                f"Stack Health: <b>{pct}%</b>  "
                f"({running}/{total} services running)"
            )
            self.lbl_health_score.setStyleSheet(f"color: {color};")

            # Build live detail string from active services
            running_names = [
                s.tool_id for s in self.services if s.is_running_now()
            ]
            offline_names = [
                s.tool_id for s in self.services
                if not s.is_running_now()
            ]
            parts = []
            if running_names:
                parts.append(
                    "ONLINE: " + ", ".join(running_names[:8])
                )
                if len(running_names) > 8:
                    parts.append(
                        f" +{len(running_names) - 8} more"
                    )
            if offline_names:
                parts.append(
                    "OFFLINE: " + ", ".join(offline_names[:5])
                )
                if len(offline_names) > 5:
                    parts.append(
                        f" +{len(offline_names) - 5} more"
                    )
            self.lbl_health_details.setText("  |  ".join(parts) if parts else "No active services.")

        def poll_services(self) -> None:
            for s in self.services:
                s.update_status()
            self._update_health_score()
            # Refresh the ticker every poll cycle so running-state
            # color changes (stopped → running) propagate.  The
            # workspace tab refreshes less often — only when a service
            # is started/stopped, not on every poll.
            self._refresh_pipeline_ticker()

        # ── Logging (dict-driven colour) ───────────────────────────────

        def log(self, text: str, source: str = "System") -> None:
            ts = datetime.now().strftime("%H:%M:%S")
            color = LOG_SOURCE_COLORS.get(source, LOG_COLOR_DEFAULT)
            clean = text.replace("<", "&lt;").replace(">", "&gt;")
            self.log_box.append(
                f'<span style="color:{color};">'
                f'[{ts}] [{source}] {clean}</span>'
            )
            self.log_box.ensureCursorVisible()

        # ── Two-Stage Stack Lifecycle ──────────────────────────────────

        def execute_stack_preparation(self) -> None:
            self.log(
                "[DEMO] Stage 1: Simulated preparation sequence...",
                "Lifecycle",
            )
            self.is_stack_prepared = False
            # Disable the activate button on the Stack Editor
            if hasattr(self, 'ipc_stack_tab'):
                self.ipc_stack_tab.btn_activate.setEnabled(False)
                self.ipc_stack_tab.btn_prepare.setStyleSheet(
                    "background-color: #2980b9; color: white; "
                    "font-weight: bold; padding: 8px; border-radius: 4px;"
                )

            stages = [
                "Resolving dependency graph",
                "Downloading source artifacts",
                "Compiling build targets",
                "Verifying hash allocations",
                "Benchmarking architecture",
                "Registering OCI entities",
            ]
            for idx, stage in enumerate(stages):
                QTimer.singleShot(
                    (idx + 1) * 600,
                    lambda s=stage: self.log(
                        f"Preparation step complete: {s}.",
                        "Lifecycle",
                    ),
                )

            def finalize():
                self.is_stack_prepared = True
                if hasattr(self, 'ipc_stack_tab'):
                    self.ipc_stack_tab.btn_activate.setEnabled(True)
                    self.ipc_stack_tab.btn_prepare.setStyleSheet(
                        "background-color: #27ae60; color: white; "
                        "font-weight: bold; padding: 8px; border-radius: 4px;"
                    )
                self.log(
                    "Stack preparation complete (simulated). "
                    "Activation pipeline is now unlocked.",
                    "Lifecycle",
                )

            QTimer.singleShot((len(stages) + 1) * 600, finalize)

        def execute_stack_activation(self) -> None:
            if not self.is_stack_prepared:
                self.log(
                    "Lifecycle Guard: Stack must be prepared first.",
                    "Lifecycle",
                )
                return
            self.log(
                "[DEMO] Stage 2: Simulated activation...",
                "Lifecycle",
            )
            for i, svc in enumerate(self.services):
                QTimer.singleShot(
                    (i + 1) * 300,
                    lambda s=svc: s.start_service(),
                )

        def execute_stack_validation(self) -> None:
            self.log(
                "[DEMO] Simulated health diagnostics (not connected to real infrastructure)...",
                "SelfHeal",
            )
            checks = [
                "Ports Matrix Check: Validating binding conflicts..."
                " [ OK ]",
                ("Dependencies Resolution: Cross-checking 10-Layer "
                 "topology... [ OK ]"),
                "GPU Compute Availability: CUDA core compatibility..."
                " [ OK ]",
                "RAM Threshold Allocation: System headroom "
                "assessment... [ OK ]",
                "Storage Permissions: base dir volume boundaries..."
                " [ OK ]",
                "Container Compatibility: Podman runtime profiling..."
                " [ OK ]",
            ]
            for check in checks:
                self.log(check, "Audit")
            self.log(
                "Infrastructure audit complete. No drift detected.",
                "Audit",
            )

        # ── System Audit ───────────────────────────────────────────────

        def run_system_audit(self) -> None:
            expected_pages = {
                "dashboard", "stack_editor",
                "container_stacks", "data_volumes", "skills_console",
                "workspace_chat", "settings",
            }
            missing_pages = expected_pages - set(self.view_map.keys())

            repair_dispatch = {
                "stack_editor": lambda: (
                    setattr(
                        self,
                        "ipc_stack_tab",
                        IpcStackTab(self),
                    ),
                    self.ipc_stack_tab.refresh(),
                    self._register_page(
                        "stack_editor", self.ipc_stack_tab
                    ),
                ),
                "container_stacks": lambda: (
                    setattr(
                        self, "stacks_tab", ContainerStacksTab(self)
                    ),
                    self._register_page(
                        "container_stacks", self.stacks_tab
                    ),
                ),
            }
            for page_name in missing_pages:
                handler = repair_dispatch.get(page_name)
                if handler:
                    handler()

            # Drift detection
            state_path = self._get_active_state_file()
            drift: list[str] = []
            if state_path:
                try:
                    with open(state_path) as f:
                        state = json.load(f)
                    git_types = {"git", "git_node"}
                    drift = [
                        tid
                        for tid in state.get("active_tools", [])
                        if not tid.startswith("skill:")
                        and self.registry_mgr.get_tool(tid)
                                .get("installer", {})
                                .get("type") in git_types
                        and not os.path.exists(
                            os.path.join(self.tools_root, tid)
                        )
                    ]
                except Exception:
                    pass

            if drift:
                self.log(
                    "DRIFT WARNING: Tools declared but missing on "
                    f"disk: {drift}",
                    "Audit",
                )
            else:
                self.log(
                    "System audit complete. "
                    "No deployment drift detected.",
                    "Audit",
                )

        def _register_page(self, key: str, widget: QWidget) -> None:
            """Register a widget into the nav stack and view_map."""
            idx = self.nav_stack.addWidget(widget)
            self.view_map[key] = idx

        # ── Container export ───────────────────────────────────────────

        def export_stack_spec(
            self, backend: str = "podman"
        ) -> str | None:
            state_path = self._get_active_state_file()
            if not state_path:
                self.log(
                    "No pipeline state found for export.", "Container"
                )
                return None
            with open(state_path, encoding="utf-8") as f:
                state = json.load(f)
            spec = build_stack_spec(state, self.registry_mgr)
            spec["backend"] = backend
            out_file = os.path.join(
                self.exports_root,
                f"stack_export_{backend}.json",
            )
            # H-03: atomic write so an interrupted export never leaves a
            # half-written spec file behind.
            _atomic_write_json(out_file, spec)
            self.log(
                f"Stack exported for {backend}: {out_file}",
                "Container",
            )
            return out_file

        def finalize_stack_export(
            self, backend_type: str = "podman"
        ) -> None:
            spec_file = self.export_stack_spec(backend_type)
            if not spec_file:
                return
            with open(spec_file) as f:
                spec = json.load(f)
            backend = ContainerBackend(self.exports_root)
            out_file = backend.write(spec, backend_type)
            label = {
                "lxc": "LXC configs + launch script",
                "firecracker": "Firecracker microVM configs + launch script",
            }.get(backend_type, f"{backend_type.capitalize()} Compose")
            self.log(
                f"{label} generated: {out_file}",
                "Container",
            )
            self.stacks_tab.refresh()

        # ── Log file watching ──────────────────────────────────────────

        def verify_and_watch(self, log_file: str) -> None:
            # M-35: use Path.touch() instead of `open(log_file, 'a').close()`
            # so the file handle is released deterministically (no GC reliance).
            from pathlib import Path as _Path
            p = _Path(log_file)
            if not p.exists():
                try:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.touch()
                except OSError:
                    return
            if log_file not in self.watcher.files():
                self.watcher.addPath(log_file)
            self.log_offsets[log_file] = p.stat().st_size

        def load_existing_logs(self) -> None:
            if not self.services:
                return
            for s in self.services:
                log_path = os.path.join(
                    self.logs_root, f"{s.tool_id}.log"
                )
                self.verify_and_watch(log_path)
                # M-03: TOCTOU-safe — wrap stat + read in a single
                # try/except so a deleted-just-now log file does not
                # surface as an exception.
                try:
                    size = os.path.getsize(log_path)
                except OSError:
                    continue
                if size <= 0:
                    continue
                try:
                    with open(log_path, encoding="utf-8",
                              errors="ignore") as f:
                        tail = f.readlines()[-15:]
                    for line in tail:
                        if line.strip():
                            # L-02: strip CRLF / CR line endings.
                            self.log(line.rstrip("\r\n").strip(), s.tool_id)
                    self.log_offsets[log_path] = size
                except OSError:
                    pass

        def handle_live_log_update(self, path: str) -> None:
            # M-03: TOCTOU-safe — getsize may raise OSError between the
            # exists() check and the read if the file was rotated.
            try:
                current_size = os.path.getsize(path)
            except OSError:
                return
            offset = self.log_offsets.get(path, 0)
            if current_size < offset:
                offset = 0
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    f.seek(offset)
                    new_chunks = f.read()
                    if new_chunks:
                        svc = next(
                            (s.tool_id for s in self.services
                             if path.endswith(
                                 f"{s.tool_id}.log"
                             )),
                            "System",
                        )
                        for line in new_chunks.splitlines():
                            if line.strip():
                                # L-02: strip CRLF / CR line endings.
                                self.log(line.rstrip("\r\n").strip(), svc)
                        self.log_offsets[path] = f.tell()
            except OSError:
                pass

        # ── Config persistence ─────────────────────────────────────────

        def _load_config(self) -> dict:
            # H-02: resolve config relative to BASE_DIR (not the cwd the
            # app was launched from).
            config_path = os.path.join(self.config_root, CONFIG_FILE)
            if os.path.exists(config_path):
                try:
                    with open(config_path, encoding="utf-8") as f:
                        return json.load(f)
                except (OSError, ValueError, json.JSONDecodeError):
                    pass
            return {}

        def save_config(self) -> None:
            services_data = {
                s.tool_id: {
                    "port": (
                        s.txt_port.text() if s.txt_port else ""
                    ),
                    "model": (
                        s.cbo_model.currentText()
                        if s.cbo_model else ""
                    ),
                }
                for s in self.services
            }
            config = {
                "base_dir": self.base_dir,
                "services": services_data,
            }
            # H-02 + H-03: write under base_dir atomically.
            os.makedirs(self.config_root, exist_ok=True)
            _atomic_write_json(
                os.path.join(self.config_root, CONFIG_FILE), config
            )

        def closeEvent(self, event) -> None:
            self.save_config()
            # H-21: shut down every managed child process so the GUI
            # doesn't orphan tmux windows / desktop launches on exit.
            try:
                self.runtime._process.shutdown()
            except Exception:
                pass
            event.accept()

else:
    AILocalStackControl = None  # type: ignore[assignment, misc]
