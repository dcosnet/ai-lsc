"""Verification UI tab — per-tool installation compliance dashboard.

Provides a table showing all registered tools with their verification
scores, individual check results, and bulk verification controls.
Integrates with ``InstallerManager.verify()`` to run the compliance
checklist and display results in real time.

Requires PySide6.  When PySide6 is not installed, the module still
parses but exports stub classes so that ``agents/__init__.py`` style
try/except imports work.
"""

from __future__ import annotations

import os
import threading
from typing import Any

from ai_lsc.constants import BASE_DIR

try:
    from PySide6.QtCore import QThread, Signal, Qt, QTimer
    from PySide6.QtGui import QColor, QFont, QPalette
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMainWindow,
        QProgressBar,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False
    QWidget = object  # type: ignore[assignment, misc]
    QThread = object  # type: ignore[assignment, misc]
    Signal = lambda *a, **kw: None  # type: ignore[assignment, misc]


# ── Verification worker (runs in background thread) ─────────────────

class VerificationWorker(QThread if _HAS_QT else object):  # type: ignore[misc]
    """Run verification checks for a batch of tools in a background thread."""

    progress = Signal(int, int)       # (completed, total)
    tool_done = Signal(str, dict)    # (tool_id, result_dict)
    finished = Signal(int)           # total tools processed

    def __init__(
        self,
        tools: dict[str, dict[str, Any]],
        tools_root: str,
        base_dir: str = BASE_DIR,
        parent: QWidget | None = None,
    ) -> None:
        if not _HAS_QT:
            return
        super().__init__(parent)
        self.tools = tools
        self.tools_root = tools_root
        self.base_dir = base_dir

    def run(self) -> None:
        if not _HAS_QT:
            return
        from ai_lsc.runtime.installer import InstallerManager

        mgr = InstallerManager(self.tools_root, self.base_dir)
        total = len(self.tools)
        completed = 0

        for tool_id, meta in self.tools.items():
            installer = meta.get("installer", {})
            fs = meta.get("filesystem", {})
            result = mgr.verify(
                tool_id=tool_id,
                inst_type=installer.get("type", "pacman"),
                pkg=installer.get("pkg", ""),
                cmd=installer.get("cmd", ""),
                filesystem=fs,
            )
            self.tool_done.emit(tool_id, result)
            completed += 1
            self.progress.emit(completed, total)

        self.finished.emit(total)


# ── Verification Tab ────────────────────────────────────────────────

