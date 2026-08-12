"""DatabaseManager widget — full CRUD editor for the tool registry.

Presents a split-pane layout: a searchable / filterable tool table on the
left and a scrollable edit form on the right.  Every field from the
registry schema is editable — categorisation (layer, role, category,
level), all 8 flags, installer spec, launcher spec, dependencies,
license, description, and filesystem paths.

**Categorisation cascade**: selecting a Category auto-populates Layer,
Level, and Role from the built-in category map (derived from the
registry).  The user can still override any of them.

Changes are validated against the registry schema before being written
to ``ecosystem.json`` via atomic write.
"""

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QBrush, QColor, QFont
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSpinBox,
        QSplitter,
        QStyledItemDelegate,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

# ── Category → default Layer / Level / Role mapping ──────────────────
# Derived from the canonical registry.  When the user picks a category
# these fields auto-fill; the user can still override afterwards.
CATEGORY_MAP: dict[str, dict[str, object]] = {
    "AI Agent":                     {"layer": "Orchestrators", "level": 5,  "role": "Sensory Bridge"},
    "AI Assistant Platform":        {"layer": "User Interfaces", "level": 8,  "role": "Central Intelligence"},
    "AI Augmentation":              {"layer": "Orchestrators", "level": 5,  "role": "Curation"},
    "AI Coding Agent":              {"layer": "DevOps", "level": 9,  "role": "Autonomous Coder"},
    "AI Monitoring":                {"layer": "Observability", "level": 7,  "role": "Health Monitor"},
    "AI Observability":             {"layer": "Observability", "level": 7,  "role": "LLM Tracing"},
    "AI Operating System":          {"layer": "DevOps", "level": 9,  "role": "OS Integration"},
    "Academic References":          {"layer": "Knowledge Management", "level": 10, "role": "Reference Manager"},
    "Agent Framework":              {"layer": "Orchestrators", "level": 5,  "role": "Multi-Agent"},
    "Agent Network":                {"layer": "DevOps", "level": 9,  "role": "Discovery"},
    "Agent OS":                     {"layer": "Orchestrators", "level": 5,  "role": "Hands"},
    "Agent Toolkit":                {"layer": "Orchestrators", "level": 5,  "role": "Tool Integration"},
    "Agent Workflow":               {"layer": "Orchestrators", "level": 5,  "role": "Reasoning"},
    "Algorithm Toolkit":            {"layer": "DevOps", "level": 9,  "role": "Hands"},
    "Analytical Database":          {"layer": "Host Platform", "level": 1,  "role": "Foundation"},
    "Antivirus":                    {"layer": "Security", "level": 6,  "role": "Scanner"},
    "Audio Parsing":                {"layer": "Knowledge Management", "level": 10, "role": "Memory"},
    "Auth":                         {"layer": "Security", "level": 6,  "role": "Identity"},
    "Build Monitoring":             {"layer": "Orchestrators", "level": 5,  "role": "Monitoring"},
    "Cache":                        {"layer": "Host Platform", "level": 1,  "role": "Foundation"},
    "Chat":                         {"layer": "User Interfaces", "level": 8,  "role": "Face"},
    "Chat Agent Platform":          {"layer": "User Interfaces", "level": 8,  "role": "Face"},
    "Chat Frontend":                {"layer": "User Interfaces", "level": 8,  "role": "Face"},
    "Cluster SSH":                  {"layer": "Orchestrators", "level": 5,  "role": "Coordination"},
    "Code Analysis":                {"layer": "DevOps", "level": 9,  "role": "Inspector"},
    "Code Generation":              {"layer": "DevOps", "level": 9,  "role": "Hands"},
    "Computer Vision":              {"layer": "User Interfaces", "level": 8,  "role": "Vision"},
    "Config Management":            {"layer": "DevOps", "level": 9,  "role": "Configuration Management"},
    "Container Security":           {"layer": "Security", "level": 6,  "role": "Scanner"},
    "Containers":                   {"layer": "Host Platform", "level": 1,  "role": "Container Runtime"},
    "Context Manager":              {"layer": "DevOps", "level": 9,  "role": "Context"},
    "Cortex Memory":                {"layer": "Knowledge Management", "level": 10, "role": "Memory"},
    "Dashboard":                     {"layer": "User Interfaces", "level": 8,  "role": "Face"},
    "Data Pipeline":                {"layer": "Knowledge Management", "level": 10,  "role": "Ingestion"},
    "Data Sync":                    {"layer": "Knowledge Management", "level": 10,  "role": "Integration"},
    "Database":                     {"layer": "Host Platform", "level": 1,  "role": "Foundation"},
    "Desktop Agent":                {"layer": "User Interfaces", "level": 8,  "role": "Face"},
    "Dev Automation":               {"layer": "DevOps", "level": 9,  "role": "Hands"},
    "Development":                  {"layer": "DevOps", "level": 9,  "role": "Hands"},
    "Distributed Compilation":     {"layer": "Orchestrators", "level": 5,  "role": "Distribution"},
    "Distributed Compute":          {"layer": "Orchestrators", "level": 5,  "role": "Scaling"},
    "Document Converter":           {"layer": "Knowledge Management", "level": 10, "role": "File Parsing"},
    "Document Management":          {"layer": "Knowledge Management", "level": 10, "role": "Document Archive"},
    "Document Understanding":       {"layer": "Knowledge Management", "level": 10, "role": "Comprehension"},
    "Ebook Library":                {"layer": "Knowledge Management", "level": 10, "role": "Library Manager"},
    "Ecosystem Dashboard":          {"layer": "User Interfaces", "level": 8,  "role": "Face"},
    "Efficient LLM":                {"layer": "Engines", "level": 4,  "role": "Engine"},
    "File Parsing":                 {"layer": "Knowledge Management", "level": 10, "role": "Memory"},
    "Find Tool":                    {"layer": "Development Environment", "level": 2,  "role": "Search"},
    "GPU":                          {"layer": "GPU Runtimes", "level": 3,  "role": "Acceleration"},
    "GPU Computing":                {"layer": "Development Environment", "level": 2,  "role": "GPU Acceleration"},
    "Graph Database":               {"layer": "Knowledge Management", "level": 10,  "role": "Memory"},
    "Graph RAG":                    {"layer": "Knowledge Management", "level": 10,  "role": "Knowledge Synthesis"},
    "Homepage":                     {"layer": "User Interfaces", "level": 8,  "role": "Face"},
    "IaC":                          {"layer": "DevOps", "level": 9,  "role": "Infrastructure as Code"},
    "IaC Control Plane":            {"layer": "DevOps", "level": 9,  "role": "Infrastructure as Code"},
    "IaC Wrapper":                  {"layer": "DevOps", "level": 9,  "role": "Infrastructure as Code"},
    "Image Generation":             {"layer": "User Interfaces", "level": 8,  "role": "Face"},
    "Intrusion Prevention":         {"layer": "Security", "level": 6,  "role": "IDS"},
    "Knowledge Graph":              {"layer": "DevOps", "level": 9,  "role": "Graph Builder"},
    "Knowledge Graph Notes":        {"layer": "User Interfaces", "level": 8,  "role": "Face"},
    "LLM Evaluation":               {"layer": "Observability", "level": 7,  "role": "Evaluation"},
    "LLM Fine-tuning":              {"layer": "GPU Runtimes", "level": 3,  "role": "Abliteration"},
    "LLM Framework":                {"layer": "Orchestrators", "level": 5,  "role": "Orchestration"},
    "LLM GUI":                      {"layer": "User Interfaces", "level": 8,  "role": "Face"},
    "LLM Router":                   {"layer": "Orchestrators", "level": 5,  "role": "API Gateway"},
    "LLM Runtime":                  {"layer": "Engines", "level": 4,  "role": "Engine"},
    "LLM Serving":                  {"layer": "Orchestrators", "level": 5,  "role": "Scaling"},
    "MCP Server":                   {"layer": "Orchestrators", "level": 5,  "role": "Code Audit"},
    "Metrics":                      {"layer": "Observability", "level": 7,  "role": "Metrics Collector"},
    "Mixed Precision":              {"layer": "GPU Runtimes", "level": 3,  "role": "Optimization"},
    "Model Training":               {"layer": "Development Environment", "level": 2,  "role": "Training"},
    "Multi-Agent":                  {"layer": "Orchestrators", "level": 5,  "role": "Coordination"},
    "Notes":                        {"layer": "Knowledge Management", "level": 10, "role": "Note Taking"},
    "OCI Export":                   {"layer": "DevOps", "level": 9,  "role": "Runtime Packaging"},
    "Outliner":                     {"layer": "Knowledge Management", "level": 10,  "role": "Knowledge Graph"},
    "PDF Pipeline":                 {"layer": "Knowledge Management", "level": 10,  "role": "Extraction"},
    "Parser":                       {"layer": "Development Environment", "level": 2,  "role": "Parsing"},
    "Persistent Memory":            {"layer": "Knowledge Management", "level": 10,  "role": "Memory"},
    "Pipeline":                     {"layer": "Orchestrators", "level": 5,  "role": "Pipeline Orchestrator"},
    "Policy Engine":                {"layer": "Security", "level": 6,  "role": "Policy"},
    "Procfile Runner":              {"layer": "DevOps", "level": 9,  "role": "Process Manager"},
    "Project Management":           {"layer": "DevOps", "level": 9,  "role": "Management"},
    "Prompt Tooling":               {"layer": "DevOps", "level": 9,  "role": "Prompt Management"},
    "Provisioning":                 {"layer": "DevOps", "level": 9,  "role": "Provisioning"},
    "Proxy":                        {"layer": "Orchestrators", "level": 5,  "role": "API Gateway"},
    "Reasoning Engine":             {"layer": "Orchestrators", "level": 5,  "role": "Brain"},
    "Runtime":                      {"layer": "Development Environment", "level": 2,  "role": "Build System"},
    "Sandbox":                      {"layer": "DevOps", "level": 9,  "role": "Isolation"},
    "Search Engine":                {"layer": "Knowledge Management", "level": 10, "role": "Memory"},
    "Search Tool":                  {"layer": "Development Environment", "level": 2,  "role": "Search"},
    "Secrets Management":           {"layer": "Security", "level": 6,  "role": "Secrets"},
    "Serverless Framework":         {"layer": "Development Environment", "level": 2,  "role": "Full-Stack Framework"},
    "Single-File LLM":              {"layer": "Engines", "level": 4,  "role": "Engine"},
    "Skill Analysis":               {"layer": "DevOps", "level": 9,  "role": "Assessment"},
    "Skill Inspection":             {"layer": "DevOps", "level": 9,  "role": "Analysis"},
    "Spaced Repetition":            {"layer": "Knowledge Management", "level": 10,  "role": "Memory"},
    "Spec Writer":                  {"layer": "DevOps", "level": 9,  "role": "Documentation"},
    "Speech Recognition":           {"layer": "User Interfaces", "level": 8,  "role": "Senses"},
    "Task Runner":                  {"layer": "DevOps", "level": 9,  "role": "Scheduler"},
    "Telemetry":                    {"layer": "Observability", "level": 7,  "role": "Collector"},
    "Terminal":                     {"layer": "Host Platform", "level": 1,  "role": "Multiplexer"},
    "Text-to-Speech":               {"layer": "User Interfaces", "level": 8,  "role": "Voice"},
    "Uncensored Models":            {"layer": "Engines", "level": 4,  "role": "Engine"},
    "VCS":                          {"layer": "Host Platform", "level": 1,  "role": "Version Control"},
    "Vector Engine":                {"layer": "Knowledge Management", "level": 10,  "role": "Embedding"},
    "Vector Store":                 {"layer": "Knowledge Management", "level": 10,  "role": "Memory"},
    "Visualization":                {"layer": "Observability", "level": 7,  "role": "Dashboard"},
    "Web Crawler":                  {"layer": "Knowledge Management", "level": 10,  "role": "Data Harvesting"},
    "Workflow":                     {"layer": "Orchestrators", "level": 5,  "role": "Visual Builder"},
    "Workflow Automation":          {"layer": "Orchestrators", "level": 5,  "role": "Workflow Orchestrator"},
}

