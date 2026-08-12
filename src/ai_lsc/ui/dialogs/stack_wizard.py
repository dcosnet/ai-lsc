"""StackWizard dialog -- metadata-driven component selector with
auto-dependency resolution and stack template support.

Presented at first launch (no ``pipeline_state.json`` found) and on
demand via *Modify Stack State (Wizard)*.  The user can either:

1. **Select a stack template** -- pre-configured tool stacks (e.g. Claude
   Code Setup, SaaS Integrations) that auto-populate the checkboxes.
2. **Manual selection** -- check individual tools from the 10-Layer
   registry, as before.

The wizard resolves missing dependencies, builds a port map, and
serialises the state to disk.
"""

import json
import os

from ai_lsc.constants import BASE_DIR, STATE_FILE_NAME
from ai_lsc.registry.manager import RegistryManager
from ai_lsc.registry.stack_templates.manager import StackTemplateManager

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QRadioButton,
        QScrollArea,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

if _HAS_QT:

    class StackWizard(QDialog):
        """Metadata-driven component selector with template and manual modes.

        Parameters
        ----------
        parent :
            Parent widget (typically the main window).
        registry_mgr :
            Loaded :class:`~ai_lsc.registry.manager.RegistryManager`.
        config_root :
            Directory containing ``pipeline_state.json``.
        extra_template_dirs :
            Optional additional directories to scan for custom stack
            templates.
        """

        # Signal emitted when a template is applied (useful for logging)
        template_applied = Signal(str, int)  # template_name, tool_count

        def __init__(
            self,
            parent,
            registry_mgr: RegistryManager,
            config_root: str,
            extra_template_dirs: list[str] | None = None,
        ) -> None:
            super().__init__(parent)
            self.registry_mgr = registry_mgr
            self.state_file = os.path.join(config_root, STATE_FILE_NAME)
            self.setWindowTitle("AI-LSC Ecosystem Compiler")
            self.setMinimumSize(1200, 800)
            self.checkboxes: dict[str, QCheckBox] = {}
            self._template_mgr = StackTemplateManager(
                extra_dirs=extra_template_dirs
            )
            self._current_mode = "template"  # "template" or "manual"
            self._build_ui()

        # ── UI construction ──────────────────────────────────────────

        def _build_ui(self) -> None:
            layout = QVBoxLayout(self)

            # Title
            title = QLabel("Select Native Ecosystem Components")
            title.setFont(QFont("Segoe UI", 16, QFont.Bold))
            layout.addWidget(title)

            # ── Mode selector (template vs manual) ─────────────────────
            mode_bar = QHBoxLayout()
            self._radio_template = QRadioButton("Start from Stack Template")
            self._radio_manual = QRadioButton("Manual Selection")
            self._radio_template.setChecked(True)
            self._radio_template.toggled.connect(self._on_mode_changed)
            mode_bar.addWidget(self._radio_template)
            mode_bar.addWidget(self._radio_manual)
            mode_bar.addStretch()
            layout.addLayout(mode_bar)

            # ── Template selector panel ────────────────────────────────
            self._template_panel = QWidget()
            tpl_layout = QVBoxLayout(self._template_panel)

            tpl_label = QLabel("Choose a pre-configured stack template:")
            tpl_label.setFont(QFont("Segoe UI", 11))
            tpl_layout.addWidget(tpl_label)

            tpl_row = QHBoxLayout()
            self._template_combo = QComboBox()
            self._template_combo.setMinimumWidth(400)
            self._populate_template_combo()
            tpl_row.addWidget(self._template_combo)

            self._apply_template_btn = QPushButton("Apply Stack Template")
            self._apply_template_btn.setStyleSheet(
                "background-color: #2980b9; padding: 8px 16px; "
                "font-weight: bold; border-radius: 4px;"
            )
            self._apply_template_btn.clicked.connect(self._apply_template)
            tpl_row.addWidget(self._apply_template_btn)
            tpl_layout.addLayout(tpl_row)

            # Template description label
            self._template_desc = QLabel("")
            self._template_desc.setWordWrap(True)
            self._template_desc.setStyleSheet(
                "color: #bdc3c7; padding: 8px; "
                "background-color: #1a1a1a; border-radius: 4px;"
            )
            self._template_desc.setMinimumHeight(60)
            tpl_layout.addWidget(self._template_desc)
            self._template_combo.currentIndexChanged.connect(
                self._on_template_selected
            )
            # Trigger initial description
            if self._template_combo.count() > 0:
                self._on_template_selected(0)

            # Template tags filter
            tag_row = QHBoxLayout()
            tag_label = QLabel("Filter by tag:")
            tag_row.addWidget(tag_label)
            self._tag_combo = QComboBox()
            self._tag_combo.setMinimumWidth(200)
            self._tag_combo.addItem("All")
            self._populate_tag_combo()
            self._tag_combo.currentTextChanged.connect(
                self._on_tag_filter
            )
            tag_row.addWidget(self._tag_combo)
            tag_row.addStretch()
            tpl_layout.addLayout(tag_row)

            layout.addWidget(self._template_panel)

            # ── Tool selection scroll area ─────────────────────────────
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )
            scroll_content = QWidget()
            grid = QGridLayout(scroll_content)

            prev_state = self._load_previous_state()
            row, col = 0, 0
            for layer_name, tools in self.registry_mgr.get_grouped_by_layer().items():
                group = QGroupBox(layer_name)
                vbox = QVBoxLayout()
                for t_id, meta in tools:
                    chk = QCheckBox(
                        f"{meta.get('name', t_id)} ({meta.get('category', '')})"
                    )
                    chk.setToolTip(meta.get("description", ""))
                    chk.setChecked(t_id in prev_state)
                    chk.setProperty("tool_id", t_id)
                    self.checkboxes[t_id] = chk
                    vbox.addWidget(chk)
                group.setLayout(vbox)
                grid.addWidget(group, row, col)
                col += 1
                if col > 2:
                    col, row = 0, row + 1

            scroll.setWidget(scroll_content)
            layout.addWidget(scroll)

            # ── Status bar ───────────────────────────────────────────
            self._status_label = QLabel("")
            self._status_label.setStyleSheet(
                "color: #2ecc71; padding: 4px;"
            )
            layout.addWidget(self._status_label)

            # ── Action buttons ────────────────────────────────────────
            btn_row = QHBoxLayout()

            self._create_tpl_btn = QPushButton(
                "Create Stack Template"
            )
            self._create_tpl_btn.setStyleSheet(
                "background-color: #e67e22; padding: 10px 16px; "
                "font-weight: bold; border-radius: 4px;"
            )
            self._create_tpl_btn.setToolTip(
                "Save the current tool selection as a reusable "
                "stack template"
            )
            self._create_tpl_btn.clicked.connect(
                self._create_template_from_selection
            )
            btn_row.addWidget(self._create_tpl_btn)

            self._clear_btn = QPushButton("Clear All")
            self._clear_btn.setStyleSheet(
                "background-color: #7f8c8d; padding: 10px; "
                "border-radius: 4px;"
            )
            self._clear_btn.clicked.connect(self._clear_all)
            btn_row.addWidget(self._clear_btn)

            btn_row.addStretch()

            self._compile_btn = QPushButton(
                "Serialize State Configuration"
            )
            self._compile_btn.setStyleSheet(
                "background-color: #27ae60; font-size: 14px; "
                "padding: 12px 24px; font-weight: bold; border-radius: 4px;"
            )
            self._compile_btn.clicked.connect(self.compile_state)
            btn_row.addWidget(self._compile_btn)

            layout.addLayout(btn_row)

            # Update status on checkbox change
            for chk in self.checkboxes.values():
                chk.toggled.connect(self._update_selection_count)

            self._update_selection_count()

        # ── Template combo helpers ────────────────────────────────────

        def _populate_template_combo(self) -> None:
            """Fill the template dropdown with all discovered templates."""
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

        def _populate_tag_combo(self) -> None:
            """Fill the tag filter dropdown."""
            all_tags: set[str] = set()
            for tpl in self._template_mgr.list_templates():
                all_tags.update(t.lower() for t in tpl["tags"])
            for tag in sorted(all_tags):
                self._tag_combo.addItem(tag)

        def _on_template_selected(self, index: int) -> None:
            """Update the description when a template is selected."""
            tpl_id = self._template_combo.currentData()
            if tpl_id:
                tpl = self._template_mgr.get_template(tpl_id)
                if tpl:
                    desc = tpl.get("description", "No description")
                    tags = ", ".join(tpl.get("tags", []))
                    ver = tpl.get("version", "1.0")
                    count = len(tpl.get("tools", []))
                    self._template_desc.setText(
                        f"[v{ver}] {desc}\n\n"
                        f"Tags: {tags}  |  Tools: {count}"
                    )

        def _on_tag_filter(self, tag: str) -> None:
            """Filter the template combo by the selected tag."""
            self._template_combo.blockSignals(True)
            self._template_combo.clear()

            templates = (
                self._template_mgr.list_templates()
                if tag == "All"
                else self._template_mgr.filter_by_tag(tag)
            )

            for tpl in templates:
                source_tag = (
                    " [custom]" if tpl["source"] == "custom" else ""
                )
                label = (
                    f"{tpl['name']} "
                    f"({tpl['tool_count']} tools{source_tag})"
                )
                self._template_combo.addItem(label, tpl["id"])

            self._template_combo.blockSignals(False)
            if self._template_combo.count() > 0:
                self._on_template_selected(0)

        def _on_mode_changed(self, checked: bool) -> None:
            """Toggle between template and manual mode."""
            if checked:
                self._current_mode = "template"
                self._template_panel.setVisible(True)
            else:
                self._current_mode = "manual"
                self._template_panel.setVisible(True)  # Keep visible
                self._template_combo.setCurrentIndex(-1)

        # ── Template application ─────────────────────────────────────

        def _apply_template(self) -> None:
            """Load the selected template and populate checkboxes."""
            tpl_id = self._template_combo.currentData()
            if not tpl_id:
                QMessageBox.warning(
                    self, "No Template",
                    "Please select a stack template first."
                )
                return

            tool_ids, new_entries = self._template_mgr.resolve_tool_ids(
                tpl_id, self.registry_mgr
            )

            # Clear all checkboxes first
            for chk in self.checkboxes.values():
                chk.setChecked(False)

            # Check tools from the template
            applied = 0
            for tid in tool_ids:
                if tid in self.checkboxes:
                    self.checkboxes[tid].setChecked(True)
                    applied += 1

            # Register new tools (git-source entries) with the registry
            if new_entries:
                for entry in new_entries:
                    tid = entry.get("id", "")
                    if tid and tid not in self.registry_mgr.data:
                        self.registry_mgr.data[tid] = entry
                        self.registry_mgr.registry_file.write_text(
                            json.dumps(
                                self.registry_mgr.data, indent=4
                            ),
                            encoding="utf-8",
                        )

            tpl = self._template_mgr.get_template(tpl_id)
            tpl_name = tpl.get("name", tpl_id) if tpl else tpl_id
            self.template_applied.emit(tpl_name, applied)

            QMessageBox.information(
                self,
                "Stack Template Applied",
                f"Applied '{tpl_name}': {applied} tools selected"
                f"{f', {len(new_entries)} new tools registered' if new_entries else ''}."
                "\n\nReview the selection below, then click "
                "'Serialize State Configuration'.",
            )
            self._update_selection_count()

        def _create_template_from_selection(self) -> None:
            """Save the currently checked tools as a new stack template."""
            selected = [
                tid for tid, chk in self.checkboxes.items()
                if chk.isChecked()
            ]
            if not selected:
                QMessageBox.warning(
                    self, "No Selection",
                    "Check at least one tool before creating a template."
                )
                return

            # Prompt for template metadata
            dlg = QDialog(self)
            dlg.setWindowTitle("Create Stack Template")
            dlg.setMinimumWidth(450)
            dlg_layout = QVBoxLayout(dlg)

            form = QHBoxLayout()
            form.addWidget(QLabel("Name:"))
            txt_name = QLineEdit()
            txt_name.setPlaceholderText(
                "e.g. My Custom Stack"
            )
            form.addWidget(txt_name)
            dlg_layout.addLayout(form)

            form2 = QHBoxLayout()
            form2.addWidget(QLabel("Tags:"))
            txt_tags = QLineEdit()
            txt_tags.setPlaceholderText(
                "e.g. custom, experimental  (comma-separated)"
            )
            form2.addWidget(txt_tags)
            dlg_layout.addLayout(form2)

            form3 = QHBoxLayout()
            form3.addWidget(QLabel("Description:"))
            txt_desc = QLineEdit()
            txt_desc.setPlaceholderText(
                "One-line description of this stack"
            )
            form3.addWidget(txt_desc)
            dlg_layout.addLayout(form3)

            dlg_layout.addWidget(
                QLabel(f"  {len(selected)} tools will be included.")
            )

            btn_box = QHBoxLayout()
            btn_box.addStretch()
            btn_save = QPushButton("Save Template")
            btn_save.setStyleSheet(
                "background-color: #27ae60; color: white; "
                "font-weight: bold;"
            )
            btn_cancel = QPushButton("Cancel")
            btn_box.addWidget(btn_save)
            btn_box.addWidget(btn_cancel)
            dlg_layout.addLayout(btn_box)

            result = {"saved": False}

            def _do_save():
                name = txt_name.text().strip()
                if not name:
                    QMessageBox.warning(
                        dlg, "Name Required",
                        "Enter a template name."
                    )
                    return
                tags = [
                    t.strip()
                    for t in txt_tags.text().split(",")
                    if t.strip()
                ]
                desc = txt_desc.text().strip()
                tpl = self._template_mgr.create_template(
                    name=name,
                    tools=selected,
                    description=desc,
                    tags=tags,
                    save_dir=os.path.join(
                        BASE_DIR, "skills", "stack-templates", "custom"
                    ),
                )
                # Refresh the template combo
                self._populate_template_combo()
                result["saved"] = True
                dlg.accept()

            btn_save.clicked.connect(_do_save)
            btn_cancel.clicked.connect(dlg.reject)
            dlg.exec()

            if result["saved"]:
                QMessageBox.information(
                    self,
                    "Template Created",
                    f"Stack template saved with "
                    f"{len(selected)} tools.\n\n"
                    "It now appears in the template dropdown.",
                )

        # ── Selection helpers ──────────────────────────────────────────

        def _clear_all(self) -> None:
            """Uncheck all tool checkboxes."""
            for chk in self.checkboxes.values():
                chk.setChecked(False)
            self._update_selection_count()

        def _update_selection_count(self) -> None:
            """Update the status bar with selection count."""
            count = sum(1 for c in self.checkboxes.values() if c.isChecked())
            total = len(self.checkboxes)
            self._status_label.setText(
                f"{count} of {total} tools selected"
            )

        # ── State persistence ──────────────────────────────────────────

        def _load_previous_state(self) -> set[str]:
            if not os.path.exists(self.state_file):
                return set()
            try:
                with open(self.state_file, encoding="utf-8") as f:
                    return set(
                        json.load(f).get("active_tools", [])
                    )
            except (OSError, ValueError, json.JSONDecodeError):
                return set()

        def compile_state(self) -> None:
            """Gather checked tools, resolve deps, write state file."""
            selected = [
                tid for tid, chk in self.checkboxes.items()
                if chk.isChecked()
            ]
            missing = self.registry_mgr.check_dependencies(selected)
            if missing:
                dep_names = [
                    self.registry_mgr.get_tool(d).get("name", d)
                    for d in missing
                ]
                msg = QMessageBox(self)
                msg.setWindowTitle("Missing Dependencies Detected")
                msg.setText(
                    f"Selected tools require:\n\n"
                    f"{', '.join(dep_names)}\n\nAuto-include them?"
                )
                msg.setStandardButtons(
                    QMessageBox.Yes | QMessageBox.No
                )
                if msg.exec() == QMessageBox.Yes:
                    selected.extend(missing)
                    for tid in missing:
                        if tid in self.checkboxes:
                            self.checkboxes[tid].setChecked(True)

            port_map = {
                tid: self.registry_mgr.get_tool(tid)
                .get("launcher", {}).get("default_port")
                for tid in selected
            }
            state = {
                "session_name": "ai_lsc",
                "base_dir": BASE_DIR,
                "active_tools": selected,
                "port_map": port_map,
                "stack_ready": True,
                "source": self._current_mode,
            }
            # H-03: atomic write so an interrupted wizard save cannot
            # corrupt the pipeline state file.
            from ai_lsc.ui.main_window import _atomic_write_json
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            _atomic_write_json(self.state_file, state)
            self.accept()

else:
    StackWizard = None  # type: ignore[assignment, misc]
