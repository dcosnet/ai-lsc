"""InfrastructureLayerPage widget -- inline tool selection for a single
infrastructure layer.

Every layer in the sidebar IS the wizard: a single static list of all
registry tools for that layer.  Clicking a tool row toggles it active/
inactive.  Active rows shift right (indent) and get a tinted background.
The list never changes structure -- only the visual status of each row.

Tool list is always built from the live upstream registry (per-layer
files) via ``load_merged_registry()``, never from the on-disk
``ecosystem.json`` cache, which can grow stale across sessions.
"""

import json
import os
from collections import OrderedDict

from ai_lsc.constants import STATE_FILE_NAME
from ai_lsc.registry.loader import load_merged_registry
from ai_lsc.ui.main_window import _atomic_write_json

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QFont, QCursor
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QScrollArea,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

# Module-level cache of the upstream registry, refreshed once per
# app start.  Individual pages index into this by layer name.
_UPSTREAM_REGISTRY: dict[str, dict] = {}


def _ensure_upstream() -> dict[str, dict]:
    """Load the upstream registry from per-layer files (cached)."""
    if not _UPSTREAM_REGISTRY:
        _UPSTREAM_REGISTRY.update(load_merged_registry())
    return _UPSTREAM_REGISTRY


def _group_by_layer(
    registry: dict[str, dict],
) -> dict[str, list[tuple[str, dict]]]:
    """Group upstream registry entries by their ``layer`` field."""
    groups: dict[str, list[tuple[str, dict]]] = {}
    for t_id, meta in registry.items():
        layer = meta.get("layer", "Uncategorized")
        groups.setdefault(layer, []).append((t_id, meta))
    # Sort each group by category then name for stable ordering
    for tools in groups.values():
        tools.sort(key=lambda t: (
            t[1].get("category", ""),
            t[1].get("name", t[0]).lower(),
        ))
    return groups


