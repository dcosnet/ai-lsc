"""ChatbotConsole widget — main chat frame with split view, file attachment,
lattice skills stack, /code command, structured JSON response handling,
QThreadPool dispatch, and SkillRuntimeResolver integration for
auto-injecting system prompts."""

import datetime
import json
import os
import re

try:
    from PySide6.QtCore import Qt, QThreadPool
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QSplitter,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

try:
    from ai_lsc.chat.api import ApiRunnable
except ImportError:
    ApiRunnable = None

from ai_lsc.constants import JCL_FILE_NAME
from ai_lsc.manifest.support import ManifestSupport

if _HAS_QT:

    class ChatbotConsole(QWidget):
        """Main chat frame: split view, file attachment, lattice skills stack,
        /code command, structured JSON response handling, QThreadPool dispatch,
        SkillRuntimeResolver integration for auto-injecting system prompts."""

        def __init__(self, parent):
            super().__init__()
            self.parent = parent
            self.chat_history_data: list[dict] = []
            self.chat_messages: list[dict] = []
            self.is_thinking = False
            self.attached_files: list[str] = []
            self.threadpool = QThreadPool.globalInstance()
            self._build_ui()
            self.reset_chat_history()

        def _build_ui(self):
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(10, 10, 10, 10)

            selectors = QFrame()
            selectors.setStyleSheet(
                "QFrame { background-color: #1e1e1e; border-radius: 6px; }"
            )
            sel_layout = QHBoxLayout(selectors)
            sel_layout.setContentsMargins(10, 8, 10, 8)

            sel_layout.addWidget(QLabel("Model Provider:"))
            self.cbo_provider = QComboBox()
            self.cbo_provider.addItems([
                "Ollama Local Engine", "HuggingFace Local Pipe",
                "External API Gate",
            ])
            self.cbo_provider.setFixedWidth(160)
            sel_layout.addWidget(self.cbo_provider)

            sel_layout.addWidget(QLabel("Active Model:"))
            self.cbo_chat_model = QComboBox()
            self.cbo_chat_model.setFixedWidth(200)
            sel_layout.addWidget(self.cbo_chat_model)

            sel_layout.addWidget(QLabel("Tool Routing:"))
            self.cbo_tool_agent = QComboBox()
            self.cbo_tool_agent.addItems([
                "Direct Prompting", "Aider Agent Framework",
                "Odysseus Matrix Protocol", "Dify Managed Router",
            ])
            self.cbo_tool_agent.setFixedWidth(180)
            sel_layout.addWidget(self.cbo_tool_agent)
            sel_layout.addStretch()

            self.btn_mount = QPushButton("Mount Session")
            self.btn_mount.setStyleSheet(
                "QPushButton { background-color: #27ae60; color: white; "
                "font-weight: bold; border-radius: 4px; padding: 5px 14px; } "
                "QPushButton:hover { background-color: #2ecc71; }"
            )
            self.btn_mount.clicked.connect(self.register_stack_parameters)
            sel_layout.addWidget(self.btn_mount)
            self.btn_load_manifest = QPushButton("Load Project")
            self.btn_load_manifest.setStyleSheet(
                "QPushButton { background-color: #1abc9c; color: white; "
                "font-weight: bold; border-radius: 4px; padding: 5px 14px; } "
                "QPushButton:hover { background-color: #16a085; }"
            )
            self.btn_load_manifest.clicked.connect(self.load_project_manifest)
            sel_layout.addWidget(self.btn_load_manifest)
            main_layout.addWidget(selectors)

            self.splitter = QSplitter(Qt.Horizontal)

            chat_container = QWidget()
            chat_layout = QVBoxLayout(chat_container)
            chat_layout.setContentsMargins(0, 5, 0, 0)

            self.chat_display = QTextEdit()
            self.chat_display.setReadOnly(True)
            self.chat_display.setUndoRedoEnabled(False)
            self.chat_display.setStyleSheet(
                "background-color: #121212; border: 1px solid #222; "
                "border-radius: 6px; padding: 10px; color: #e0e0e0; "
                "line-height: 150%;"
            )
            self.chat_display.setFont(QFont("Segoe UI", 11))
            chat_layout.addWidget(self.chat_display)

            input_controls = QVBoxLayout()
            self.lbl_files = QLabel("")
            self.lbl_files.setStyleSheet(
                "color: #3498db; font-size: 10px; font-weight: bold;"
            )
            self.lbl_files.hide()
            input_controls.addWidget(self.lbl_files)

            input_row = QHBoxLayout()
            self.btn_attach = QPushButton("\U0001f4ce")
            self.btn_attach.setToolTip("Include File(s) as Context (RAG)")
            self.btn_attach.setStyleSheet(
                "background-color: #34495e; color: white; font-size: 14px; "
                "border-radius: 6px; padding: 8px;"
            )
            self.btn_attach.setFixedWidth(40)
            self.btn_attach.clicked.connect(self.attach_files)
            input_row.addWidget(self.btn_attach)

            self.txt_message_input = QLineEdit()
            self.txt_message_input.setPlaceholderText(
                "Message context, prepend /code for agent parsing..."
            )
            self.txt_message_input.setStyleSheet(
                "QLineEdit { background-color: #1e1e1e; border: 1px solid #333; "
                "border-radius: 6px; padding: 10px; color: #ffffff; } "
                "QLineEdit:focus { border: 1px solid #d35400; }"
            )
            self.txt_message_input.setFont(QFont("Segoe UI", 11))
            self.txt_message_input.returnPressed.connect(self.transmit_user_prompt)
            input_row.addWidget(self.txt_message_input)

            self.btn_send = QPushButton("Send")
            self.btn_send.setStyleSheet(
                "QPushButton { background-color: #d35400; color: white; "
                "font-weight: bold; border-radius: 6px; padding: 9px 20px; } "
                "QPushButton:hover { background-color: #e67e22; }"
            )
            self.btn_send.clicked.connect(self.transmit_user_prompt)
            input_row.addWidget(self.btn_send)

            self.btn_clear = QPushButton("Clear")
            self.btn_clear.setToolTip("Clear Context Pipe")
            self.btn_clear.setStyleSheet(
                "QPushButton { background-color: #c0392b; color: white; "
                "font-weight: bold; border-radius: 6px; padding: 9px 15px; } "
                "QPushButton:hover { background-color: #e74c3c; }"
            )
            self.btn_clear.clicked.connect(self.reset_chat_history)
            input_row.addWidget(self.btn_clear)
            input_controls.addLayout(input_row)
            chat_layout.addLayout(input_controls)
            self.splitter.addWidget(chat_container)

            settings_container = QScrollArea()
            settings_container.setWidgetResizable(True)
            settings_container.setFixedWidth(290)
            settings_container.setStyleSheet(
                "QScrollArea { border: none; } "
                "QWidget { background-color: #1a1a1a; }"
            )
            settings_widget = QWidget()
            settings_layout = QVBoxLayout(settings_widget)
            settings_layout.setAlignment(Qt.AlignTop)

            settings_layout.addWidget(QLabel("<b>Model Parameters</b>"))
            settings_layout.addWidget(QLabel("System Instruction:"))
            self.txt_system_prompt = QTextEdit()
            self.txt_system_prompt.setFixedHeight(100)
            self.txt_system_prompt.setPlaceholderText(
                "You are a helpful assistant..."
            )
            self.txt_system_prompt.setStyleSheet(
                "background-color: #262626; border: 1px solid #333; "
                "border-radius: 4px; color: #ccc;"
            )
            settings_layout.addWidget(self.txt_system_prompt)

            settings_layout.addWidget(QLabel("Temperature:"))
            self.spin_temp = QDoubleSpinBox()
            self.spin_temp.setRange(0.0, 2.0)
            self.spin_temp.setSingleStep(0.1)
            self.spin_temp.setValue(0.7)
            self.spin_temp.setStyleSheet("background-color: #262626; color: white;")
            settings_layout.addWidget(self.spin_temp)

            settings_layout.addWidget(QLabel("Max Predict (Tokens):"))
            self.spin_tokens = QSpinBox()
            self.spin_tokens.setRange(128, 32768)
            self.spin_tokens.setSingleStep(256)
            self.spin_tokens.setValue(4096)
            self.spin_tokens.setStyleSheet("background-color: #262626; color: white;")
            settings_layout.addWidget(self.spin_tokens)
            settings_layout.addSpacing(10)

            settings_layout.addWidget(
                QLabel("<b>Lattice Skills Stack</b> (Drag to Reorder)")
            )
            self.skills_list_widget = QListWidget()
            self.skills_list_widget.setSelectionMode(
                QAbstractItemView.SingleSelection
            )
            self.skills_list_widget.setDragDropMode(
                QAbstractItemView.InternalMove
            )
            self.skills_list_widget.setStyleSheet(
                "QListWidget { background-color: #121212; color: #d4d4d4; "
                "border: 1px solid #333; }"
            )
            settings_layout.addWidget(self.skills_list_widget)

            settings_container.setWidget(settings_widget)
            self.splitter.addWidget(settings_container)
            self.splitter.setSizes([700, 290])
            main_layout.addWidget(self.splitter)

        def update_model_dropdown(self, items: list[str]):
            current = self.cbo_chat_model.currentText()
            self.cbo_chat_model.clear()
            self.cbo_chat_model.addItems(items)
            if current in items:
                self.cbo_chat_model.setCurrentText(current)

        def update_dropdown_arrays(self, models: list[str], skills: list[str]):
            self.update_model_dropdown(models)
            existing_checked = {
                self.skills_list_widget.item(i).text()
                for i in range(self.skills_list_widget.count())
                if self.skills_list_widget.item(i).checkState() == Qt.Checked
            }
            self.skills_list_widget.clear()
            for skill in skills:
                item = QListWidgetItem(skill, self.skills_list_widget)
                item.setFlags(
                    item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled
                )
                item.setCheckState(
                    Qt.Checked if skill in existing_checked else Qt.Unchecked
                )

        def attach_files(self):
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select Files to Include", "", "All Files (*)"
            )
            if not files:
                return
            self.attached_files = list(set(self.attached_files + files))
            self.lbl_files.setText(
                f"[ {len(self.attached_files)} files staged for next prompt ]"
            )
            self.lbl_files.show()

        def reset_chat_history(self):
            self.chat_history_data = []
            self.chat_messages = []
            self.attached_files = []
            self.lbl_files.hide()
            self.is_thinking = False
            self.rebuild_chat_view()

        def register_stack_parameters(self):
            """Mount session: sync dropdowns, auto-inject skill system prompt
            via SkillRuntimeResolver, clear history."""
            self.parent.sync_chat_workspace_dropdown()
            self.chat_history_data = []
            self.chat_messages = []
            self.is_thinking = False

            selected = self.cbo_chat_model.currentText() or "[No Target]"

            resolved_prompt = self.parent.skill_resolver.extract_system_prompt(
                selected
            )
            if resolved_prompt:
                self.txt_system_prompt.setPlainText(resolved_prompt)
                self.parent.log(
                    f"SkillRuntime resolved SYSTEM directive for {selected}",
                    "SkillRuntime",
                )

            active_skills = [
                self.skills_list_widget.item(i).text()
                for i in range(self.skills_list_widget.count())
                if self.skills_list_widget.item(i).checkState() == Qt.Checked
            ]
            skills_str = (
                ", ".join(active_skills) if active_skills else "None (Raw Model)"
            )

            self.chat_messages.append({
                "identity": "System Cluster Guard",
                "payload": (
                    f"Session mounted.\nTarget: '{selected}'\n"
                    f"Active Stack Pipeline: [{skills_str}]\n\n"
                    f"Local core engine is online and ready for input."
                ),
                "timestamp": datetime.now().strftime("%H:%M"),
                "is_user": False,
            })
            self.rebuild_chat_view()

        def rebuild_chat_view(self):
            if not self.chat_messages and not self.is_thinking:
                self.chat_display.setHtml("""
                    <div style='color: #666; text-align: center;
                         font-family: sans-serif; margin-top: 40px;'>
                        <h3>Local Engine Thread Instantiated</h3>
                        <p>Configure model parameters, then click
                           <b>Mount Session</b>.</p>
                    </div>
                """)
                return

            bubble_styles = {
                "user": {
                    "align": "right", "bg": "#2d2d2d",
                    "radius": "12px 12px 2px 12px", "max_w": "75%",
                },
                "assistant": {
                    "align": "left", "bg": "#1a1a1a",
                    "border": "1px solid #262626",
                    "radius": "12px 12px 12px 2px", "max_w": "80%",
                },
                "error": {
                    "align": "left", "bg": "#2c1a1a",
                    "border": "1px solid #c0392b",
                    "radius": "12px 12px 12px 2px", "max_w": "80%",
                },
            }

            html = (
                "<body style='background:#121212; color:#e0e0e0;"
                " font-family:sans-serif;'>"
            )
            for msg in self.chat_messages:
                ts = msg["timestamp"]
                payload = (
                    msg["payload"]
                    .replace("<", "&lt;").replace(">", "&gt;")
                    .replace("\n", "<br/>")
                )
                is_error = "?" in msg["identity"]
                style_key = (
                    "user" if msg["is_user"]
                    else ("error" if is_error else "assistant")
                )
                s = bubble_styles[style_key]
                label_color = (
                    "#e0e0e0" if msg["is_user"]
                    else ("#e74c3c" if is_error else "#d35400")
                )
                label = (
                    "<b>You</b>" if msg["is_user"]
                    else f"<b style='color:{label_color}'>{msg['identity']}</b>"
                )
                border_css = (
                    f"border: {s['border']};" if "border" in s else ""
                )
                html += (
                    f"<div style='margin-bottom:15px; text-align:{s['align']}';>"
                    f"<span style='background:{s['bg']}; {border_css} color:#e0e0e0; "
                    f"padding:10px 14px; border-radius:{s['radius']}; "
                    f"display:inline-block; max-width:{s['max_w']};'>"
                    f"{label} <span style='font-size:8pt;color:#777;'>{ts}</span>"
                    f"<br/>"
                    f"<span style='color:#d4d4d4;font-family:monospace;'>"
                    f"{payload}</span>"
                    f"</span></div>"
                )

            if self.is_thinking:
                model = self.cbo_chat_model.currentText() or "Model"
                html += (
                    f"<div style='margin-bottom:15px; text-align:left;'>"
                    f"<span style='background:#1a1a1a; border:1px solid #d35400; "
                    f"color:#888; padding:10px 14px; "
                    f"border-radius:12px 12px 12px 2px; display:inline-block;'>"
                    f"<b style='color:#d35400;'>{model}</b> "
                    f"is calculating a response"
                    f"<span style='color:#d35400;'>...</span>"
                    f"</span></div>"
                )

            html += "</body>"
            self.chat_display.setHtml(html)
            self.chat_display.ensureCursorVisible()


        def load_project_manifest(self):
            path = ManifestSupport.discover_manifest(self.parent.base_dir)
            if not path:
                path, _ = QFileDialog.getOpenFileName(
                    self, "Select Project Manifest", self.parent.base_dir,
                    "Project Files (*.json)",
                )
            if not path:
                return
            manifest = ManifestSupport.load_manifest(path)
            if not manifest:
                self.parent.log("Failed to load manifest.", "Manifest")
                return

            system_text = ManifestSupport.build_system_context(manifest)
            if system_text:
                self.txt_system_prompt.setPlainText(system_text)

            context_files = ManifestSupport.resolve_context_files(
                manifest, os.path.dirname(path)
            )
            if context_files:
                self.attached_files = list(set(
                    self.attached_files + context_files
                ))
                self.lbl_files.setText(
                    f"[ {len(self.attached_files)} files staged: "
                    f"{os.path.basename(path)} loaded ]"
                )
                self.lbl_files.show()

            jcl_path = os.path.join(os.path.dirname(path), JCL_FILE_NAME)
            jobs = ManifestSupport.load_jcl(jcl_path)
            job_summary = (
                ", ".join(j["name"] for j in jobs) if jobs else "None"
            )

            self.parent.log(
                f"Manifest loaded: {os.path.basename(path)} "
                f"({len(context_files)} files, JCL jobs: {job_summary})",
                "Manifest",
            )

        def _extract_skill_prompt(self, skill_name: str) -> str:
            skills_map = self.parent.skills_console_tab.get_all_skills_map()
            path = skills_map.get(skill_name)
            if not path or not os.path.exists(path):
                return ""
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for pattern, flags in [
                    (r'SYSTEM\s+"""(.*?)"""',
                     re.DOTALL | re.IGNORECASE),
                    (r'SYSTEM\s+"(.*?)"', re.IGNORECASE),
                ]:
                    m = re.search(pattern, content, flags)
                    if m:
                        return m.group(1).strip()
            except Exception:
                pass
            return ""

        def handle_api_result(self, sender_id, reply, raw_append=None):
            # UX-06: stop the watchdog timer on any result
            if hasattr(self, '_chat_watchdog'):
                self._chat_watchdog.stop()
            self.is_thinking = False
            if raw_append:
                self.chat_history_data.append(
                    {"role": "assistant", "content": raw_append}
                )
            try:
                if reply.startswith("{") and reply.endswith("}"):
                    data = json.loads(reply)
                    if data.get("ui_action") == "switch_tab":
                        self.parent.nav_stack.setCurrentIndex(
                            data.get("target_index", 0)
                        )
                    if "response_text" in data:
                        reply = data["response_text"]
            except Exception:
                pass
            self.chat_messages.append({
                "identity": sender_id, "payload": reply,
                "timestamp": datetime.now().strftime("%H:%M"),
                "is_user": False,
            })
            self.rebuild_chat_view()
            self.btn_send.setEnabled(True)
            self.txt_message_input.setPlaceholderText(
                "Message context, prepend /code for agent parsing..."
            )

        def transmit_user_prompt(self):
            user_text = self.txt_message_input.text().strip()
            if not user_text and not self.attached_files:
                return

            if user_text.startswith("/code"):
                user_text = user_text.replace("/code", "").strip()
                self.cbo_tool_agent.setCurrentText("Aider Agent Framework")
                coder_idx = next(
                    (i for i in range(self.cbo_chat_model.count())
                     if any(kw in self.cbo_chat_model.itemText(i).lower()
                            for kw in ("coder", "qwen"))),
                    None,
                )
                if coder_idx is not None:
                    self.cbo_chat_model.setCurrentIndex(coder_idx)

            target_model = self.cbo_chat_model.currentText()
            if not target_model:
                self.chat_messages.append({
                    "identity": "? System Guard",
                    "payload": "Aborted: No active target model selected.",
                    "timestamp": datetime.now().strftime("%H:%M"),
                    "is_user": False,
                })
                self.rebuild_chat_view()
                return

            self.txt_message_input.clear()
            file_context, display_text = self._assemble_file_context(user_text)
            full_prompt = (
                (file_context + "\n" + user_text) if file_context else user_text
            )

            self.chat_messages.append({
                "identity": "User", "payload": display_text,
                "timestamp": datetime.now().strftime("%H:%M"),
                "is_user": True,
            })
            payload_history = self._build_payload_history(full_prompt)

            self.is_thinking = True
            self.rebuild_chat_view()
            self.btn_send.setEnabled(False)
            self.txt_message_input.setPlaceholderText("Awaiting response...")

            # UX-06: 180-second watchdog timer for stuck "thinking" state
            self._chat_watchdog = QTimer(self)
            self._chat_watchdog.setSingleShot(True)
            self._chat_watchdog.setInterval(180_000)
            self._chat_watchdog.timeout.connect(self._on_chat_timeout)

            ollama_port = self.parent.resolve_ollama_port()
            worker = ApiRunnable(
                model_id=target_model, port_id=ollama_port,
                history_snapshot=payload_history,
                temperature=self.spin_temp.value(),
                max_tokens=self.spin_tokens.value(),
            )
            worker.signals.result.connect(self.handle_api_result)
            self._chat_watchdog.start()
            self.threadpool.start(worker)

        def _on_chat_timeout(self) -> None:
            """UX-06: handle 180s chat timeout."""
            if self.is_thinking:
                self.is_thinking = False
                self.btn_send.setEnabled(True)
                self.txt_message_input.setPlaceholderText("Type a message...")
                self.chat_messages.append({
                    "identity": "? Timeout Watchdog",
                    "payload": (
                        "Response timed out after 180 seconds. "
                        "The model may be overloaded or the request too large. "
                        "Please try again or use a smaller model."
                    ),
                    "timestamp": datetime.now().strftime("%H:%M"),
                    "is_user": False,
                })
                self.rebuild_chat_view()

        def _assemble_file_context(self, user_text: str) -> tuple[str, str]:
            if not self.attached_files:
                return "", user_text
            parts = ["Use the following files as context for my request:\n"]
            for fpath in self.attached_files:
                try:
                    with open(fpath, encoding="utf-8") as f:
                        parts.append(
                            f"\n--- FILE: {os.path.basename(fpath)} ---\n"
                            f"{f.read()}\n"
                        )
                except Exception as e:
                    parts.append(
                        f"\n--- FILE: {os.path.basename(fpath)} "
                        f"[ERROR: {e}] ---\n"
                    )
            self.attached_files = []
            self.lbl_files.hide()
            return "".join(parts), f"[Attached {len(parts) - 1} files]\n" + user_text

        def _build_payload_history(self, full_prompt: str) -> list[dict]:
            sys_prompt = self.txt_system_prompt.toPlainText().strip()

            def _get_skill_directives():
                for i in range(self.skills_list_widget.count()):
                    item = self.skills_list_widget.item(i)
                    if item.checkState() != Qt.Checked:
                        continue
                    name = item.text()
                    prompt = self._extract_skill_prompt(name)
                    if not prompt:
                        continue
                    yield f"--- [Active Sub-Skill: {name}] ---\n{prompt}"

            skill_directives = list(_get_skill_directives())

            parts = []
            if sys_prompt:
                parts.append(sys_prompt)
            if skill_directives:
                parts.append(
                    "You are a multi-agent orchestrated lattice execution cluster. "
                    "Absorb and layer the following skill instructions:\n\n"
                    + "\n\n".join(skill_directives)
                )
            system_content = (
                parts[0] + "\n\n" + parts[1]
                if len(parts) == 2
                else (parts[0] if parts else "")
            )

            self.chat_history_data.append(
                {"role": "user", "content": full_prompt}
            )
            filtered = [
                m for m in self.chat_history_data if m.get("role") != "system"
            ]
            result = []
            if system_content:
                result.append({"role": "system", "content": system_content})
            result.extend(filtered)
            return result

else:
    ChatbotConsole = None
