"""ServiceRow widget -- a single service row driven by registry metadata + flags.

Renders one tool (or skill:-prefixed behavior binding) inside the
Tools/Services page.  Each row shows the service name, live status,
CPU load, port input, model selector (for engine/LLM-runtime services),
Ollama pull controls, launcher buttons (CLI/GUI/Web), and
Install/Sync + Start/Stop action buttons.

All process management is delegated to
:class:`~ai_lsc.runtime.executor.RuntimeExecutor` -- this widget
contains **zero** ``subprocess`` / ``psutil`` calls.
"""

import os
import threading

from ai_lsc.constants import SERVICE_LICENSES, STATUS_STYLES
from ai_lsc.utils.process import cpu_load_for_processes

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QFrame,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

if _HAS_QT:

    class ServiceRow(QWidget):
        """A single service row, fully driven by registry metadata + flags.
        Supports both regular tools and skill:-prefixed behavior bindings."""

        def __init__(self, parent, tool_id: str, port, meta: dict):
            super().__init__(parent)
            self.parent = parent
            self.tool_id = tool_id
            self.port = port
            self.meta = meta
            self.is_skill = tool_id.startswith("skill:")

            if self.is_skill:
                self._build_skill_row()
                return

            self.installer = meta.get("installer", {})
            self.launcher = meta.get("launcher", {})
            self.flags = meta.get("flags", {})
            self.is_ollama = self.flags.get("is_ollama", False)
            self.has_models = meta.get("category") in (
                "Engine", "LLM Runtime", "Development",
            )
            self.has_api = self.flags.get("has_web", False) or meta.get(
                "category"
            ) in (
                "Engine", "LLM Runtime", "Pipeline",
                "Agent Framework", "Embedding",
            )
            self.search_term = self.installer.get("pkg", tool_id)
            self._build_ui()

        # -- property shortcuts to parent attributes -----------------------

        @property
        def _runtime(self):
            """Lazy accessor for the RuntimeExecutor on the main window."""
            return self.parent.runtime

        def _log(self, text: str, source: str = "System"):
            self.parent.log(text, source)

        # -- row builders --------------------------------------------------

        def _build_skill_row(self):
            layout = QHBoxLayout(self)
            layout.setContentsMargins(10, 5, 10, 5)
            skill_name = self.tool_id.split(":", 1)[1]

            self.lbl_name = QLabel(f"[Skill] {skill_name}")
            self.lbl_name.setFixedWidth(160)
            self.lbl_name.setFont(QFont("Consolas", 11, QFont.Bold))
            layout.addWidget(self.lbl_name)

            self.lbl_status = QLabel("[ READY ]")
            self.lbl_status.setFixedWidth(90)
            self.lbl_status.setAlignment(Qt.AlignCenter)
            self.lbl_status.setStyleSheet(
                "color: #3498db; font-weight: bold;"
            )
            layout.addWidget(self.lbl_status)

            desc = QLabel("Skill Behavior Binding (Active in Pipeline)")
            desc.setStyleSheet("color: #7f8c8d; font-style: italic;")
            layout.addWidget(desc)
            layout.addStretch()

            self.txt_port = None
            self.cbo_model = None

        def _build_ui(self):
            layout = QHBoxLayout(self)
            layout.setContentsMargins(10, 5, 10, 5)

            level_tag = f"L{self.meta.get('level', 0)}"
            self.lbl_name = QLabel(
                f"[{level_tag}] {self.meta.get('name', self.tool_id)}"
            )
            self.lbl_name.setFixedWidth(160)
            self.lbl_name.setFont(QFont("Consolas", 11, QFont.Bold))
            layout.addWidget(self.lbl_name)

            self.lbl_status = QLabel("[ CHECKING ]")
            self.lbl_status.setFixedWidth(90)
            self.lbl_status.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.lbl_status)

            self.lbl_load = QLabel("---")
            self.lbl_load.setFixedWidth(50)
            self.lbl_load.setStyleSheet(
                "color: #FFB000; font-family: 'Consolas'; font-weight: bold;"
            )
            layout.addWidget(self.lbl_load)

            if self.port is not None:
                layout.addWidget(QLabel("Port:"))
                self.txt_port = QLineEdit(str(self.port))
                self.txt_port.setFixedWidth(60)
                self.txt_port.setAlignment(Qt.AlignCenter)
                layout.addWidget(self.txt_port)
            else:
                self.txt_port = None
                spacer = QFrame()
                spacer.setFixedWidth(95)
                layout.addWidget(spacer)

            if self.has_models:
                self.cbo_model = QComboBox()
                self.cbo_model.setFixedWidth(180)
                layout.addWidget(self.cbo_model)
            else:
                self.cbo_model = None
                spacer = QFrame()
                spacer.setFixedWidth(180)
                layout.addWidget(spacer)

            if self.is_ollama:
                self.txt_pull = QLineEdit()
                self.txt_pull.setPlaceholderText("model tag")
                self.txt_pull.setFixedWidth(100)
                layout.addWidget(self.txt_pull)
                btn_pull = QPushButton("Pull")
                btn_pull.setFixedWidth(50)
                btn_pull.setStyleSheet(
                    "background-color: #d35400; color: white; font-weight: bold;"
                )
                btn_pull.clicked.connect(self.pull_model)
                layout.addWidget(btn_pull)

            layout.addStretch()

            # -- Infer C/W/G interface buttons from flags + launcher type --
            # Tools with explicit flags keep them; others are inferred so
            # every service row gets the correct launcher buttons.
            launcher_type = self.launcher.get("type", "")
            has_port = self.port is not None
            show_web = self.flags.get("has_web", False) or (
                has_port and launcher_type in ("tmux", "systemd")
            )
            show_gui = self.flags.get("has_gui", False) or (
                launcher_type == "desktop"
            )
            show_cli = self.flags.get("has_cli", False) or (
                launcher_type in ("cli", "tmux")
            )

            launcher_style = (
                "QPushButton { background-color: #34495e; color: white; "
                "font-weight: bold; border-radius: 3px; } "
                "QPushButton:hover { background-color: #415b76; }"
            )
            for visible, label, tip, handler in [
                (show_cli, "C", "Launch CLI in terminal", self.launch_cli),
                (show_gui, "G", "Launch Desktop/GUI app", self.launch_gui),
                (show_web, "W", "Open Web UI in browser", self.launch_web),
            ]:
                if visible:
                    btn = QPushButton(label)
                    btn.setFixedWidth(28)
                    btn.setToolTip(tip)
                    btn.setStyleSheet(launcher_style)
                    btn.clicked.connect(handler)
                    layout.addWidget(btn)

            spacer = QFrame()
            spacer.setFixedWidth(10)
            layout.addWidget(spacer)

            # API endpoint / key button for tools with external API support
            if self.has_api:
                btn_api = QPushButton(":set api")
                btn_api.setToolTip(
                    "Set external API endpoint and key"
                )
                btn_api.setStyleSheet(
                    "QPushButton { background-color: #e67e22; color: white; "
                    "font-weight: bold; font-size: 11px; border-radius: 3px; }"
                    "QPushButton:hover { background-color: #f39c12; }"
                )
                btn_api.setFixedWidth(60)
                btn_api.clicked.connect(self._open_api_dialog)
                layout.addWidget(btn_api)

            self.btn_update = QPushButton("Install / Sync")
            self.btn_update.setStyleSheet("background-color: #8e44ad;")
            self.btn_update.clicked.connect(self.smart_install)
            self._install_btn_original_text = self.btn_update.text()
            layout.addWidget(self.btn_update)

            start_labels = {
                "systemd": "Enable (systemd)",
                "desktop": "Launch App",
            }
            self.btn_start = QPushButton(
                start_labels.get(self.launcher.get("type"), "Start Engine")
            )
            self.btn_start.setStyleSheet("background-color: #27ae60;")
            self.btn_start.clicked.connect(self.start_service)
            layout.addWidget(self.btn_start)

            stop_labels = {"systemd": "Disable"}
            self.btn_stop = QPushButton(
                stop_labels.get(self.launcher.get("type"), "Kill Process")
            )
            self.btn_stop.setStyleSheet("background-color: #c0392b;")
            self.btn_stop.clicked.connect(self.stop_service)
            layout.addWidget(self.btn_stop)

        # -- model hydration -----------------------------------------------

        def hydrate_models(self, ollama_models: list, aider_models: list):
            if not self.has_models or self.cbo_model is None:
                return
            self.cbo_model.clear()
            pool = (
                aider_models
                if any(k in self.tool_id.lower()
                       for k in ("aider", "claude"))
                else ollama_models
            )
            self.cbo_model.addItems(pool)

        # -- launcher actions (delegate to runtime) ----------------------

        def launch_cli(self):
            desc = self._runtime.launch_cli(
                tool_id=self.tool_id,
                launcher_type=self.launcher.get("type", ""),
            )
            self._log(desc)

        def launch_gui(self):
            self._log(
                f"GUI payload triggered for: {self.meta.get('name')}", "System"
            )

        def launch_web(self):
            if self.txt_port is None:
                return
            url = self._runtime.open_web_url(self.txt_port.text().strip())
            self._log(f"Browser navigated to {url}", "System")

        # -- install (dispatched via runtime) -----------------------------

        def smart_install(self):
            inst_type = self.installer.get("type")
            pkg = self.installer.get("pkg", self.tool_id)
            cmd = self.installer.get("cmd", "")

            # UX-03: disable button and show progress during install
            self.btn_update.setEnabled(False)
            self.btn_update.setText("Installing...")
            self.btn_update.setStyleSheet("background-color: #555; color: #aaa;")

            self._log(
                f"Deploying {self.meta.get('name')} via {inst_type}...",
                "Installer",
            )

            license_text = SERVICE_LICENSES.get(self.meta.get("name"))
            if license_text:
                msg = QMessageBox(self)
                msg.setWindowTitle(f"Legal Notice: {self.meta.get('name')}")
                msg.setText(
                    f"To install <b>{self.meta.get('name')}</b>, "
                    f"you must accept the license."
                )
                msg.setInformativeText(license_text)
                msg.setTextInteractionFlags(Qt.TextBrowserInteraction)
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                if msg.exec() != QMessageBox.Ok:
                    return

            threading.Thread(
                target=self._run_install,
                args=(inst_type, pkg, cmd),
                daemon=True,
            ).start()

        def _run_install(self, inst_type: str, pkg: str, cmd: str):
            ctx = self._runtime.format_context()
            # Pull the tool's license SPDX from the registry metadata
            # so the installer's license gate can check it.
            license_spdx = self.meta.get("license")
            try:
                desc = self._runtime.install_tool(
                    inst_type=inst_type,
                    pkg=pkg,
                    cmd=cmd,
                    tool_id=self.tool_id,
                    ctx=ctx,
                    license_spdx=license_spdx,
                )
                QTimer.singleShot(
                    0, lambda d=desc, t=self.tool_id: self._on_install_done(d, t)
                )
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                QTimer.singleShot(
                    0, lambda e=exc: self._on_install_error(
                        f"Deployment failed: {e}", "Installer Error"
                    )
                )
            except Exception as exc:
                # Catch license-gate exceptions (LicenseBlocked /
                # LicenseAcceptanceRequired) which are raised before
                # any subprocess call.  These need to be handled on the
                # main thread (Qt dialogs must run on the main thread).
                QTimer.singleShot(
                    0, lambda e=exc: self._handle_license_exception(e)
                )

        def _restore_install_btn(self) -> None:
            """UX-03: re-enable install button after install completes/fails."""
            self.btn_update.setEnabled(True)
            self.btn_update.setText(self._install_btn_original_text)
            self.btn_update.setStyleSheet("background-color: #8e44ad;")

        def _on_install_done(self, desc: str, tool_id: str) -> None:
            self._log(desc, tool_id)
            self._restore_install_btn()

        def _on_install_error(self, msg: str, source: str) -> None:
            self._log(msg, source)
            self._restore_install_btn()

        def _handle_license_exception(self, exc: Exception) -> None:
            """Handle LicenseBlocked / LicenseAcceptanceRequired on the
            main thread (Qt dialogs must run there)."""
            try:
                from ai_lsc.registry.license_gate import (
                    LicenseAcceptanceRequired,
                    LicenseBlocked,
                )
                from ai_lsc.ui.dialogs.license_dialog import (
                    LicenseAcceptanceDialog,
                    LicenseBlockedDialog,
                )
            except ImportError:
                # If the license modules aren't available (shouldn't
                # happen in normal operation), fall back to logging.
                self._log(f"License check failed: {exc}", "License")
                return

            if isinstance(exc, LicenseBlocked):
                dlg = LicenseBlockedDialog(
                    tool_id=exc.tool_id,
                    tool_name=self.meta.get("name", exc.tool_id),
                    reason=exc.reason,
                    parent=self,
                )
                dlg.exec()
                return

            if isinstance(exc, LicenseAcceptanceRequired):
                dlg = LicenseAcceptanceDialog(
                    tool_id=exc.tool_id,
                    tool_name=self.meta.get("name", exc.tool_id),
                    license_info=exc.license_info,
                    parent=self,
                )
                # Connect the dialog's signals to handlers that record
                # the acceptance + retry the install.
                dlg.accepted_individual.connect(
                    self._on_license_accepted_individual
                )
                dlg.accepted_all_of_type.connect(
                    self._on_license_accepted_all
                )
                dlg.exec()
                return

            # Unknown exception type — just log it.
            self._log(f"Unexpected license error: {exc}", "License")

        def _on_license_accepted_individual(self, tool_id: str, spdx: str) -> None:
            """Called when the user clicks 'Accept & Install' in the
            license dialog.  Records the acceptance and retries the
            install on a background thread."""
            try:
                self.parent.license_gate.accept(tool_id, spdx, via="individual")
            except Exception as exc:
                self._log(f"Failed to record license acceptance: {exc}", "License")
                return
            self._log(
                f"License {spdx} accepted for {tool_id}. Retrying install...",
                "License",
            )
            # Retry the install
            inst = self.meta.get("installer", {})
            self._run_install(
                inst.get("type", "pacman"),
                inst.get("pkg", ""),
                inst.get("cmd", ""),
            )

        def _on_license_accepted_all(self, tool_id: str, spdx: str) -> None:
            """Called when the user clicks 'Accept all <license>' in
            the license dialog.  Adds the SPDX to the auto-approval
            registry, records the per-tool acceptance, and retries."""
            try:
                self.parent.license_gate.add_auto_approval(spdx)
                self.parent.license_gate.accept(tool_id, spdx, via="auto-approved")
            except ValueError as exc:
                self._log(f"Cannot auto-approve {spdx}: {exc}", "License")
                return
            except Exception as exc:
                self._log(f"Failed to record license acceptance: {exc}", "License")
                return
            self._log(
                f"License {spdx} added to auto-approvals + accepted for {tool_id}. "
                f"Retrying install...",
                "License",
            )
            inst = self.meta.get("installer", {})
            self._run_install(
                inst.get("type", "pacman"),
                inst.get("pkg", ""),
                inst.get("cmd", ""),
            )

        # -- ollama model pull --------------------------------------------

        def pull_model(self):
            model_name = self.txt_pull.text().strip()
            if not model_name:
                self._log(
                    "Error: Specify a valid model target descriptor.", "Ollama"
                )
                return
            self._log(f"Spawning pull for: {model_name}", "Ollama")

            def _run():
                try:
                    proc = self._runtime.pull_model(model_name)
                    # UX-10: Since pull_model now redirects to a log file,
                    # poll for completion and surface errors.
                    proc.wait(timeout=1800)
                    if proc.returncode == 0:
                        QTimer.singleShot(
                            0, lambda: self._log(
                                f"Model {model_name} pulled successfully.",
                                "Ollama",
                            )
                        )
                        QTimer.singleShot(
                            0, self.parent.refresh_all_models
                        )
                    else:
                        QTimer.singleShot(
                            0, lambda: self._log(
                                f"PULL FAILED for {model_name} "
                                f"(exit code {proc.returncode}). "
                                f"Check the pull log in logs/ for details.",
                                "Ollama Error",
                            )
                        )
                except Exception as exc:
                    QTimer.singleShot(
                        0, lambda: self._log(f"PULL FAILED: {exc}", "Ollama Error")
                    )

            threading.Thread(target=_run, daemon=True).start()

        # -- start / stop / status (delegated to runtime) ---------------

        def start_service(self):
            port = self.txt_port.text() if self.txt_port else ""
            model_arg = ""
            if (self.has_models and self.cbo_model
                    and self.cbo_model.currentText()):
                model_arg = self.cbo_model.currentText()

            log_file = os.path.join(self.parent.logs_root, f"{self.tool_id}.log")
            try:
                desc = self._runtime.start_service(
                    tool_id=self.tool_id,
                    launcher_cmd=self.launcher.get("cmd", ""),
                    launcher_type=self.launcher.get("type", ""),
                    port=port,
                    model_arg=model_arg,
                )
            except ValueError as exc:
                # H-19: port / tool_id validation surfaced from the runtime.
                self._log(f"Cannot start: {exc}", "Validation")
                return
            self._log(desc, self.launcher.get("type", "Tmux").capitalize())
            self.parent.verify_and_watch(log_file)
            QTimer.singleShot(2000, self.update_status)

        def stop_service(self):
            desc = self._runtime.stop_service(
                tool_id=self.tool_id,
                launcher_type=self.launcher.get("type", ""),
                launcher_cmd=self.launcher.get("cmd", ""),
                search_term=self.search_term,
            )
            self._log(desc, "System")
            QTimer.singleShot(1500, self.update_status)

        def update_status(self):
            if self.is_skill:
                return
            running = self._runtime.is_service_running(
                launcher_type=self.launcher.get("type", ""),
                tool_id=self.tool_id,
                service_cmd=self.launcher.get("cmd", ""),
                search_term=self.search_term,
            )
            self._last_running_state = running
            cpu = (
                cpu_load_for_processes(self.search_term)
                if running
                else 0.0
            )
            text, color = STATUS_STYLES[running]
            self.lbl_status.setText(text)
            self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold;")
            self.lbl_load.setText(f"{int(cpu)}%" if running else "---")

        def is_running_now(self) -> bool:
            """Return the most recent cached running state.

            Returns False if update_status() has never been called.
            Used by the PipelineTicker + WorkspaceTab to color/skip
            tool pills without re-querying the runtime.
            """
            return getattr(self, "_last_running_state", False)

        # -- API configuration dialog ------------------------------------

        def _open_api_dialog(self):
            dlg = QDialog(self)
            dlg.setWindowTitle(
                f"API Configuration — {self.meta.get('name', self.tool_id)}"
            )
            dlg.setMinimumWidth(450)
            dlg_layout = QVBoxLayout(dlg)

            form = QFormLayout()
            txt_endpoint = QLineEdit()
            txt_endpoint.setPlaceholderText(
                "e.g. https://api.openai.com/v1"
            )
            txt_key = QLineEdit()
            txt_key.setPlaceholderText(
                "e.g. sk-...  (stored locally only)"
            )
            txt_key.setEchoMode(QLineEdit.Password)
            txt_model_override = QLineEdit()
            txt_model_override.setPlaceholderText(
                "e.g. gpt-4o  (optional model override)"
            )
            form.addRow("API Endpoint:", txt_endpoint)
            form.addRow("API Key:", txt_key)
            form.addRow("Model Override:", txt_model_override)
            dlg_layout.addLayout(form)

            # Restore saved values
            cfg = self.parent.config_data.get("api_overrides", {})
            tool_cfg = cfg.get(self.tool_id, {})
            txt_endpoint.setText(tool_cfg.get("endpoint", ""))
            txt_key.setText(tool_cfg.get("api_key", ""))
            txt_model_override.setText(tool_cfg.get("model_override", ""))

            btn_box = QHBoxLayout()
            btn_save = QPushButton("Save")
            btn_save.setStyleSheet(
                "background-color: #27ae60; color: white; font-weight: bold;"
            )
            btn_clear = QPushButton("Clear")
            btn_clear.setStyleSheet(
                "background-color: #c0392b; color: white;"
            )
            btn_cancel = QPushButton("Cancel")
            btn_box.addStretch()
            btn_box.addWidget(btn_save)
            btn_box.addWidget(btn_clear)
            btn_box.addWidget(btn_cancel)
            dlg_layout.addLayout(btn_box)

            def _save():
                api_overrides = self.parent.config_data.setdefault(
                    "api_overrides", {}
                )
                api_overrides[self.tool_id] = {
                    "endpoint": txt_endpoint.text().strip(),
                    "api_key": txt_key.text().strip(),
                    "model_override": txt_model_override.text().strip(),
                }
                self.parent.save_config()
                self._log(
                    f"API configuration saved for {self.meta.get('name')}",
                    "API Config",
                )
                dlg.accept()

            def _clear():
                api_overrides = self.parent.config_data.get(
                    "api_overrides", {}
                )
                api_overrides.pop(self.tool_id, None)
                self.parent.save_config()
                txt_endpoint.clear()
                txt_key.clear()
                txt_model_override.clear()
                self._log(
                    f"API configuration cleared for {self.meta.get('name')}",
                    "API Config",
                )

            btn_save.clicked.connect(_save)
            btn_clear.clicked.connect(_clear)
            btn_cancel.clicked.connect(dlg.reject)

            dlg.exec()

else:
    ServiceRow = None
