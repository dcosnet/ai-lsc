"""ToolsTab widget — read-only tree view of the full tool registry.

Displays every registered tool grouped by its infrastructure layer,
showing tool name, level, layer, role, category, and an "interface"
column that surfaces — at a glance — whether each tool exposes a
**CLI**, a **GUI**, a **Web UI**, is **passive** (library / skills
collection / MCP API), or any combination of those.

The interface column uses coloured badge glyphs so the user can scan a
layer quickly and see what kind of thing each entry is.
"""

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QBrush
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

# ── Interface badge taxonomy ─────────────────────────────────────────────
# Glyph → meaning.  Order matters: the rightmost matching glyph wins for
# the "primary kind" used in the summary column.
_BADGE_CLI = ">_"        # CLI
_BADGE_GUI = "[ ]"       # GUI window
_BADGE_WEB = "www"       # Web UI on a port
_BADGE_PASSIVE = "lib"   # passive library / collection
_BADGE_MCP = "mcp"       # MCP API tool
_BADGE_SKILLS = "ski"    # skills collection

# Per-badge colours (foreground) for the interface column.
_BADGE_COLORS = {
    _BADGE_CLI: "#3498db",      # blue
    _BADGE_GUI: "#9b59b6",      # purple
    _BADGE_WEB: "#2ecc71",      # green
    _BADGE_PASSIVE: "#7f8c8d",  # grey
    _BADGE_MCP: "#e67e22",      # orange
    _BADGE_SKILLS: "#f1c40f",   # yellow
}


def _interface_badges(flags: dict) -> list[str]:
    """Build the ordered badge list for a tool's flag dict.

    Order: CLI → GUI → Web → Passive → MCP → Skills.
    Passive-family badges (passive/mcp/skills) suppress the active-surface
    badges in the *compact* summary view, since the user explicitly cares
    about distinguishing passive tools from runnable ones.
    """
    badges: list[str] = []
    if flags.get("has_cli"):
        badges.append(_BADGE_CLI)
    if flags.get("has_gui"):
        badges.append(_BADGE_GUI)
    if flags.get("has_web"):
        badges.append(_BADGE_WEB)
    if flags.get("is_passive"):
        badges.append(_BADGE_PASSIVE)
    if flags.get("is_mcp"):
        badges.append(_BADGE_MCP)
    if flags.get("is_skills_collection"):
        badges.append(_BADGE_SKILLS)
    return badges


def _interface_summary(flags: dict) -> str:
    """One-line human-readable interface summary.

    Examples::

        'CLI + Web UI'                       # Open WebUI style
        'GUI'                                # Obsidian
        'Passive (library)'                  # langchain
        'Passive (skills collection)'        # nvidia_agent_skills
        'Passive (MCP API)'                  # an MCP-only tool
        '—'                                  # no interface declared
    """
    if flags.get("is_skills_collection"):
        return "Passive (skills collection)"
    if flags.get("is_mcp"):
        return "Passive (MCP API)"
    if flags.get("is_passive"):
        return "Passive (library)"

    surfaces: list[str] = []
    if flags.get("has_cli"):
        surfaces.append("CLI")
    if flags.get("has_gui"):
        surfaces.append("GUI")
    if flags.get("has_web"):
        surfaces.append("Web UI")
    return " + ".join(surfaces) if surfaces else "—"


def _badge_brush(glyph: str) -> "QBrush":
    return QBrush(QColor(_BADGE_COLORS.get(glyph, "#bdc3c7")))