# ── Field-constant lookups (populated once on first use) ─────────────

_LAYER_ORDER: list[str] = []
_ALL_CATEGORIES: list[str] = []
_ROLE_SET: set[str] = set()

_LICENSE_SPDX_IDS: list[str] = []
_INSTALLER_TYPES: list[str] = [
    "ollama", "uv", "pipx", "pip", "npm",
    "git", "git_node", "pacman", "dnf", "apt",
    "script", "custom",
]
_LAUNCHER_TYPES: list[str] = ["systemd", "tmux", "desktop", "lxc"]

_FLAG_KEYS: list[str] = [
    "has_cli", "has_gui", "has_web",
    "is_ollama",
    "is_passive", "is_mcp", "is_skills_collection",
]

_FLAG_LABELS: dict[str, str] = {
    "has_cli": "CLI",
    "has_gui": "GUI",
    "has_web": "Web UI",
    "is_ollama": "Ollama-native",
    "is_passive": "Passive (library/collection)",
    "is_mcp": "MCP API tool",
    "is_skills_collection": "Skills collection",
}


def _populate_lookups(registry: dict) -> None:
    """Populate the layer / category / role dropdowns from live data."""
    global _LAYER_ORDER, _ALL_CATEGORIES, _ROLE_SET, _LICENSE_SPDX_IDS
    if _LAYER_ORDER:
        return
    from ai_lsc.constants import NAV_LAYER_ORDER
    _LAYER_ORDER = list(NAV_LAYER_ORDER)

    # Categories: start with the canonical CATEGORY_MAP keys, then
    # append any extras found in live data.
    seen_cats: set[str] = set(CATEGORY_MAP.keys())
    for meta in registry.values():
        if not isinstance(meta, dict):
            continue
        cat = meta.get("category", "")
        if cat:
            seen_cats.add(cat)
        role = meta.get("role", "")
        if role:
            _ROLE_SET.add(role)
    _ALL_CATEGORIES = sorted(seen_cats)

    try:
        from ai_lsc.registry.licenses import CATALOG
        _LICENSE_SPDX_IDS = sorted(CATALOG.keys())
    except ImportError:
        _LICENSE_SPDX_IDS = ["MIT", "Apache-2.0", "GPL-3.0", "Proprietary"]


