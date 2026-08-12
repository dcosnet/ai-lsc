"""IpcStackTab widget -- Enhanced Stack Editor (replaces old wizard popup).

This is the central stack composition surface.  It combines:
  - Template selector (from the old StackWizard dialog)
  - Execution flow builder (left/right panel with >>/<< buttons)
  - Dependency validation + auto-include
  - Lifecycle engine controls (Prepare / Activate / Validate)
  - Create-template-from-selection
  - Compile button that writes pipeline.json
"""

import json
import os
from datetime import datetime

from ai_lsc.constants import BASE_DIR, PIPELINE_FILE_NAME, STATE_FILE_NAME
from ai_lsc.ui.main_window import _atomic_write_json
from ai_lsc.registry.stack_templates.manager import StackTemplateManager

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QComboBox,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

if _HAS_QT:

    class IpcStackTab(QWidget):
        """Enhanced stack editor: templates, flow builder, lifecycle, compile."""

        def __init__(self, main_window):
            super().__init__()
            self.main = main_window
            self._template_mgr = StackTemplateManager()
            self._build_ui()

        # ── UI construction ──────────────────────────────────────────

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(10, 8, 10, 8)

            # ── Title row ───────────────────────────────────────────
            title_row = QHBoxLayout()
            lbl = QLabel("<b>Stack Editor</b>")
            lbl.setFont(QFont("Segoe UI", 14))
            title_row.addWidget(lbl)
            title_row.addStretch()

            # Template controls on the right
            title_row.addWidget(QLabel("Template:"))
            self._template_combo = QComboBox()
            self._template_combo.setMinimumWidth(280)
            self._populate_template_combo()
            self._template_combo.currentIndexChanged.connect(
                self._on_template_selected
            )
            title_row.addWidget(self._template_combo)

            self._apply_tpl_btn = QPushButton("Apply Template")
            self._apply_tpl_btn.setStyleSheet(
                "background-color: #2980b9; color: white; "
                "font-weight: bold; padding: 6px 12px; border-radius: 4px;"
            )
            self._apply_tpl_btn.clicked.connect(self._apply_template)
            title_row.addWidget(self._apply_tpl_btn)
            root.addLayout(title_row)

            # Template description
            self._template_desc = QLabel("")
            self._template_desc.setWordWrap(True)
            self._template_desc.setStyleSheet(
                "color: #bdc3c7; padding: 6px 8px; "
                "background-color: #1a1a1a; border-radius: 4px; "
                "font-size: 11px; min-height: 36px;"
            )
            root.addWidget(self._template_desc)
            if self._template_combo.count() > 0:
                self._on_template_selected(0)

            # ── Two-panel flow builder ─────────────────────────────
            flow_frame = QFrame()
            flow_frame.setStyleSheet(
                "QFrame { border: 1px solid #333; border-radius: 6px; }"
            )
            flow_layout = QHBoxLayout(flow_frame)
            flow_layout.setContentsMargins(6, 6, 6, 6)

            # Left: available components tree
            left = QVBoxLayout()
            left.addWidget(
                QLabel(
                    "<span style='color:#a5d6a7;font-weight:bold;font-size:11px;'>"
                    "AVAILABLE COMPONENTS</span>"
                )
            )
            self.avail_tree = QTreeWidget()
            self.avail_tree.setColumnCount(1)
            self.avail_tree.setHeaderLabels(["Component"])
            left.addWidget(self.avail_tree)
            flow_layout.addLayout(left, 2)

            # Center: arrow buttons
            center = QVBoxLayout()
            center.addStretch()
            btn_add = QPushButton(" >> ")
            btn_add.setFixedWidth(50)
            btn_add.clicked.connect(self.add_node)
            center.addWidget(btn_add)
            btn_rem = QPushButton(" << ")
            btn_rem.setFixedWidth(50)
            btn_rem.clicked.connect(self.remove_node)
            center.addWidget(btn_rem)
            center.addStretch()
            flow_layout.addLayout(center, 0)

            # Right: execution flow
            right = QVBoxLayout()
            right.addWidget(
                QLabel(
                    "<span style='color:#a5d6a7;font-weight:bold;font-size:11px;'>"
                    "EXECUTION FLOW</span>"
                )
            )
            self.flow_list = QListWidget()
            right.addWidget(self.flow_list)

            self.lbl_validation = QLabel("Health: Awaiting Compilation...")
            self.lbl_validation.setStyleSheet(
                "color: #7f8c8d; font-weight: bold; font-size: 11px;"
            )
            right.addWidget(self.lbl_validation)
            flow_layout.addLayout(right, 2)

            root.addWidget(flow_frame, stretch=2)

            # ── Two-Stage Stack Lifecycle Engine ────────────────────
            lifecycle_group = QGroupBox("Stack Lifecycle Engine")
            lifecycle_layout = QHBoxLayout(lifecycle_group)

            self.btn_prepare = QPushButton("Prepare Stack Structure")
            self.btn_prepare.setStyleSheet(
                "background-color: #2980b9; color: white; "
                "font-weight: bold; padding: 8px; border-radius: 4px;"
            )
            self.btn_prepare.clicked.connect(
                self.main.execute_stack_preparation
            )
            lifecycle_layout.addWidget(self.btn_prepare)

            self.btn_activate = QPushButton("Activate Stack Matrix")
            self.btn_activate.setEnabled(False)
            self.btn_activate.setStyleSheet(
                "background-color: #27ae60; color: white; "
                "font-weight: bold; padding: 8px; border-radius: 4px;"
            )
            self.btn_activate.clicked.connect(
                self.main.execute_stack_activation
            )
            lifecycle_layout.addWidget(self.btn_activate)

            self.btn_validate = QPushButton("Validate Stack Integrity")
            self.btn_validate.setStyleSheet(
                "background-color: #8e44ad; color: white; "
                "font-weight: bold; padding: 8px; border-radius: 4px;"
            )
            self.btn_validate.clicked.connect(
                self.main.execute_stack_validation
            )
            lifecycle_layout.addWidget(self.btn_validate)

            lifecycle_layout.addStretch()
            root.addWidget(lifecycle_group)

            # ── Action buttons row ──────────────────────────────────
            action_row = QHBoxLayout()

            btn_create_tpl = QPushButton("Save as Template")
            btn_create_tpl.setStyleSheet(
                "background-color: #e67e22; color: white; "
                "font-weight: bold; padding: 8px 14px; border-radius: 4px;"
            )
            btn_create_tpl.setToolTip(
                "Save the current flow selection as a reusable stack template"
            )
            btn_create_tpl.clicked.connect(self._create_template_from_flow)
            action_row.addWidget(btn_create_tpl)

            btn_clear = QPushButton("Clear Flow")
            btn_clear.setStyleSheet(
                "background-color: #7f8c8d; color: white; "
                "padding: 8px 14px; border-radius: 4px;"
            )
            btn_clear.clicked.connect(self._clear_flow)
            action_row.addWidget(btn_clear)

            action_row.addStretch()

            btn_audit = QPushButton("Run System Audit")
            btn_audit.clicked.connect(self.main.run_system_audit)
            action_row.addWidget(btn_audit)

            self.btn_compile = QPushButton("Compile Stack")
            self.btn_compile.setStyleSheet(
                "background-color: #27ae60; color: white; font-size: 13px; "
                "font-weight: bold; padding: 10px 24px; border-radius: 4px;"
            )
            self.btn_compile.clicked.connect(self.compile_stack)
            action_row.addWidget(self.btn_compile)

            root.addLayout(action_row)

            # Wire lifecycle enable from main window
            self._sync_lifecycle_state()

        # ── Template helpers ────────────────────────────────────────

        def _populate_template_combo(self) -> None:
            self._template_combo.blockSignals(True)
            self._template_combo.clear()
            for tpl in self._template_mgr.list_templates():
                source_tag = (
                    " [custom]" if tpl["source"] == "custom" else ""
                )
                label = (
                    f"{tpl['name']} "
                    f"({tpl['tool_count']} tools{source_tag})"
                )
                self._template_combo.addItem(label, tpl["id"])
            self._template_combo.blockSignals(False)

        def _on_template_selected(self, index: int) -> None:
            tpl_id = self._template_combo.currentData()
            if not tpl_id:
                self._template_desc.setText("")
                return
            tpl = self._template_mgr.get_template(tpl_id)
            if not tpl:
                return
            desc = tpl.get("description", "No description")
            tags = ", ".join(tpl.get("tags", []))
            ver = tpl.get("version", "1.0")
            count = len(tpl.get("tools", []))
            self._template_desc.setText(
                f"[v{ver}] {desc}  |  Tags: {tags}  |  Tools: {count}"
            )

        def _apply_template(self) -> None:
            """Apply a template: populate the flow list and update infra
            layer checkboxes."""
            tpl_id = self._template_combo.currentData()
            if not tpl_id:
                QMessageBox.warning(
                    self, "No Template",
                    "Please select a stack template first."
                )
                return

            tool_ids, new_entries = self._template_mgr.resolve_tool_ids(
                tpl_id, self.main.registry_mgr
            )

            # Register any new tools from git-source entries
            if new_entries:
                for entry in new_entries:
                    tid = entry.get("id", "")
                    if tid and tid not in self.main.registry_mgr.data:
                        self.main.registry_mgr.data[tid] = entry
                        self.main.registry_mgr.registry_file.write_text(
                            json.dumps(
                                self.main.registry_mgr.data, indent=4
                            ),
                            encoding="utf-8",
                        )

            # Update the flow list
            self.flow_list.clear()
            for tid in tool_ids:
                meta = self.main.registry_mgr.get_tool(tid)
                display = meta.get("name", tid) if meta else tid
                if tid.startswith("skill:"):
                    display = f"[Skill] {display}"
                item = QListWidgetItem(display)
                item.setData(Qt.UserRole, tid)
                self.flow_list.addItem(item)

            # Update infrastructure layer checkboxes to match template
            self._sync_layer_checkboxes(tool_ids)

            self.validate_flow()

            tpl = self._template_mgr.get_template(tpl_id)
            tpl_name = tpl.get("name", tpl_id) if tpl else tpl_id

            # Also compile state directly (like the old wizard)
            self._compile_state_from_ids(tool_ids)

            self.main.log(
                f"Template '{tpl_name}' applied: "
                f"{len(tool_ids)} tools staged.",
                "StackCompiler",
            )

        def _sync_layer_checkboxes(self, tool_ids: list[str]) -> None:
            """Update all InfrastructureLayerPage checkboxes to match
            the given tool_ids set."""
            id_set = set(tool_ids)
            nav = self.main.nav_stack
            for i in range(nav.count()):
                page = nav.widget(i)
                page_cls = type(page).__name__
                if page_cls == "InfrastructureLayerPage":
                    for tid, chk in page.checkboxes.items():
                        chk.blockSignals(True)
                        chk.setChecked(tid in id_set)
                        chk.blockSignals(False)
                    page._update_count_label()
                    page.refresh_active_services()

        def _compile_state_from_ids(self, tool_ids: list[str]) -> None:
            """Write pipeline_state.json from a flat list of tool IDs,
            with dependency resolution."""
            missing = self.main.registry_mgr.check_dependencies(tool_ids)
            if missing:
                tool_ids = list(tool_ids) + missing
                self._sync_layer_checkboxes(tool_ids)

            port_map = {}
            for tid in tool_ids:
                if tid.startswith("skill:"):
                    continue
                meta = self.main.registry_mgr.get_tool(tid)
                default_port = meta.get("launcher", {}).get("default_port")
                if default_port:
                    port_map[tid] = default_port

            state = {
                "session_name": "ai_lsc",
                "base_dir": BASE_DIR,
                "active_tools": tool_ids,
                "port_map": port_map,
                "stack_ready": True,
                "source": "template",
            }
            os.makedirs(self.main.config_root, exist_ok=True)
            state_file = os.path.join(
                self.main.config_root, STATE_FILE_NAME
            )
            _atomic_write_json(state_file, state)

            self.main._populate_services()
            self.main._refresh_pipeline_ticker()
            self.main._refresh_workspace_tab()
            self.main.refresh_models()

        # ── Flow builder ────────────────────────────────────────────

        def refresh(self):
            self.avail_tree.clear()
            state_file = os.path.join(
                self.main.config_root, STATE_FILE_NAME
            )
            installed_tools = []
            if os.path.exists(state_file):
                try:
                    with open(state_file) as f:
                        installed_tools = json.load(f).get(
                            "active_tools", []
                        )
                except Exception:
                    pass

            if installed_tools:
                eco_node = QTreeWidgetItem(
                    ["Ecosystem Infrastructure"]
                )
                self.avail_tree.addTopLevelItem(eco_node)
                for t_id in installed_tools:
                    meta = self.main.registry_mgr.get_tool(t_id)
                    item = QTreeWidgetItem(
                        [meta.get("name", t_id)]
                    )
                    item.setData(0, Qt.UserRole, t_id)
                    eco_node.addChild(item)

            skills_dir = self.main.skills_root
            if os.path.exists(skills_dir):
                skill_node = QTreeWidgetItem(["Runtime Skills"])
                self.avail_tree.addTopLevelItem(skill_node)
                for entry in sorted(os.listdir(skills_dir)):
                    if entry.startswith("."):
                        continue
                    full = os.path.join(skills_dir, entry)
                    if os.path.isfile(full):
                        item = QTreeWidgetItem([entry])
                        item.setData(
                            0, Qt.UserRole, f"skill:{entry}"
                        )
                        skill_node.addChild(item)
            self.avail_tree.expandAll()

            self._sync_lifecycle_state()

        def add_node(self):
            selected = self.avail_tree.currentItem()
            if not selected or not selected.data(0, Qt.UserRole):
                return
            t_id = selected.data(0, Qt.UserRole)
            display = selected.text(0)
            if t_id.startswith("skill:"):
                display = f"[Skill] {display}"

            existing = [
                self.flow_list.item(i).data(Qt.UserRole)
                for i in range(self.flow_list.count())
            ]
            if t_id in existing:
                return

            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, t_id)
            self.flow_list.addItem(item)
            self.validate_flow()

        def remove_node(self):
            row = self.flow_list.currentRow()
            if row >= 0:
                self.flow_list.takeItem(row)
                self.validate_flow()

        def validate_flow(self):
            flow_ids = [
                self.flow_list.item(i).data(Qt.UserRole)
                for i in range(self.flow_list.count())
            ]
            missing = self.main.registry_mgr.check_dependencies(flow_ids)
            if missing:
                dep_names = [
                    self.main.registry_mgr.get_tool(d).get("name", d)
                    for d in missing
                ]
                self.lbl_validation.setText(
                    f"Missing Dependencies: "
                    f"{', '.join(dep_names)}"
                )
                self.lbl_validation.setStyleSheet(
                    "color: #e74c3c; font-weight: bold; font-size: 11px;"
                )
            else:
                self.lbl_validation.setText(
                    "Health: Dependencies Satisfied. Ready to compile."
                )
                self.lbl_validation.setStyleSheet(
                    "color: #2ecc71; font-weight: bold; font-size: 11px;"
                )

        def compile_stack(self):
            flow_ids = [
                self.flow_list.item(i).data(Qt.UserRole)
                for i in range(self.flow_list.count())
            ]
            if not flow_ids:
                return

            port_map = {}
            for t_id in flow_ids:
                if t_id.startswith("skill:"):
                    continue
                meta = self.main.registry_mgr.get_tool(t_id)
                default_port = meta.get(
                    "launcher", {}
                ).get("default_port")
                if default_port:
                    port_map[t_id] = default_port

            state = {
                "active_tools": flow_ids,
                "port_map": port_map,
                "timestamp": datetime.now().isoformat(),
            }
            pipe_file = os.path.join(
                self.main.config_root, PIPELINE_FILE_NAME
            )
            os.makedirs(self.main.config_root, exist_ok=True)
            _atomic_write_json(pipe_file, state)

            # Also update pipeline_state.json to keep everything in sync
            self._compile_state_from_ids(flow_ids)

            self.main.log(
                "Stack orchestration compiled successfully.",
                "StackCompiler",
            )

        def _clear_flow(self) -> None:
            self.flow_list.clear()
            self.lbl_validation.setText("Health: Awaiting Compilation...")
            self.lbl_validation.setStyleSheet(
                "color: #7f8c8d; font-weight: bold; font-size: 11px;"
            )

        def _create_template_from_flow(self) -> None:
            """Save the current flow list as a new stack template."""
            flow_ids = [
                self.flow_list.item(i).data(Qt.UserRole)
                for i in range(self.flow_list.count())
            ]
            if not flow_ids:
                QMessageBox.warning(
                    self, "Empty Flow",
                    "Add tools to the execution flow first."
                )
                return

            dlg_input = QDialog(self)
            dlg_input.setWindowTitle("Save as Stack Template")
            dlg_input.setMinimumWidth(450)
            dlg_layout = QVBoxLayout(dlg_input)

            for field_label, placeholder in [
                ("Name:", "e.g. My Custom Stack"),
                ("Tags:", "e.g. custom, experimental  (comma-separated)"),
                ("Description:", "One-line description"),
            ]:
                row = QHBoxLayout()
                row.addWidget(QLabel(field_label))
                txt = QLineEdit()
                txt.setPlaceholderText(placeholder)
                row.addWidget(txt)
                dlg_layout.addLayout(row)
                if "Name" in field_label:
                    name_edit = txt
                elif "Tags" in field_label:
                    tags_edit = txt
                else:
                    desc_edit = txt

            dlg_layout.addWidget(
                QLabel(f"  {len(flow_ids)} tools will be included.")
            )

            btn_row = QHBoxLayout()
            btn_row.addStretch()
            btn_save = QPushButton("Save")
            btn_save.setStyleSheet(
                "background-color: #27ae60; color: white; "
                "font-weight: bold;"
            )
            btn_cancel = QPushButton("Cancel")
            btn_row.addWidget(btn_save)
            btn_row.addWidget(btn_cancel)
            dlg_layout.addLayout(btn_row)

            saved = {"ok": False}

            def _do_save():
                name = name_edit.text().strip()
                if not name:
                    QMessageBox.warning(
                        dlg_input, "Name Required",
                        "Enter a template name."
                    )
                    return
                tags = [
                    t.strip()
                    for t in tags_edit.text().split(",")
                    if t.strip()
                ]
                desc = desc_edit.text().strip()
                self._template_mgr.create_template(
                    name=name,
                    tools=flow_ids,
                    description=desc,
                    tags=tags,
                    save_dir=os.path.join(
                        BASE_DIR,
                        "skills", "stack-templates", "custom",
                    ),
                )
                self._populate_template_combo()
                saved["ok"] = True
                dlg_input.accept()

            btn_save.clicked.connect(_do_save)
            btn_cancel.clicked.connect(dlg_input.reject)
            dlg_input.exec()

            if saved["ok"]:
                self.main.log(
                    f"Stack template saved with {len(flow_ids)} tools.",
                    "StackCompiler",
                )

        def _sync_lifecycle_state(self) -> None:
            """Mirror the main window's is_stack_prepared state to
            our local activate button."""
            if hasattr(self.main, "is_stack_prepared"):
                self.btn_activate.setEnabled(
                    self.main.is_stack_prepared
                )
                if self.main.is_stack_prepared:
                    self.btn_prepare.setStyleSheet(
                        "background-color: #27ae60; color: white; "
                        "font-weight: bold; padding: 8px; "
                        "border-radius: 4px;"
                    )

        def showEvent(self, event) -> None:
            """Refresh + sync lifecycle state when this tab becomes visible."""
            super().showEvent(event)
            self.refresh()
            self._sync_lifecycle_state()

else:
    IpcStackTab = None