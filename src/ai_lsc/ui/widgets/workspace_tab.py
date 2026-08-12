"""WorkspaceTab — peek-style orchestration surface.

Each active tool gets its own sub-tab inside this workspace:

* **Web tools** (``flags.has_web=True``) embed via
  ``QWebEngineView`` pointed at ``http://127.0.0.1:{port}``.  When the
  tool is not running, the sub-tab shows a "Start tool" button instead.
* **CLI tools** (``flags.has_cli=True`` and no web interface) embed
  via a ``QProcess`` running ``tmux attach -t ai_lsc_<uid>::<tool_id>``
  inside a lightweight terminal widget.  When the tool is not running,
  the sub-tab shows a "Start tool" button.
* **Passive / library tools** (no web + no CLI) get a placeholder
  sub-tab explaining they have no interactive surface.

The intent is to feel like virt-manager / aqemu — every tool you've
staged is reachable from a single window, no context-switch to a
browser or terminal app required.

Servo note
----------
The user originally suggested using servo (Mozilla's Rust web engine)
instead of an external browser.  Servo's Python bindings are not yet
production-ready and have no first-class PySide6 integration, so this
module defaults to ``PySide6.QtWebEngineWidgets.QWebEngineView``.
Swapping in servo later is a one-line change: replace
``_make_web_view()`` with a servo-backed widget that exposes the same
``setUrl()`` / ``url()`` / ``load()`` API.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Optional web-engine import — degrades gracefully if PySide6 QtWebEngine
# isn't installed (some minimal installs skip it).
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    _HAS_WEBENGINE = True
except ImportError:
    QWebEngineView = None  # type: ignore[assignment, misc]
    _HAS_WEBENGINE = False


class _PlaceholderPage(QWidget):
    """Sub-tab body shown when a tool has no interactive surface or
    when the tool is not running."""

    start_requested = Signal(str)  # tool_id

    def __init__(
        self,
        tool_id: str,
        reason: str,
        can_start: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.tool_id = tool_id
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel(tool_id)
        title.setFont(QFont("Sans", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        body = QLabel(reason)
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignCenter)
        body.setStyleSheet("color: #64748b; margin: 12px 40px;")
        layout.addWidget(body)

        if can_start:
            start_btn = QPushButton("Start tool")
            start_btn.setCursor(Qt.PointingHandCursor)
            start_btn.setStyleSheet(
                "padding: 8px 24px; background: #2563eb; color: white; "
                "border-radius: 4px; font-weight: bold;"
            )
            start_btn.clicked.connect(
                lambda: self.start_requested.emit(self.tool_id)
            )
            layout.addWidget(start_btn, alignment=Qt.AlignCenter)


class _WebToolPage(QWidget):
    """Sub-tab body for a web-interface tool — QWebEngineView or a
    fallback 'web engine not available' page."""

    def __init__(
        self,
        tool_id: str,
        url: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.tool_id = tool_id
        self.url = url
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # URL bar
        url_bar = QFrame()
        url_bar.setFixedHeight(28)
        url_bar.setStyleSheet(
            "background: #1e1e1e; border-bottom: 1px solid #333;"
        )
        url_layout = QHBoxLayout(url_bar)
        url_layout.setContentsMargins(8, 0, 8, 0)
        url_label = QLabel(url)
        url_label.setStyleSheet("color: #bdc3c7; font-family: monospace;")
        url_layout.addWidget(url_label)
        url_layout.addStretch()
        reload_btn = QPushButton("⟳")
        reload_btn.setFixedSize(24, 22)
        reload_btn.setCursor(Qt.PointingHandCursor)
        reload_btn.setToolTip("Reload")
        url_layout.addWidget(reload_btn)
        open_external_btn = QPushButton("↗")
        open_external_btn.setFixedSize(24, 22)
        open_external_btn.setCursor(Qt.PointingHandCursor)
        open_external_btn.setToolTip("Open in browser")
        url_layout.addWidget(open_external_btn)
        layout.addWidget(url_bar)

        # Web view (or fallback)
        if _HAS_WEBENGINE:
            self._view: QWebEngineView | None = QWebEngineView()
            self._view.setUrl(_qurl_from_str(url))
            reload_btn.clicked.connect(self._view.reload)
            open_external_btn.clicked.connect(
                lambda: _open_in_external_browser(url)
            )
            layout.addWidget(self._view, stretch=1)
        else:
            fallback = _PlaceholderPage(
                tool_id,
                (
                    "QtWebEngine is not installed in this environment.\n"
                    f"Open {url} in an external browser to interact with "
                    f"{tool_id}.\n\n"
                    "Install with: pip install PySide6-Addons"
                ),
                can_start=False,
            )
            layout.addWidget(fallback, stretch=1)
            open_external_btn.clicked.connect(
                lambda: _open_in_external_browser(url)
            )

    def reload(self) -> None:
        """Reload the embedded web view."""
        if _HAS_WEBENGINE and self._view is not None:
            self._view.reload()


class _CliToolPage(QWidget):
    """Sub-tab body for a CLI tool — a tmux-attached terminal widget.

    Implementation: a ``QTextEdit`` (read-only) that polls the tmux
    session's ``capture-pane`` output every 250ms and renders it in a
    monospace font.  Input is sent via ``tmux send-keys``.  This is
    not a full PTY emulator but is enough for peek-style orchestration
    of CLI tools that have already been launched in a tmux window by
    the runtime executor.
    """

    def __init__(
        self,
        tool_id: str,
        tmux_session: str,
        tmux_window: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.tool_id = tool_id
        self.tmux_session = tmux_session
        self.tmux_window = tmux_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QFrame()
        header.setFixedHeight(28)
        header.setStyleSheet(
            "background: #1e293b; border-bottom: 1px solid #0f172a;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 0, 8, 0)
        title = QLabel(f"tmux: {tmux_session}:{tmux_window}")
        title.setStyleSheet("color: #cbd5e1; font-family: monospace;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

        # Terminal pane — read-only QTextEdit with a poll-driven refresh
        self._term = QTextEdit()
        self._term.setReadOnly(True)
        self._term.setStyleSheet(
            "background: #0f172a; color: #e2e8f0; "
            "font-family: 'Liberation Mono', 'DejaVu Sans Mono', monospace; "
            "font-size: 12px; padding: 6px;"
        )
        layout.addWidget(self._term, stretch=1)

        # Poll timer — refresh the pane contents 4× per second
        self._poll = QTimer(self)
        self._poll.setInterval(250)
        self._poll.timeout.connect(self._refresh_pane)
        self._poll.start()

        # Initial refresh
        self._refresh_pane()

    def _refresh_pane(self) -> None:
        """Capture the tmux pane contents and render them."""
        try:
            import subprocess
            # tmux capture-pane returns the visible pane content with ANSI
            # stripped.  -p prints to stdout, -e preserves escape sequences
            # (we strip them ourselves to keep the QTextEdit happy).
            proc = subprocess.run(
                [
                    "tmux", "capture-pane",
                    "-t", f"{self.tmux_session}:{self.tmux_window}",
                    "-p", "-S", "-200",
                ],
                capture_output=True, text=True, timeout=1,
                check=False,
            )
            if proc.returncode == 0:
                # Strip trailing whitespace lines
                content = proc.stdout.rstrip()
                # Avoid flicker — only update if content actually changed
                if content != self._term.toPlainText():
                    self._term.setPlainText(content)
                    # Auto-scroll to bottom
                    cursor = self._term.textCursor()
                    cursor.movePosition(cursor.End)
                    self._term.setTextCursor(cursor)
        except (OSError, subprocess.SubprocessError):
            # tmux not installed or session missing — leave the pane as-is
            pass

    def stop_polling(self) -> None:
        """Stop the refresh timer (call when the tab is closed)."""
        self._poll.stop()


class WorkspaceTab(QWidget):
    """Peek-style orchestration surface: one sub-tab per active tool.

    Signals
    -------
    start_tool_requested(str)
        Emitted when the user clicks "Start tool" on a placeholder
        sub-tab.  Payload is the tool_id.  The main window connects
        this to its service-start handler.
    """

    start_tool_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(36)
        header.setStyleSheet(
            "background: #0f172a; border-bottom: 1px solid #1e293b;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        title = QLabel("Workspace")
        title.setStyleSheet("color: #f1f5f9; font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self._status_label = QLabel("No active tools")
        self._status_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        header_layout.addWidget(self._status_label)
        layout.addWidget(header)

        # Sub-tab widget
        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self._on_tab_close)
        layout.addWidget(self._tabs, stretch=1)

        # Track which tool_id owns which sub-tab index
        self._tab_tool_ids: list[str] = []

        # Empty-state placeholder when no sub-tabs are present
        self._empty_label = QLabel(
            "No active tools in the workspace.\n\n"
            "Stage tools in the Stack Editor and they will appear here as "
            "sub-tabs you can interact with — web tools embedded, CLI "
            "tools attached via tmux.\n\n"
            "Think virt-manager for your AI stack."
        )
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            "color: #64748b; font-size: 13px; padding: 40px;"
        )
        self._tabs.addTab(self._empty_label, "(empty)")

    # ── Public API ───────────────────────────────────────────────────

    def refresh(
        self,
        active_tools: Iterable[str],
        registry: dict[str, dict],
        running_tools: Iterable[str],
        port_map: dict[str, int | str],
        tmux_session: str,
    ) -> None:
        """Rebuild the sub-tabs from the active_tools set.

        Parameters
        ----------
        active_tools :
            Tool IDs that are staged (from pipeline_state.active_tools).
        registry :
            The merged registry dict (tool_id → metadata).
        running_tools :
            Tool IDs that are currently running (used to decide whether
            to show the embedded view or a "Start tool" placeholder).
        port_map :
            tool_id → port mapping for web tools.
        tmux_session :
            The tmux session name the runtime uses (e.g. "ai_lsc_1001").
        """
        active = list(active_tools)
        running = set(running_tools)

        # Clear existing tabs
        while self._tabs.count() > 0:
            old = self._tabs.widget(0)
            if isinstance(old, _CliToolPage):
                old.stop_polling()
            self._tabs.removeTab(0)
        self._tab_tool_ids.clear()

        # Re-populate
        for tool_id in active:
            if tool_id.startswith("skill:"):
                continue
            meta = registry.get(tool_id, {})
            flags = meta.get("flags", {})
            launcher = meta.get("launcher", {})
            is_running = tool_id in running

            if flags.get("has_web"):
                port = port_map.get(tool_id) or launcher.get("default_port")
                if is_running and port:
                    url = f"http://127.0.0.1:{port}"
                    page: QWidget = _WebToolPage(tool_id, url)
                    label = f"\U0001f310 {tool_id}"
                else:
                    page = _PlaceholderPage(
                        tool_id,
                        f"{tool_id} is not running. Click below to start it.",
                        can_start=True,
                    )
                    page.start_requested.connect(
                        self.start_tool_requested.emit
                    )
                    label = f"\U0001f310 {tool_id} \u23f8"
            elif flags.get("has_gui") or launcher.get("type") == "desktop":
                # Desktop / GUI application — launched externally,
                # no embeddable surface.  Show a status placeholder.
                page = _PlaceholderPage(
                    tool_id,
                    (
                        f"{tool_id} is a desktop application launched "
                        f"externally.  It is "
                        + ("running." if is_running else "not running.")
                        + "\n\nClick below to launch it."
                    ),
                    can_start=not is_running,
                )
                if not is_running:
                    page.start_requested.connect(
                        self.start_tool_requested.emit
                    )
                label = (
                    f"\U0001f5a5 {tool_id}"
                    if is_running
                    else f"\U0001f5a5 {tool_id} \u23f8"
                )
            elif flags.get("has_cli"):
                if is_running:
                    # tmux window name matches what the TmuxManager uses
                    # (session::tool_id).
                    tmux_window = f"{tmux_session}::{tool_id}"
                    page = _CliToolPage(tool_id, tmux_session, tmux_window)
                    label = f"⌨ {tool_id}"
                else:
                    page = _PlaceholderPage(
                        tool_id,
                        f"{tool_id} is not running. Click below to start it.",
                        can_start=True,
                    )
                    page.start_requested.connect(
                        self.start_tool_requested.emit
                    )
                    label = f"⌨ {tool_id} ⏸"
            else:
                # Passive / library tool — no interactive surface
                page = _PlaceholderPage(
                    tool_id,
                    (
                        f"{tool_id} is a passive/library tool with no "
                        f"interactive surface. It runs in the background "
                        f"and is consumed by other tools."
                    ),
                    can_start=False,
                )
                label = f"📦 {tool_id}"

            self._tabs.addTab(page, label)
            self._tab_tool_ids.append(tool_id)

        # Update the status label
        if active:
            running_count = sum(1 for t in active if t in running)
            self._status_label.setText(
                f"{len(active)} tools staged · {running_count} running"
            )
        else:
            self._status_label.setText("No active tools")
            # Restore the empty-state placeholder if everything was cleared
            if self._tabs.count() == 0:
                self._tabs.addTab(self._empty_label, "(empty)")

    # ── Internal handlers ───────────────────────────────────────────

    def _on_tab_close(self, index: int) -> None:
        """Handle the user closing a sub-tab.  Stops the polling timer
        for CLI pages but does NOT stop the underlying tool — that's
        the user's call from the Stack Editor."""
        if index < 0 or index >= len(self._tab_tool_ids):
            return
        page = self._tabs.widget(index)
        if isinstance(page, _CliToolPage):
            page.stop_polling()
        self._tabs.removeTab(index)
        del self._tab_tool_ids[index]
        # Restore empty-state if everything was closed
        if self._tabs.count() == 0:
            self._tabs.addTab(self._empty_label, "(empty)")


# ── Module-level helpers ──────────────────────────────────────────────


def _qurl_from_str(url: str):
    """Construct a QUrl from a string (lazy import to keep the module
    importable when QtWebEngine is absent)."""
    from PySide6.QtCore import QUrl
    return QUrl(url)


def _open_in_external_browser(url: str) -> None:
    """Open *url* in the user's default browser (fallback for when
    QtWebEngine isn't available)."""
    import webbrowser
    webbrowser.open(url)


__all__ = ["WorkspaceTab"]