class VerificationTab(QWidget if _HAS_QT else object):  # type: ignore[misc]
    """Dashboard showing per-tool installation verification results.

    Columns:
        - Tool ID
        - Install Type
        - Score (0-100%)
        - Native Install
        - Filesystem Compliance
        - Config Redirect
        - Cache Redirect
        - Logs Redirect
        - Launcher Accessible
        - Version Detection
        - Health Check
        - Location
    """

    def __init__(
        self,
        registry: dict[str, dict[str, Any]],
        tools_root: str,
        base_dir: str = BASE_DIR,
        parent: QWidget | None = None,
    ) -> None:
        if not _HAS_QT:
            return
        super().__init__(parent)
        self.registry = registry
        self.tools_root = tools_root
        self.base_dir = base_dir
        self._worker: VerificationWorker | None = None
        self._results: dict[str, dict] = {}
        self._init_ui()
        self._populate_table()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # ── Header ───────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel(
            "<b>Installation Verification — Ankh of Jah</b>"
        )
        title.setFont(QFont("Segoe UI", 14))
        hdr.addWidget(title)
        hdr.addStretch()
        layout.addLayout(hdr)

        # ── Controls ───────────────────────────────────────────────
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet(
            "QFrame { border: 1px solid #333; border-radius: 6px; "
            "padding: 8px; background-color: #1a1a1a; }"
        )
        ctrl_layout = QHBoxLayout(ctrl_frame)

        self.btn_verify_all = QPushButton("Verify All Tools")
        self.btn_verify_all.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: #000; "
            "font-weight: bold; padding: 8px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #27ae60; }"
        )
        self.btn_verify_all.clicked.connect(self._run_batch_verify)
        ctrl_layout.addWidget(self.btn_verify_all)

        self.btn_verify_selected = QPushButton("Verify Selected")
        self.btn_verify_selected.setStyleSheet(
            "QPushButton { background-color: #3498db; color: #fff; "
            "font-weight: bold; padding: 8px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #2980b9; }"
        )
        self.btn_verify_selected.clicked.connect(self._run_selected_verify)
        ctrl_layout.addWidget(self.btn_verify_selected)

        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("Filter by tool ID...")
        self.txt_filter.setMaximumWidth(250)
        self.txt_filter.setStyleSheet(
            "QLineEdit { background-color: #1e1e1e; border: 1px solid #444; "
            "color: white; padding: 6px; border-radius: 4px; }"
        )
        self.txt_filter.textChanged.connect(self._apply_filter)
        ctrl_layout.addWidget(self.txt_filter)

        ctrl_layout.addStretch()

        # Summary label
        self.lbl_summary = QLabel("Ready — no verifications run yet")
        self.lbl_summary.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        ctrl_layout.addWidget(self.lbl_summary)

        layout.addWidget(ctrl_frame)

        # ── Progress bar ────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #333; border-radius: 4px; "
            "background-color: #1e1e1e; text-align: center; color: white; "
            "min-height: 20px; }"
            "QProgressBar::chunk { background-color: #2ecc71; border-radius: 3px; }"
        )
        layout.addWidget(self.progress_bar)

        # ── Results table ──────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "Tool ID", "Type", "Score",
            "Native", "FS OK", "Config", "Cache", "Logs",
            "Binary", "Version", "Health", "Location",
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        header = self.table.horizontalHeader()
        # All columns interactive so user can resize to read content
        for col in range(self.table.columnCount()):
            header.setSectionResizeMode(
                col, QHeaderView.ResizeMode.Interactive
            )
        # Set sensible default widths
        col_widths = [200, 80, 60, 60, 60, 60, 60, 60, 60, 60, 60, 250]
        for col, width in enumerate(col_widths):
            self.table.setColumnWidth(col, width)

        self.table.setStyleSheet(
            "QTableWidget { background-color: #1e1e1e; "
            "gridline-color: #333; border: 1px solid #333; }"
            "QTableWidget::item { padding: 4px; }"
            "QHeaderView::section { background-color: #2c3e50; "
            "color: white; padding: 4px; border: 1px solid #1a252f; "
            "font-weight: bold; }"
        )

        layout.addWidget(self.table)

    def _populate_table(self) -> None:
        """Fill the table with all registered tools (unverified state)."""
        self.table.setRowCount(len(self.registry))
        for row, (tool_id, meta) in enumerate(
            sorted(self.registry.items())
        ):
            installer = meta.get("installer", {})
            name = meta.get("name", tool_id)

            self.table.setItem(
                row, 0, QTableWidgetItem(name or tool_id)
            )
            self.table.setItem(
                row, 1, QTableWidgetItem(
                    installer.get("type", "unknown")
                )
            )
            self.table.setItem(row, 2, QTableWidgetItem("\u2014"))
            for col in range(3, 12):
                self.table.setItem(row, col, QTableWidgetItem("\u2014"))

    def _run_batch_verify(self) -> None:
        """Verify all tools in a background thread."""
        if self._worker and self._worker.isRunning():
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_verify_all.setEnabled(False)
        self.btn_verify_selected.setEnabled(False)
        self.lbl_summary.setText("Verifying all tools...")

        self._worker = VerificationWorker(
            self.registry, self.tools_root, self.base_dir, self,
        )
        self._worker.tool_done.connect(self._on_tool_result)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_batch_done)
        self._worker.start()

    def _run_selected_verify(self) -> None:
        """Verify only the currently selected rows."""
        rows = set(
            i.row() for i in self.table.selectedItems()
        )
        if not rows:
            return

        # Build a subset of the registry for selected tools
        selected_tools: dict[str, dict[str, Any]] = {}
        for row in rows:
            item = self.table.item(row, 0)
            if item:
                tool_name = item.text()
                # Map display name back to tool_id
                for tid, meta in self.registry.items():
                    if meta.get("name", tid) == tool_name or tid == tool_name:
                        selected_tools[tid] = self.registry[tid]
                        break

        if not selected_tools:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(selected_tools))
        self.progress_bar.setValue(0)
        self.lbl_summary.setText(
            f"Verifying {len(selected_tools)} selected tools..."
        )

        self._worker = VerificationWorker(
            selected_tools, self.tools_root, self.base_dir, self,
        )
        self._worker.tool_done.connect(self._on_tool_result)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_batch_done)
        self._worker.start()

    def _on_progress(self, completed: int, total: int) -> None:
        """Update the progress bar."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(completed)

    def _on_tool_result(self, tool_id: str, result: dict) -> None:
        """Update a single row with verification results."""
        self._results[tool_id] = result

        # Find the row for this tool
        row = -1
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item is None:
                continue
            item_text = item.text()
            expected = self.registry.get(tool_id, {}).get("name", tool_id)
            if item_text == expected or item_text == tool_id:
                row = r
                break

        if row < 0:
            return

        checks = result.get("checks", [])
        score = result.get("score", 0)
        location = result.get("install_location", "")

        # Build a check-name -> passed map
        check_map = {c["name"]: c["passed"] for c in checks}

        # Score cell (colour-coded)
        score_item = QTableWidgetItem(f"{score}%")
        if score >= 80:
            score_item.setForeground(QColor("#2ecc71"))
        elif score >= 50:
            score_item.setForeground(QColor("#f39c12"))
        else:
            score_item.setForeground(QColor("#e74c3c"))
        score_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.table.setItem(row, 2, score_item)

        # Individual checks: columns 3-10
        check_columns = [
            "Native Install", "Filesystem Compliance",
            "Config Redirect", "Cache Redirect", "Logs Redirect",
            "Launcher Accessible", "Version Detection", "Health Check",
        ]
        for idx, check_name in enumerate(check_columns):
            col = 3 + idx
            passed = check_map.get(check_name)
            if passed is None:
                text = "N/A"
                color = "#7f8c8d"
            elif passed:
                text = "PASS"
                color = "#2ecc71"
            else:
                text = "FAIL"
                color = "#e74c3c"
            item = QTableWidgetItem(text)
            item.setForeground(QColor(color))
            self.table.setItem(row, col, item)

        # Location
        self.table.setItem(row, 11, QTableWidgetItem(location))

    def _on_batch_done(self, total: int) -> None:
        """Finalize after batch verification completes."""
        self.progress_bar.setVisible(False)
        self.btn_verify_all.setEnabled(True)
        self.btn_verify_selected.setEnabled(True)

        # Compute summary
        scores = [r["score"] for r in self._results.values()]
        if scores:
            avg = sum(scores) / len(scores)
            passing = sum(1 for s in scores if s >= 80)
            failing = sum(1 for s in scores if s < 50)
            self.lbl_summary.setText(
                f"Verified {total} tools | "
                f"Average: {avg:.0f}% | "
                f"Passing (>=80%): {passing} | "
                f"Failing (<50%): {failing}"
            )
        else:
            self.lbl_summary.setText(
                f"No verification results for {total} tools"
            )

    def _apply_filter(self, text: str) -> None:
        """Filter visible rows by tool ID substring."""
        filter_lower = text.lower().strip()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                continue
            visible = (
                not filter_lower
                or filter_lower in item.text().lower()
            )
            self.table.setRowHidden(row, not visible)

    def refresh(self) -> None:
        """Re-populate table from registry (e.g. after tool install)."""
        self._results.clear()
        self._populate_table()
        self.lbl_summary.setText("Ready \u2014 no verifications run yet")