if _HAS_QT:

    # ── Row styles ──────────────────────────────────────────────────
    _ROW_INACTIVE = (
        "background-color: transparent;"
        "border: 1px solid transparent;"
        "border-radius: 4px;"
        "padding: 5px 8px 5px 12px;"
        "margin: 1px 0px;"
    )
    _ROW_ACTIVE = (
        "background-color: rgba(46, 204, 113, 0.13);"
        "border-left: 3px solid rgba(46, 204, 113, 0.7);"
        "border-top: 1px solid rgba(46, 204, 113, 0.2);"
        "border-right: 1px solid rgba(46, 204, 113, 0.2);"
        "border-bottom: 1px solid rgba(46, 204, 113, 0.2);"
        "border-radius: 4px;"
        "padding: 5px 8px 5px 20px;"
        "margin: 1px 0px 1px 8px;"
    )
    _ROW_HOVER = (
        "background-color: rgba(52, 152, 219, 0.08);"
        "border: 1px solid rgba(52, 152, 219, 0.15);"
        "border-radius: 4px;"
        "padding: 5px 8px 5px 12px;"
        "margin: 1px 0px;"
    )
    _ACTIVE_DOT = (
        "<span style='color:#2ecc71; font-size:8px;'>&#9679;</span>"
    )

    class _ToolRow(QWidget):
        """A single clickable tool row.  Tracks its own active state."""

        def __init__(self, tool_id: str, parent_page: "InfrastructureLayerPage"):
            super().__init__()
            self.tool_id = tool_id
            self._page = parent_page
            self._active = False
            self._hover = False

            row = QHBoxLayout(self)
            row.setContentsMargins(10, 6, 8, 6)
            row.setSpacing(6)

            # Active indicator dot (hidden until active)
            self.dot = QLabel("")
            self.dot.setFixedWidth(12)
            row.addWidget(self.dot)

            # Tool name
            self.name_lbl = QLabel()
            self.name_lbl.setTextFormat(Qt.TextFormat.RichText)
            row.addWidget(self.name_lbl)

            # Category tag
            self.cat_lbl = QLabel()
            self.cat_lbl.setTextFormat(Qt.TextFormat.RichText)
            row.addWidget(self.cat_lbl)

            row.addStretch()

            # Badges
            self.badge_lbl = QLabel()
            self.badge_lbl.setTextFormat(Qt.TextFormat.RichText)
            row.addWidget(self.badge_lbl)

            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        def set_active(self, active: bool) -> None:
            self._active = active
            if active:
                self.setStyleSheet(_ROW_ACTIVE)
                self.dot.setText(_ACTIVE_DOT)
            else:
                self.setStyleSheet(_ROW_INACTIVE)
                self.dot.setText("")

        def enterEvent(self, event):
            if not self._active:
                self.setStyleSheet(_ROW_HOVER)
            self._hover = True
            super().enterEvent(event)

        def leaveEvent(self, event):
            self._hover = False
            self.setStyleSheet(_ROW_ACTIVE if self._active else _ROW_INACTIVE)
            super().leaveEvent(event)

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._active = not self._active
                self.set_active(self._active)
                self._page._on_row_toggled(self.tool_id, self._active)
            super().mousePressEvent(event)

    class InfrastructureLayerPage(QWidget):
        """Single-list tool selector with indent + background-color state.

        Every tool for this layer appears exactly once in a flat scrollable
        list.  Clicking a row toggles it active/inactive.  Active rows get
        an 8px left indent plus a green tinted background with a left accent
        bar and green dot.  No checkboxes, no separate active/available
        areas -- one list, one click to toggle.

        Tool data is always sourced from the live upstream registry
        (per-layer Python files), never from the on-disk ecosystem.json
        cache which can grow stale between sessions.
        """

        def __init__(self, main_window, layer_name: str):
            super().__init__()
            self.main = main_window
            self.layer_name = layer_name
            self.rows: dict[str, _ToolRow] = {}
            self._debounce_timer = QTimer(self)
            self._debounce_timer.setSingleShot(True)
            self._debounce_timer.setInterval(400)
            self._debounce_timer.timeout.connect(self._compile_from_rows)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 8, 12, 8)
            layout.setSpacing(0)

            # ── Header ──────────────────────────────────────────────
            hdr = QHBoxLayout()
            lbl = QLabel(f"<b>{layer_name}</b>")
            lbl.setFont(QFont("Segoe UI", 14))
            hdr.addWidget(lbl)

            self.lbl_count = QLabel("")
            self.lbl_count.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            hdr.addWidget(self.lbl_count)
            hdr.addStretch()

            btn_select_all = QLabel(
                "<a href='#select_all' style='color: #3498db; "
                "text-decoration: none;'>Select All</a>"
            )
            btn_select_all.linkActivated.connect(self._select_all)
            hdr.addWidget(btn_select_all)

            btn_clear = QLabel(
                "<a href='#clear_all' style='color: #e74c3c; "
                "text-decoration: none;'>Clear</a>"
            )
            btn_clear.linkActivated.connect(self._clear_all)
            hdr.addWidget(btn_clear)

            layout.addLayout(hdr)
            layout.addSpacing(4)

            # ── Scrollable tool list ────────────────────────────────
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )
            scroll.setStyleSheet(
                "QScrollArea { border: none; background: transparent; }"
            )

            self.scroll_content = QWidget()
            self.scroll_content.setStyleSheet("background: transparent;")
            self.list_layout = QVBoxLayout(self.scroll_content)
            self.list_layout.setContentsMargins(4, 0, 4, 0)
            self.list_layout.setSpacing(0)

            scroll.setWidget(self.scroll_content)
            layout.addWidget(scroll)

            # Build rows from the live upstream registry
            self._build_rows()

        # ── Row construction ────────────────────────────────────────

        def _build_rows(self) -> None:
            """Clear existing rows and rebuild from upstream registry."""
            # Remove old rows
            for tid in list(self.rows):
                w = self.rows.pop(tid)
                w.setParent(None)
                w.deleteLater()

            # Source from live upstream (per-layer files), not ecosystem.json
            upstream = _ensure_upstream()
            grouped = _group_by_layer(upstream)
            layer_tools = grouped.get(self.layer_name, [])
            active_ids = self._load_active_ids()

            for t_id, meta in layer_tools:
                flags = meta.get("flags", {})
                category = meta.get("category", "")
                name = meta.get("name", t_id)
                is_active = t_id in active_ids

                row = _ToolRow(t_id, self)
                row.name_lbl.setText(
                    f"<span style='font-size:12px; color:#ddd;'>{name}</span>"
                )
                row.cat_lbl.setText(
                    f"<span style='color:#777;font-size:10px;'>"
                    f"({category})</span>"
                )

                # Build badge string
                badge_parts = []
                if flags.get("has_cli"):
                    badge_parts.append(
                        "<span style='color:#3498db;font-family:monospace;"
                        "font-size:10px;'>&gt;_</span>"
                    )
                if flags.get("has_gui"):
                    badge_parts.append(
                        "<span style='color:#9b59b6;font-family:monospace;"
                        "font-size:10px;'>[GUI]</span>"
                    )
                if flags.get("has_web"):
                    badge_parts.append(
                        "<span style='color:#2ecc71;font-family:monospace;"
                        "font-size:10px;'>WEB</span>"
                    )
                if flags.get("is_ollama"):
                    badge_parts.append(
                        "<span style='color:#e67e22;font-family:monospace;"
                        "font-size:10px;'>OLLAMA</span>"
                    )
                if flags.get("is_passive"):
                    badge_parts.append(
                        "<span style='color:#7f8c8d;font-family:monospace;"
                        "font-size:10px;'>LIB</span>"
                    )
                if flags.get("is_mcp"):
                    badge_parts.append(
                        "<span style='color:#e67e22;font-family:monospace;"
                        "font-size:10px;'>MCP</span>"
                    )
                if flags.get("is_skills_collection"):
                    badge_parts.append(
                        "<span style='color:#8e44ad;font-family:monospace;"
                        "font-size:10px;'>SKILLS</span>"
                    )
                row.badge_lbl.setText("  ".join(badge_parts))
                row.setToolTip(meta.get("description", ""))

                row.set_active(is_active)
                self.rows[t_id] = row
                self.list_layout.addWidget(row)

            self.list_layout.addStretch()
            self._update_count_label()

        # ── State helpers ──────────────────────────────────────────

        def _load_active_ids(self) -> set[str]:
            """Load active_tools from pipeline_state.json."""
            state_file = os.path.join(
                self.main.config_root, STATE_FILE_NAME
            )
            if not os.path.exists(state_file):
                return set()
            try:
                with open(state_file, encoding="utf-8") as f:
                    return set(
                        json.load(f).get("active_tools", [])
                    )
            except (OSError, ValueError, json.JSONDecodeError):
                return set()

        def _gather_all_selected(self) -> list[str]:
            """Collect active tool IDs from ALL infrastructure layer pages."""
            selected = []
            nav = self.main.nav_stack
            for i in range(nav.count()):
                page = nav.widget(i)
                if isinstance(page, InfrastructureLayerPage):
                    for tid, row in page.rows.items():
                        if row._active:
                            selected.append(tid)
            return selected

        def _on_row_toggled(self, t_id: str, active: bool) -> None:
            """Row was clicked; debounce the compile."""
            self._debounce_timer.start()
            self._update_count_label()

        def _compile_from_rows(self) -> None:
            """Gather all active tools across every layer, resolve deps,
            and write the pipeline state file."""
            selected = self._gather_all_selected()

            # Dependency resolution
            missing = self.main.registry_mgr.check_dependencies(selected)
            if missing:
                selected.extend(missing)
                nav = self.main.nav_stack
                for i in range(nav.count()):
                    page = nav.widget(i)
                    if isinstance(page, InfrastructureLayerPage):
                        for tid in missing:
                            if tid in page.rows:
                                page.rows[tid].set_active(True)

            # Build port map from upstream registry (authoritative)
            upstream = _ensure_upstream()
            port_map = {}
            for tid in selected:
                if tid.startswith("skill:"):
                    continue
                meta = upstream.get(tid, {})
                default_port = meta.get("launcher", {}).get("default_port")
                if default_port:
                    port_map[tid] = default_port

            state = {
                "session_name": "ai_lsc",
                "base_dir": self.main.base_dir,
                "active_tools": selected,
                "port_map": port_map,
                "stack_ready": True,
                "source": "inline_wizard",
            }
            os.makedirs(self.main.config_root, exist_ok=True)
            state_file = os.path.join(
                self.main.config_root, STATE_FILE_NAME
            )
            _atomic_write_json(state_file, state)

            self.main.log(
                f"Stack state recompiled: {len(selected)} tools active "
                f"(from {self.layer_name}).",
                "StackCompiler",
            )

            # Refresh the rest of the UI
            self.main._populate_services()
            self.main._refresh_pipeline_ticker()
            self.main._refresh_workspace_tab()
            self.main.refresh_models()

            # Sync row states on all sibling layer pages
            nav = self.main.nav_stack
            for i in range(nav.count()):
                page = nav.widget(i)
                if isinstance(page, InfrastructureLayerPage) and page is not self:
                    page._sync_row_states()

            self._update_count_label()

        def _sync_row_states(self) -> None:
            """Re-read active set and update all row visuals to match."""
            active_ids = self._load_active_ids()
            for t_id, row in self.rows.items():
                is_active = t_id in active_ids
                row.set_active(is_active)
            self._update_count_label()

        def refresh_active_services(self) -> None:
            """No-op: active state is shown via row background color."""
            self._sync_row_states()

        def _update_count_label(self) -> None:
            total = len(self.rows)
            active = sum(1 for r in self.rows.values() if r._active)
            self.lbl_count.setText(f"{active}/{total} active")

        def _select_all(self) -> None:
            for row in self.rows.values():
                row.set_active(True)
            self._debounce_timer.start()

        def _clear_all(self) -> None:
            for row in self.rows.values():
                row.set_active(False)
            self._debounce_timer.start()

        def highlight_tool(self, tool_id: str) -> None:
            """Focus and flash a specific tool row (from ticker click)."""
            row = self.rows.get(tool_id)
            if row:
                row.setFocus()
                # Brief visual flash
                row.setStyleSheet(_ROW_HOVER)
                QTimer.singleShot(600, lambda: row.setStyleSheet(
                    _ROW_ACTIVE if row._active else _ROW_INACTIVE
                ))

else:
    InfrastructureLayerPage = None