def _set_combo_text(combo: QComboBox, text: str) -> None:
    """Set a QComboBox to *text*, adding it if not present."""
    idx = combo.findText(text)
    if idx >= 0:
        combo.setCurrentIndex(idx)
    else:
        combo.setEditText(text)


if _HAS_QT:

    class _CategoryDelegate(QStyledItemDelegate):
        """Combo-box delegate for the Category column in the tool table.

        When the user picks a new category the change is immediately
        cascaded (layer / level / role) and auto-saved to ecosystem.json.
        """

        def __init__(self, parent: DatabaseManager) -> None:
            super().__init__(parent)
            self._db: DatabaseManager = parent

        def createEditor(self, parent, option, index):
            combo = QComboBox(parent)
            combo.addItem("")  # blank = clear
            for cat in _ALL_CATEGORIES:
                combo.addItem(cat)
            combo.setEditable(True)
            # Pre-select current value
            current = index.data(Qt.DisplayRole) or ""
            idx = combo.findText(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                combo.setEditText(current)
            combo.currentTextChanged.connect(
                lambda text, idx=index: self._on_category_picked(
                    idx, text
                )
            )
            return combo

        def setModelData(self, editor, model, index):
            text = editor.currentText()
            model.setData(index, text, Qt.DisplayRole)

        def _on_category_picked(
            self, table_index, new_category: str
        ) -> None:
            row = table_index.row()
            tool_id_item = self._db.tool_table.item(row, 0)
            if not tool_id_item:
                return
            tool_id = tool_id_item.data(Qt.UserRole)
            if not tool_id or not new_category:
                return

            # Cascade: update layer / level / role from CATEGORY_MAP
            mapping = CATEGORY_MAP.get(new_category)
            meta = self._db.main.registry_mgr.data.get(tool_id, {})
            if mapping:
                meta["layer"] = mapping["layer"]
                meta["level"] = mapping["level"]
                meta["role"] = mapping["role"]
            meta["category"] = new_category

            # Write back
            self._db.main.registry_mgr.data[tool_id] = meta
            from ai_lsc.ui.main_window import _atomic_write_json
            _atomic_write_json(
                self._db.main.registry_mgr.registry_file,
                self._db.main.registry_mgr.data,
            )

            # Update table cells for this row
            lvl_item = self._db.tool_table.item(row, 2)
            if lvl_item:
                lvl_item.setText(str(meta.get("level", "")))
            cat_item = self._db.tool_table.item(row, 3)
            if cat_item:
                cat_item.setText(new_category)

            # If this tool is currently loaded in the edit form,
            # refresh it too.
            if tool_id == self._db._current_tool_id:
                self._db._load_tool(tool_id)

            self._db._show_status(
                "ok",
                f"<b>{tool_id}</b> category → "
                f"<b>{new_category}</b> (auto-saved).",
            )

    class DatabaseManager(QWidget):
        """Full CRUD editor for the ecosystem tool registry.

        Layout
        ------
        Left  (40 %) — searchable table of all tools.
        Right (60 %) — scrollable edit form for the selected tool.

        The form groups fields into logical sections that match the
        registry schema: Identity, Categorisation, Installer, Launcher,
        Flags, License, Dependencies, Filesystem.

        **Categorisation cascade**: changing Category auto-fills Layer,
        Level, and Role from :data:`CATEGORY_MAP`.
        """

        def __init__(self, main_window) -> None:
            super().__init__()
            self.main = main_window
            self._current_tool_id: str | None = None
            self._dirty = False
            self._loading = False  # guard to suppress dirty during programmatic set

            _populate_lookups(main_window.registry_mgr.get_all_tools())

            root = QVBoxLayout(self)
            root.setContentsMargins(4, 4, 4, 4)

            # ── Title bar ────────────────────────────────────────────
            title = QLabel(
                "<b>Tool Database Manager</b> "
                "<span style='color:#7f8c8d;'>"
                "— edit categorisation, flags, and metadata per tool"
                "</span>"
            )
            title.setWordWrap(True)
            root.addWidget(title)

            # ── Status bar (validation results / save feedback) ──────
            self.status_label = QLabel("")
            self.status_label.setWordWrap(True)
            self.status_label.setStyleSheet(
                "padding: 4px 8px; border-radius: 4px;"
            )
            root.addWidget(self.status_label)

            # ── Splitter ─────────────────────────────────────────────
            splitter = QSplitter(Qt.Horizontal)

            # ── Left panel: tool list ────────────────────────────────
            left = QWidget()
            left_layout = QVBoxLayout(left)
            left_layout.setContentsMargins(0, 0, 0, 0)

            # Filter row
            filter_row = QHBoxLayout()
            filter_row.addWidget(QLabel("Search:"))
            self.search_edit = QLineEdit()
            self.search_edit.setPlaceholderText(
                "Filter by tool_id, name, category..."
            )
            self.search_edit.textChanged.connect(self._apply_filter)
            filter_row.addWidget(self.search_edit)

            self.layer_filter = QComboBox()
            self.layer_filter.addItem("All Layers")
            for layer in _LAYER_ORDER:
                self.layer_filter.addItem(layer)
            self.layer_filter.currentIndexChanged.connect(self._apply_filter)
            filter_row.addWidget(QLabel("Layer:"))
            filter_row.addWidget(self.layer_filter)
            left_layout.addLayout(filter_row)

            # Tool table
            self.tool_table = QTableWidget()
            self.tool_table.setColumnCount(5)
            self.tool_table.setHorizontalHeaderLabels([
                "Tool ID", "Name", "Lvl", "Category", "License",
            ])
            self.tool_table.setSelectionBehavior(
                QTableWidget.SelectRows
            )
            self.tool_table.setSelectionMode(
                QTableWidget.SingleSelection
            )
            # Only the Category column (3) is editable via delegate;
            # all other columns are read-only.
            self.tool_table.setEditTriggers(
                QTableWidget.SelectedClicked
            )
            self.tool_table.setItemDelegateForColumn(
                3, _CategoryDelegate(self)
            )
            self.tool_table.setSortingEnabled(True)
            self.tool_table.verticalHeader().setDefaultSectionSize(24)
            self.tool_table.horizontalHeader().setStretchLastSection(
                True
            )
            self.tool_table.setColumnWidth(0, 160)
            self.tool_table.setColumnWidth(1, 200)
            self.tool_table.setColumnWidth(2, 36)
            self.tool_table.setColumnWidth(3, 150)
            self.tool_table.setColumnWidth(4, 120)
            self.tool_table.itemSelectionChanged.connect(
                self._on_tool_selected
            )
            left_layout.addWidget(self.tool_table)

            # Action buttons below table
            btn_row = QHBoxLayout()
            self.btn_add = QPushButton("+ Add Tool")
            self.btn_add.clicked.connect(self._add_tool)
            btn_row.addWidget(self.btn_add)
            self.btn_delete = QPushButton("Delete Tool")
            self.btn_delete.clicked.connect(self._delete_tool)
            btn_row.addWidget(self.btn_delete)
            self.btn_validate_all = QPushButton("Validate All")
            self.btn_validate_all.clicked.connect(
                self._validate_all
            )
            btn_row.addWidget(self.btn_validate_all)
            left_layout.addLayout(btn_row)

            splitter.addWidget(left)

            # ── Right panel: edit form ───────────────────────────────
            self.edit_scroll = QScrollArea()
            self.edit_scroll.setWidgetResizable(True)
            self.edit_container = QWidget()
            self.edit_layout = QVBoxLayout(self.edit_container)
            self.edit_layout.setSpacing(8)
            self.edit_container.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )
            self.edit_scroll.setWidget(self.edit_container)

            # No-selection placeholder
            self.placeholder = QLabel(
                "<i>Select a tool from the table to edit its properties."
                "</i>"
            )
            self.placeholder.setAlignment(Qt.AlignCenter)
            self.placeholder.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )
            self.placeholder.setStyleSheet("color: #7f8c8d; padding: 40px;")
            self.edit_layout.addWidget(self.placeholder)

            splitter.addWidget(self.edit_scroll)
            splitter.setStretchFactor(0, 4)
            splitter.setStretchFactor(1, 6)

            root.addWidget(splitter, 1)

            # Populate the table
            self._populate_table()

        # ── Table population ──────────────────────────────────────────

        def _populate_table(self) -> None:
            registry = self.main.registry_mgr.get_all_tools()
            self.tool_table.setRowCount(0)
            self._all_rows: list[tuple[str, dict]] = []
            for t_id, meta in sorted(registry.items()):
                if not isinstance(meta, dict):
                    continue
                self._all_rows.append((t_id, meta))

            self._apply_filter()

        def _apply_filter(self) -> None:
            search = self.search_edit.text().lower().strip()
            layer_idx = self.layer_filter.currentIndex()
            layer_filter = (
                _LAYER_ORDER[layer_idx - 1]
                if layer_idx > 0
                else ""
            )

            self.tool_table.setRowCount(0)
            row_idx = 0
            for t_id, meta in self._all_rows:
                name = meta.get("name", t_id)
                cat = meta.get("category", "")
                layer = meta.get("layer", "")
                lic = meta.get("license", "")

                if layer_filter and layer != layer_filter:
                    continue
                if search:
                    haystack = f"{t_id} {name} {cat} {layer} {lic}".lower()
                    if search not in haystack:
                        continue

                self.tool_table.insertRow(row_idx)
                items = [
                    t_id,
                    name,
                    str(meta.get("level", "")),
                    cat,
                    lic,
                ]
                for col, text in enumerate(items):
                    item = QTableWidgetItem(text)
                    item.setData(Qt.UserRole, t_id)
                    if col != 3:
                        # Only Category column is editable
                        item.setFlags(
                            item.flags() & ~Qt.ItemIsEditable
                        )
                    if col == 0:
                        item.setFont(
                            QFont("Segoe UI", 9, QFont.Bold)
                        )
                    self.tool_table.setItem(row_idx, col, item)
                row_idx += 1

        def _on_tool_selected(self) -> None:
            rows = self.tool_table.selectionModel().selectedRows()
            if not rows:
                return
            row = rows[0].row()
            tool_id = (
                self.tool_table.item(row, 0)
                .data(Qt.UserRole)
            )
            if tool_id == self._current_tool_id:
                return
            self._save_current_if_dirty()
            self._load_tool(tool_id)

        # ── Edit form builders ────────────────────────────────────────

        def _clear_edit_form(self) -> None:
            """Remove all edit widgets from the form."""
            while self.edit_layout.count():
                child = self.edit_layout.takeAt(0)
                w = child.widget()
                if w:
                    w.deleteLater()

        def _load_tool(self, tool_id: str) -> None:
            self._current_tool_id = tool_id
            self._dirty = False
            self._loading = True
            self._clear_edit_form()

            meta = self.main.registry_mgr.get_tool(tool_id)
            if not meta:
                self.edit_layout.addWidget(QLabel(
                    f"<b>{tool_id}</b> not found in registry."
                ))
                self._loading = False
                return

            # ── Identity ────────────────────────────────────────────
            grp_id = QGroupBox("Identity")
            form_id = QFormLayout(grp_id)

            self.f_tool_id = QLabel(tool_id)
            self.f_tool_id.setTextInteractionFlags(
                Qt.TextSelectableByMouse
            )
            self.f_tool_id.setStyleSheet(
                "font-family: monospace; color: #3498db;"
            )
            form_id.addRow("Tool ID:", self.f_tool_id)

            self.f_name = QLineEdit(meta.get("name", tool_id))
            form_id.addRow("Name:", self.f_name)

            self.f_description = QTextEdit(
                meta.get("description", "")
            )
            self.f_description.setMaximumHeight(60)
            form_id.addRow("Description:", self.f_description)

            self.edit_layout.addWidget(grp_id)

            # ── Categorisation ─────────────────────────────────────
            grp_cat = QGroupBox("Categorisation")
            form_cat = QFormLayout(grp_cat)

            # Category — fixed dropdown, NOT editable.
            # This is the primary selector; Layer / Level / Role
            # auto-fill when it changes.
            self.f_category = QComboBox()
            self.f_category.setEditable(False)
            self.f_category.addItem("")  # blank = custom / unknown
            for cat in _ALL_CATEGORIES:
                self.f_category.addItem(cat)
            idx = self.f_category.findText(meta.get("category", ""))
            if idx >= 0:
                self.f_category.setCurrentIndex(idx)
            else:
                self.f_category.setCurrentIndex(0)
            form_cat.addRow("Category:", self.f_category)

            # Level — auto-determined from category.
            self.f_level = QSpinBox()
            self.f_level.setRange(1, 10)
            self.f_level.setValue(meta.get("level", 1))
            form_cat.addRow("Level:", self.f_level)

            # Layer — auto-determined from category.
            self.f_layer = QComboBox()
            self.f_layer.setEditable(True)
            for layer in _LAYER_ORDER:
                self.f_layer.addItem(layer)
            idx = self.f_layer.findText(meta.get("layer", ""))
            if idx >= 0:
                self.f_layer.setCurrentIndex(idx)
            else:
                self.f_layer.setEditText(meta.get("layer", ""))
            form_cat.addRow("Layer:", self.f_layer)

            # Role — auto-selected from category default.
            self.f_role = QComboBox()
            self.f_role.setEditable(True)
            for role in sorted(_ROLE_SET):
                self.f_role.addItem(role)
            idx = self.f_role.findText(meta.get("role", ""))
            if idx >= 0:
                self.f_role.setCurrentIndex(idx)
            else:
                self.f_role.setEditText(meta.get("role", ""))
            form_cat.addRow("Role:", self.f_role)

            # Cascade signal: category change → auto-fill level/layer/role
            self.f_category.currentTextChanged.connect(
                self._on_category_changed
            )

            self.edit_layout.addWidget(grp_cat)

            # ── Installer ──────────────────────────────────────────
            inst = meta.get("installer", {})
            grp_inst = QGroupBox("Installer")
            form_inst = QFormLayout(grp_inst)

            self.f_inst_type = QComboBox()
            self.f_inst_type.addItems(_INSTALLER_TYPES)
            idx = self.f_inst_type.findText(
                inst.get("type", "pacman")
            )
            if idx >= 0:
                self.f_inst_type.setCurrentIndex(idx)
            form_inst.addRow("Type:", self.f_inst_type)

            self.f_inst_pkg = QLineEdit(inst.get("pkg", ""))
            form_inst.addRow("Package / URL:", self.f_inst_pkg)

            self.f_inst_cmd = QLineEdit(inst.get("cmd", "") or "")
            self.f_inst_cmd.setPlaceholderText(
                "(script type only)"
            )
            form_inst.addRow("Command:", self.f_inst_cmd)

            self.f_inst_post = QLineEdit(
                inst.get("post_install", "") or ""
            )
            form_inst.addRow("Post-install:", self.f_inst_post)

            self.f_inst_update = QLineEdit(
                inst.get("update_cmd", "") or ""
            )
            form_inst.addRow("Update cmd:", self.f_inst_update)

            self.edit_layout.addWidget(grp_inst)

            # ── Launcher ──────────────────────────────────────────
            launch = meta.get("launcher", {})
            grp_launch = QGroupBox("Launcher")
            form_launch = QFormLayout(grp_launch)

            self.f_launch_type = QComboBox()
            self.f_launch_type.addItems(_LAUNCHER_TYPES)
            idx = self.f_launch_type.findText(
                launch.get("type", "desktop")
            )
            if idx >= 0:
                self.f_launch_type.setCurrentIndex(idx)
            form_launch.addRow("Type:", self.f_launch_type)

            self.f_launch_cmd = QLineEdit(launch.get("cmd", ""))
            form_launch.addRow("Command:", self.f_launch_cmd)

            self.f_launch_port = QSpinBox()
            self.f_launch_port.setRange(0, 65535)
            port_val = launch.get("default_port")
            self.f_launch_port.setValue(port_val if port_val else 0)
            self.f_launch_port.setSpecialValueText("None")
            form_launch.addRow("Default Port:", self.f_launch_port)

            self.edit_layout.addWidget(grp_launch)

            # ── Flags ──────────────────────────────────────────────
            grp_flags = QGroupBox("Flags")
            flags_layout = QVBoxLayout(grp_flags)

            flags = meta.get("flags", {})
            self._flag_widgets: dict[str, QCheckBox] = {}
            row_flags = QHBoxLayout()
            col_count = 0
            for key in _FLAG_KEYS:
                cb = QCheckBox(_FLAG_LABELS.get(key, key))
                cb.setChecked(bool(flags.get(key, False)))
                self._flag_widgets[key] = cb
                row_flags.addWidget(cb)
                col_count += 1
                if col_count == 4:
                    flags_layout.addLayout(row_flags)
                    row_flags = QHBoxLayout()
                    col_count = 0
            if col_count > 0:
                flags_layout.addLayout(row_flags)

            # Quick presets
            preset_row = QHBoxLayout()
            preset_row.addWidget(QLabel("Presets:"))
            for label, preset_flags in [
                ("Web Service", {
                    "has_cli": True, "has_web": True,
                    "has_gui": False, "is_ollama": False,
                    "is_passive": False,
                    "is_mcp": False, "is_skills_collection": False,
                }),
                ("CLI Tool", {
                    "has_cli": True, "has_web": False,
                    "has_gui": False, "is_ollama": False,
                    "is_passive": False,
                    "is_mcp": False, "is_skills_collection": False,
                }),
                ("Passive Library", {
                    "has_cli": False, "has_web": False,
                    "has_gui": False, "is_ollama": False,
                    "is_passive": True,
                    "is_mcp": False, "is_skills_collection": False,
                }),
                ("MCP API", {
                    "has_cli": False, "has_web": False,
                    "has_gui": False, "is_ollama": False,
                    "is_passive": False,
                    "is_mcp": True, "is_skills_collection": False,
                }),
                ("Skills Pack", {
                    "has_cli": False, "has_web": False,
                    "has_gui": False, "is_ollama": False,
                    "is_passive": False,
                    "is_mcp": False, "is_skills_collection": True,
                }),
            ]:
                btn = QPushButton(label)
                btn.setMaximumWidth(120)
                btn.clicked.connect(
                    lambda _, pf=preset_flags: self._apply_flag_preset(pf)
                )
                preset_row.addWidget(btn)
            preset_row.addStretch()
            flags_layout.addLayout(preset_row)

            self.edit_layout.addWidget(grp_flags)

            # ── License ────────────────────────────────────────────
            grp_lic = QGroupBox("License")
            form_lic = QFormLayout(grp_lic)

            self.f_license = QComboBox()
            self.f_license.setEditable(True)
            self.f_license.addItems(_LICENSE_SPDX_IDS)
            idx = self.f_license.findText(
                meta.get("license", "Proprietary")
            )
            if idx >= 0:
                self.f_license.setCurrentIndex(idx)
            else:
                self.f_license.setEditText(
                    meta.get("license", "Proprietary")
                )
            form_lic.addRow("SPDX ID:", self.f_license)

            self.edit_layout.addWidget(grp_lic)

            # ── Dependencies ───────────────────────────────────────
            grp_deps = QGroupBox("Dependencies")
            deps_layout = QVBoxLayout(grp_deps)

            self.f_deps = QLineEdit(
                ", ".join(meta.get("deps", []))
            )
            self.f_deps.setPlaceholderText(
                "Comma-separated tool IDs (e.g. redis, qdrant)"
            )
            deps_layout.addWidget(self.f_deps)

            self.edit_layout.addWidget(grp_deps)

            # ── Filesystem ─────────────────────────────────────────
            fs = meta.get("filesystem", {})
            grp_fs = QGroupBox("Filesystem Paths (relative to base)")
            form_fs = QFormLayout(grp_fs)

            self._fs_fields: dict[str, QLineEdit] = {}
            for fs_key in (
                "install", "config", "cache", "data",
                "logs", "runtime", "models",
            ):
                le = QLineEdit(fs.get(fs_key, "") or "")
                le.setPlaceholderText(f"e.g. tools/{tool_id}")
                self._fs_fields[fs_key] = le
                form_fs.addRow(f"{fs_key}:", le)

            self.edit_layout.addWidget(grp_fs)

            # ── Action buttons ─────────────────────────────────────
            btn_bar = QHBoxLayout()

            self.btn_save = QPushButton("Save Changes")
            self.btn_save.setStyleSheet(
                "background-color: #27ae60; font-weight: bold;"
            )
            self.btn_save.clicked.connect(self._save_current)
            btn_bar.addWidget(self.btn_save)

            self.btn_revert = QPushButton("Revert")
            self.btn_revert.clicked.connect(
                lambda: self._load_tool(self._current_tool_id)
            )
            btn_bar.addWidget(self.btn_revert)

            self.btn_validate = QPushButton("Validate Entry")
            self.btn_validate.clicked.connect(self._validate_current)
            btn_bar.addWidget(self.btn_validate)

            btn_bar.addStretch()
            self.edit_layout.addLayout(btn_bar)

            # ── Raw JSON preview ───────────────────────────────────
            grp_raw = QGroupBox("Raw JSON Preview")
            raw_layout = QVBoxLayout(grp_raw)
            self.raw_preview = QTextEdit()
            self.raw_preview.setReadOnly(True)
            self.raw_preview.setMaximumHeight(180)
            self.raw_preview.setStyleSheet(
                "font-family: monospace; font-size: 11px;"
            )
            raw_layout.addWidget(self.raw_preview)
            self._refresh_raw_preview()
            self.edit_layout.addWidget(grp_raw)

            # Mark dirty on any edit
            for w in (
                self.f_name, self.f_description,
                self.f_inst_pkg, self.f_inst_cmd,
                self.f_inst_post, self.f_inst_update,
                self.f_launch_cmd, self.f_deps,
            ):
                if isinstance(w, QLineEdit):
                    w.textChanged.connect(self._mark_dirty)
                elif isinstance(w, QTextEdit):
                    w.textChanged.connect(self._mark_dirty)

            for w in (
                self.f_level, self.f_layer, self.f_role,
                self.f_inst_type,
                self.f_launch_type, self.f_launch_port,
                self.f_license,
            ):
                if isinstance(w, QComboBox):
                    w.currentIndexChanged.connect(self._mark_dirty)
                elif isinstance(w, QSpinBox):
                    w.valueChanged.connect(self._mark_dirty)

            for cb in self._flag_widgets.values():
                cb.stateChanged.connect(self._mark_dirty)

            for le in self._fs_fields.values():
                le.textChanged.connect(self._mark_dirty)

            self.edit_layout.addStretch()
            self._loading = False

        # ── Category cascade ──────────────────────────────────────────

        def _on_category_changed(self, category: str) -> None:
            """Auto-fill Level, Layer, and Role when Category changes."""
            if self._loading:
                return
            mapping = CATEGORY_MAP.get(category)
            if mapping is None:
                return
            self._loading = True
            self.f_level.setValue(mapping["level"])
            _set_combo_text(self.f_layer, mapping["layer"])
            _set_combo_text(self.f_role, mapping["role"])
            self._loading = False
            self._mark_dirty()

        # ── Flag presets ──────────────────────────────────────────────

        def _apply_flag_preset(
            self, preset: dict[str, bool]
        ) -> None:
            for key, val in preset.items():
                cb = self._flag_widgets.get(key)
                if cb:
                    cb.setChecked(val)
            self._mark_dirty()

        # ── Dirty tracking ────────────────────────────────────────────

        def _mark_dirty(self) -> None:
            if self._loading:
                return
            self._dirty = True
            self.btn_save.setStyleSheet(
                "background-color: #e67e22; font-weight: bold;"
            )
            self._refresh_raw_preview()

        def _refresh_raw_preview(self) -> None:
            if not self._current_tool_id:
                return
            data = self._collect_form_data()
            import json
            self.raw_preview.setPlainText(
                json.dumps(data, indent=2, ensure_ascii=False)
            )

        # ── Collect form data back into a dict ────────────────────────

        def _collect_form_data(self) -> dict:
            port_val = self.f_launch_port.value()
            deps_text = self.f_deps.text().strip()
            deps_list = [
                d.strip()
                for d in deps_text.split(",")
                if d.strip()
            ]

            flags = {}
            for key, cb in self._flag_widgets.items():
                flags[key] = cb.isChecked()

            fs = {}
            for key, le in self._fs_fields.items():
                val = le.text().strip()
                fs[key] = val

            return {
                "name": self.f_name.text().strip(),
                "level": self.f_level.value(),
                "layer": self.f_layer.currentText(),
                "role": self.f_role.currentText(),
                "category": self.f_category.currentText(),
                "description": self.f_description.toPlainText().strip(),
                "license": self.f_license.currentText().strip(),
                "installer": {
                    "type": self.f_inst_type.currentText(),
                    "pkg": self.f_inst_pkg.text().strip(),
                    "cmd": self.f_inst_cmd.text().strip() or None,
                    "post_install": (
                        self.f_inst_post.text().strip() or None
                    ),
                    "update_cmd": (
                        self.f_inst_update.text().strip() or None
                    ),
                },
                "launcher": {
                    "type": self.f_launch_type.currentText(),
                    "cmd": self.f_launch_cmd.text().strip(),
                    "default_port": port_val if port_val > 0 else None,
                },
                "deps": deps_list,
                "flags": flags,
                "filesystem": fs,
            }

        # ── Save / Revert / Validate ──────────────────────────────────

        def _save_current(self) -> None:
            if not self._current_tool_id:
                return

            data = self._collect_form_data()
            tool_id = self._current_tool_id

            # Validate before writing
            from ai_lsc.registry.validator import validate_registry
            test_registry = dict(self.main.registry_mgr.data)
            test_registry[tool_id] = data
            errors = validate_registry(test_registry)
            tool_errors = [
                e for e in errors
                if e.startswith(f"{tool_id}:")
            ]
            if tool_errors:
                self._show_status(
                    "error",
                    f"Validation failed for {tool_id}:<br>"
                    + "<br>".join(
                        f"&bull; {e}" for e in tool_errors
                    ),
                )
                return

            # Write via atomic write
            self.main.registry_mgr.data[tool_id] = data
            registry_path = (
                self.main.registry_mgr.registry_file
            )
            from ai_lsc.ui.main_window import _atomic_write_json
            _atomic_write_json(registry_path, self.main.registry_mgr.data)
            self._dirty = False
            self.btn_save.setStyleSheet(
                "background-color: #27ae60; font-weight: bold;"
            )
            self._show_status(
                "ok",
                f"<b>{tool_id}</b> saved successfully.",
            )
            self._populate_table()
            self._reselect_tool(tool_id)

        def _save_current_if_dirty(self) -> None:
            if self._dirty and self._current_tool_id:
                reply = QMessageBox.question(
                    self,
                    "Unsaved changes",
                    f"Save changes to <b>{self._current_tool_id}</b> "
                    f"before switching?",
                    QMessageBox.Save | QMessageBox.Discard,
                    QMessageBox.Save,
                )
                if reply == QMessageBox.Save:
                    self._save_current()

        def _validate_current(self) -> None:
            if not self._current_tool_id:
                return
            data = self._collect_form_data()
            tool_id = self._current_tool_id
            from ai_lsc.registry.validator import validate_registry
            test_registry = dict(self.main.registry_mgr.data)
            test_registry[tool_id] = data
            errors = validate_registry(test_registry)
            tool_errors = [
                e for e in errors
                if e.startswith(f"{tool_id}:")
            ]
            other_count = len(errors) - len(tool_errors)
            if not tool_errors:
                self._show_status(
                    "ok",
                    f"<b>{tool_id}</b> — no validation errors."
                    + (
                        f"  ({other_count} warning(s) in other tools)"
                        if other_count
                        else ""
                    ),
                )
            else:
                self._show_status(
                    "error",
                    f"<b>{tool_id}</b> — {len(tool_errors)} error(s):"
                    "<br>"
                    + "<br>".join(
                        f"&bull; {e}" for e in tool_errors
                    ),
                )

        def _validate_all(self) -> None:
            # Re-read from disk in case user edited outside
            self.main.registry_mgr._bootstrap()
            from ai_lsc.registry.validator import validate_registry
            errors = validate_registry(self.main.registry_mgr.data)
            total_tools = len(self.main.registry_mgr.data)
            if not errors:
                self._show_status(
                    "ok",
                    f"All {total_tools} tools pass validation.",
                )
            else:
                self._show_status(
                    "error",
                    f"<b>{len(errors)} error(s)</b> across "
                    f"{total_tools} tools:<br>"
                    + "<br>".join(
                        f"&bull; {e}" for e in errors[:30]
                    )
                    + (
                        f"<br>... and {len(errors) - 30} more"
                        if len(errors) > 30
                        else ""
                    ),
                )

        # ── Add / Delete tool ─────────────────────────────────────────

        def _add_tool(self) -> None:
            new_id, ok = _NewToolDialog.get_tool_id(self)
            if not ok or not new_id:
                return
            registry = self.main.registry_mgr.data
            if new_id in registry:
                self._show_status(
                    "error",
                    f"<b>{new_id}</b> already exists in the registry.",
                )
                return

            # Template with sensible defaults
            registry[new_id] = {
                "name": new_id.replace("_", " ").title(),
                "level": 1,
                "layer": _LAYER_ORDER[0] if _LAYER_ORDER else "",
                "role": "",
                "category": "",
                "description": "",
                "license": "Proprietary",
                "installer": {
                    "type": "pacman",
                    "pkg": new_id,
                },
                "launcher": {
                    "type": "desktop",
                    "cmd": new_id,
                    "default_port": None,
                },
                "deps": [],
                "flags": {
                    k: False for k in _FLAG_KEYS
                },
                "filesystem": {},
            }
            from ai_lsc.ui.main_window import _atomic_write_json
            _atomic_write_json(
                self.main.registry_mgr.registry_file, registry
            )
            self._populate_table()
            self._reselect_tool(new_id)
            self._show_status(
                "ok",
                f"<b>{new_id}</b> added with defaults. "
                f"Edit and save to finalise.",
            )

        def _delete_tool(self) -> None:
            if not self._current_tool_id:
                return
            tool_id = self._current_tool_id
            reply = QMessageBox.warning(
                self,
                "Delete tool?",
                f"Permanently remove <b>{tool_id}</b> from the "
                f"registry?  This cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

            self.main.registry_mgr.data.pop(tool_id, None)
            from ai_lsc.ui.main_window import _atomic_write_json
            _atomic_write_json(
                self.main.registry_mgr.registry_file,
                self.main.registry_mgr.data,
            )
            self._current_tool_id = None
            self._dirty = False
            self._clear_edit_form()
            self.edit_layout.addWidget(QLabel(
                "<i>Tool deleted. Select another to edit.</i>"
            ))
            self._populate_table()
            self._show_status(
                "ok",
                f"<b>{tool_id}</b> removed from registry.",
            )

        # ── Helpers ──────────────────────────────────────────────────

        def _reselect_tool(self, tool_id: str) -> None:
            """Re-select the given tool_id in the table after refresh."""
            for row in range(self.tool_table.rowCount()):
                item = self.tool_table.item(row, 0)
                if item and item.data(Qt.UserRole) == tool_id:
                    self.tool_table.selectRow(row)
                    self.tool_table.scrollTo(
                        self.tool_table.model().index(row, 0)
                    )
                    return

        def _show_status(
            self, level: str, html: str
        ) -> None:
            colors = {
                "ok": ("#27ae60", "#1a3a2a"),
                "error": ("#e74c3c", "#3a1a1a"),
                "info": ("#3498db", "#1a2a3a"),
            }
            fg, bg = colors.get(level, ("#bdc3c7", "#1a1a1a"))
            self.status_label.setStyleSheet(
                f"padding: 6px 10px; border-radius: 4px; "
                f"color: {fg}; background-color: {bg};"
            )
            self.status_label.setText(html)

        def refresh(self) -> None:
            """Called by the main window when the nav tab is activated."""
            _populate_lookups(
                self.main.registry_mgr.get_all_tools()
            )
            self._populate_table()


    # ── Dialogs ────────────────────────────────────────────────────────

    class _NewToolDialog(QDialog):
        """Modal dialog that asks the user for a new tool_id."""

        @staticmethod
        def get_tool_id(parent: QWidget) -> tuple[str, bool]:
            dlg = _NewToolDialog(parent)
            result = dlg.exec()
            return dlg.input_field.text().strip(), (
                result == QDialog.DialogCode.Accepted
            )

        def __init__(self, parent: QWidget) -> None:
            super().__init__(parent)
            self.setWindowTitle("Add New Tool")
            self.setMinimumWidth(400)
            layout = QVBoxLayout(self)

            layout.addWidget(QLabel(
                "Enter the new tool identifier (lowercase, "
                "alphanumeric + underscores):"
            ))
            self.input_field = QLineEdit()
            self.input_field.setPlaceholderText("e.g. my_new_tool")
            layout.addWidget(self.input_field)

            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(self._validate_and_accept)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)

        def _validate_and_accept(self) -> None:
            import re
            text = self.input_field.text().strip()
            if not text:
                self.input_field.setStyleSheet(
                    "border: 2px solid #e74c3c;"
                )
                return
            if not re.match(r"^[a-z0-9_]+$", text):
                self.input_field.setStyleSheet(
                    "border: 2px solid #e74c3c;"
                )
                return
            self.accept()


else:
    DatabaseManager = None