if _HAS_QT:

    class ToolsTab(QWidget):
        """Read-only tree view of the full tool registry, grouped by layer.

        Columns:
          0. Tool name
          1. Level (L1..L13)
          2. Layer
          3. Role
          4. Category
          5. Interface  — coloured badges for CLI / GUI / Web / passive / MCP / skills
          6. Launcher  — systemd / tmux / desktop (how the tool runs)

        A summary header at the top shows the live counts per interface
        type so the user can see at a glance what the registry contains.
        """

        def __init__(self, main_window):
            super().__init__()
            self.main = main_window
            layout = QVBoxLayout(self)

            # Header — populated in refresh() with live counts
            self.header_label = QLabel(
                "<b>Registry Tool Surface (10-Layer Architecture)</b>"
            )
            self.header_label.setWordWrap(True)
            layout.addWidget(self.header_label)

            # Legend row
            legend = QHBoxLayout()
            legend.setSpacing(12)
            for glyph, meaning in [
                (_BADGE_CLI, "CLI"),
                (_BADGE_GUI, "GUI"),
                (_BADGE_WEB, "Web UI"),
                (_BADGE_PASSIVE, "Passive (library)"),
                (_BADGE_MCP, "MCP API"),
                (_BADGE_SKILLS, "Skills collection"),
            ]:
                chip = QLabel(
                    f"<span style='color:{_BADGE_COLORS[glyph]}; "
                    f"font-family: monospace; font-weight: bold;'>"
                    f"{glyph}</span> = {meaning}"
                )
                legend.addWidget(chip)
            legend.addStretch()
            legend_widget = QWidget()
            legend_widget.setLayout(legend)
            layout.addWidget(legend_widget)

            self.tree = QTreeWidget()
            self.tree.setColumnCount(7)
            self.tree.setHeaderLabels([
                "Tool", "Level", "Layer", "Role",
                "Category", "Interface", "Launcher",
            ])
            # Stretch the Tool and Category columns; keep the rest tight.
            self.tree.setColumnWidth(0, 220)
            self.tree.setColumnWidth(1, 50)
            self.tree.setColumnWidth(2, 160)
            self.tree.setColumnWidth(3, 160)
            self.tree.setColumnWidth(4, 160)
            self.tree.setColumnWidth(5, 180)
            self.tree.setColumnWidth(6, 80)
            layout.addWidget(self.tree)

        def refresh(self):
            self.tree.clear()
            grouped = self.main.registry_mgr.get_grouped_by_layer()

            # Aggregate counts for the summary header
            cli_n = gui_n = web_n = passive_n = mcp_n = skills_n = 0
            total = 0
            for _layer, tools in grouped.items():
                for _t_id, meta in tools:
                    total += 1
                    f = meta.get("flags", {})
                    if f.get("has_cli"):
                        cli_n += 1
                    if f.get("has_gui"):
                        gui_n += 1
                    if f.get("has_web"):
                        web_n += 1
                    if f.get("is_passive"):
                        passive_n += 1
                    if f.get("is_mcp"):
                        mcp_n += 1
                    if f.get("is_skills_collection"):
                        skills_n += 1

            self.header_label.setText(
                f"<b>Registry Tool Surface (10-Layer Architecture)</b> "
                f"— {total} tools | "
                f"<span style='color:{_BADGE_COLORS[_BADGE_CLI]}'>CLI {cli_n}</span> · "
                f"<span style='color:{_BADGE_COLORS[_BADGE_GUI]}'>GUI {gui_n}</span> · "
                f"<span style='color:{_BADGE_COLORS[_BADGE_WEB]}'>Web {web_n}</span> · "
                f"<span style='color:{_BADGE_COLORS[_BADGE_PASSIVE]}'>Passive {passive_n}</span> · "
                f"<span style='color:{_BADGE_COLORS[_BADGE_MCP]}'>MCP {mcp_n}</span> · "
                f"<span style='color:{_BADGE_COLORS[_BADGE_SKILLS]}'>Skills {skills_n}</span>"
            )

            for layer, tools in grouped.items():
                # Layer-level row: show count + breakdown of interface
                # types inside the layer.
                layer_cli = sum(
                    1 for _tid, m in tools if m.get("flags", {}).get("has_cli")
                )
                layer_web = sum(
                    1 for _tid, m in tools if m.get("flags", {}).get("has_web")
                )
                layer_passive = sum(
                    1 for _tid, m in tools if m.get("flags", {}).get("is_passive")
                )
                layer_item = QTreeWidgetItem([
                    f"{layer}  ({len(tools)} tools)",
                    "",
                    layer,
                    "",
                    "",
                    f"cli:{layer_cli}  web:{layer_web}  passive:{layer_passive}",
                    "",
                ])
                # Layer row styling: bold, slightly lighter background
                font = layer_item.font(0)
                font.setBold(True)
                for col in range(7):
                    layer_item.setFont(col, font)
                    layer_item.setForeground(
                        col, QBrush(QColor("#a5d6a7"))
                    )
                self.tree.addTopLevelItem(layer_item)

                for t_id, meta in tools:
                    lvl = f"L{meta.get('level', 0)}"
                    flags = meta.get("flags", {})
                    iface_summary = _interface_summary(flags)
                    launcher_type = (
                        meta.get("launcher", {}).get("type", "")
                        or "—"
                    )

                    item = QTreeWidgetItem([
                        meta.get("name", t_id),
                        lvl,
                        meta.get("layer", ""),
                        meta.get("role", ""),
                        meta.get("category", ""),
                        iface_summary,
                        launcher_type,
                    ])
                    item.setData(0, Qt.UserRole, t_id)

                    # Colour the Interface cell by primary badge so the
                    # user can scan visually.  Passive-family colours
                    # take precedence over active-surface colours.
                    if flags.get("is_skills_collection"):
                        primary = _BADGE_SKILLS
                    elif flags.get("is_mcp"):
                        primary = _BADGE_MCP
                    elif flags.get("is_passive"):
                        primary = _BADGE_PASSIVE
                    elif flags.get("has_web"):
                        primary = _BADGE_WEB
                    elif flags.get("has_gui"):
                        primary = _BADGE_GUI
                    elif flags.get("has_cli"):
                        primary = _BADGE_CLI
                    else:
                        primary = None

                    if primary:
                        item.setForeground(5, _badge_brush(primary))

                    # Dim passive tools slightly so active services pop
                    if flags.get("is_passive"):
                        for col in (0, 1, 2, 3, 4, 6):
                            item.setForeground(
                                col, QBrush(QColor("#7f8c8d"))
                            )

                    layer_item.addChild(item)
            self.tree.expandAll()

        def highlight_tool(self, tool_id: str) -> bool:
            """Find the row for *tool_id*, select it, scroll to it,
            and return True.  Returns False if the tool_id is not in
            the registry.

            Called by the PipelineTicker when the user clicks a tool
            name in the scrolling status bar.
            """
            matches = self.tree.findItems(
                tool_id, Qt.MatchExactly | Qt.MatchRecursive, 0,
            )
            # findItems matches the visible column 0 (tool name), not
            # the UserRole tool_id — so fall back to a manual scan.
            target_item = None
            if matches:
                target_item = matches[0]
            else:
                iterator = iter(self.tree)
                for item in self.tree:
                    if item.data(0, Qt.UserRole) == tool_id:
                        target_item = item
                        break
            if target_item is None:
                return False
            self.tree.setCurrentItem(target_item)
            self.tree.scrollToItem(
                target_item, self.tree.PositionAtCenter,
            )
            # Flash a highlight on the row briefly so the user notices it
            from PySide6.QtGui import QBrush, QColor
            from PySide6.QtCore import QTimer
            original_bg = target_item.background(0)
            target_item.setBackground(0, QBrush(QColor("#fef3c7")))  # amber-100
            def _restore():
                target_item.setBackground(0, original_bg)
            QTimer.singleShot(1500, _restore)
            return True

else:
    ToolsTab = None
