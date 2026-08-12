"""GitWorktreeTab — Git Repo Manager for all registry git/git_node tools.

Automatically lists every tool whose installer type is ``git`` or
``git_node`` from the merged registry.  Each row shows the tool's
name, source URL, layer, installation status, current branch/commit,
and whether the working tree is dirty.  Actions: update (git pull),
open directory, install (clone).

No excuses — if a tool is in the registry with installer type git or
git_node, it appears here.
"""

import os
import subprocess

from ai_lsc.utils.process import enriched_env

try:
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QColor, QFont
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QPushButton,
        QProgressBar,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

# Installer types that mean "installed via git".
_GIT_INSTALLER_TYPES = {"git", "git_node"}


def _run_git(
    args: list[str],
    cwd: str,
    env: dict[str, str] | None = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess:
    """Run a git command and return the CompletedProcess."""
    return subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        timeout=timeout,
    )


def _repo_status(git_dir: str, env: dict[str, str]) -> dict:
    """Probe a git working tree for branch, commit, tag, dirty state.

    Returns a dict with keys: branch, commit, tag, dirty, ahead, behind.
    All values are strings (empty string when unavailable).
    """
    info: dict[str, str] = {
        "branch": "",
        "commit": "",
        "tag": "",
        "dirty": "",
        "ahead": "",
        "behind": "",
    }
    if not os.path.isdir(os.path.join(git_dir, ".git")):
        return info

    # Branch
    try:
        r = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], git_dir, env)
        if r.returncode == 0:
            info["branch"] = r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass

    # Short commit
    try:
        r = _run_git(["rev-parse", "--short", "HEAD"], git_dir, env)
        if r.returncode == 0:
            info["commit"] = r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass

    # Nearest tag
    try:
        r = _run_git(
            ["describe", "--tags", "--abbrev=0", "--always"],
            git_dir, env, timeout=10,
        )
        if r.returncode == 0:
            info["tag"] = r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass

    # Dirty check (anything staged or unstaged)
    try:
        r = _run_git(["status", "--porcelain"], git_dir, env, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            info["dirty"] = "yes"
    except (OSError, subprocess.SubprocessError):
        pass

    # Ahead/behind upstream
    try:
        r = _run_git(
            ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"],
            git_dir, env, timeout=10,
        )
        if r.returncode == 0:
            parts = r.stdout.strip().split("\t")
            if len(parts) == 2:
                ahead, behind = parts
                if ahead != "0":
                    info["ahead"] = ahead
                if behind != "0":
                    info["behind"] = behind
    except (OSError, subprocess.SubprocessError):
        pass

    return info


class _GitOpThread(QThread):
    """Background thread for git pull operations."""
    finished = Signal(str, str, str)  # tool_id, status, message
    progress = Signal(str, int)       # tool_id, percent

    def __init__(self, tool_id: str, git_dir: str, env: dict, parent=None):
        super().__init__(parent)
        self.tool_id = tool_id
        self.git_dir = git_dir
        self.env = env

    def run(self) -> None:
        self.progress.emit(self.tool_id, 10)
        try:
            r = _run_git(["pull", "--ff-only"], self.git_dir, self.env, timeout=120)
            self.progress.emit(self.tool_id, 90)
            if r.returncode == 0:
                self.finished.emit(
                    self.tool_id, "ok",
                    r.stdout.strip() or "Already up to date.",
                )
            else:
                stderr = r.stderr.strip() or "Unknown error"
                # Trim to first line for display
                stderr = stderr.split("\n")[0]
                self.finished.emit(self.tool_id, "error", stderr)
        except subprocess.TimeoutExpired:
            self.finished.emit(self.tool_id, "error", "Pull timed out (120s)")
        except (OSError, subprocess.SubprocessError) as exc:
            self.finished.emit(self.tool_id, "error", str(exc))
        self.progress.emit(self.tool_id, 100)


if _HAS_QT:

    class GitWorktreeTab(QWidget):
        """Git Repo Manager — auto-populated from the registry.

        Every tool whose installer.type is ``git`` or ``git_node``
        appears in the table automatically.  The table shows real-time
        git status (branch, commit, dirty) for installed repos and
        provides update/install actions.
        """

        # ── Column indices ───────────────────────────────────────────
        _COL_TOOL_ID = 0
        _COL_NAME = 1
        _COL_SOURCE = 2
        _COL_LAYER = 3
        _COL_CATEGORY = 4
        _COL_INSTALLER = 5
        _COL_BRANCH = 6
        _COL_COMMIT = 7
        _COL_TAG = 8
        _COL_STATUS = 9
        _COL_ACTIONS = 10
        _COLUMN_COUNT = 11

        def __init__(self, main_window):
            super().__init__()
            self.main = main_window
            self._threads: list[_GitOpThread] = []

            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(6)

            # ── Header ────────────────────────────────────────────────
            header = QHBoxLayout()
            lbl_title = QLabel("<b>Git Repo Manager</b>")
            lbl_title.setFont(QFont("Segoe UI", 13))
            header.addWidget(lbl_title)
            header.addStretch()

            self.lbl_counts = QLabel("")
            self.lbl_counts.setStyleSheet("color: #7f8c8d; font-size: 11px;")
            header.addWidget(self.lbl_counts)
            header.addSpacing(12)

            self.btn_refresh = QPushButton("Refresh")
            self.btn_refresh.setStyleSheet(
                "background-color: #2980b9; color: white; "
                "padding: 5px 14px; border-radius: 3px;"
            )
            self.btn_refresh.clicked.connect(self.refresh)
            header.addWidget(self.btn_refresh)

            self.btn_update_all = QPushButton("Update All Installed")
            self.btn_update_all.setStyleSheet(
                "background-color: #27ae60; color: white; "
                "padding: 5px 14px; border-radius: 3px;"
            )
            self.btn_update_all.clicked.connect(self._update_all_installed)
            header.addWidget(self.btn_update_all)
            layout.addLayout(header)

            # ── Filter row ────────────────────────────────────────────
            filter_row = QHBoxLayout()
            self.btn_filter_all = QPushButton("All")
            self.btn_filter_all.setStyleSheet(
                "padding: 3px 10px; border: 1px solid #2ecc71; "
                "color: #2ecc71; border-radius: 3px;"
            )
            self.btn_filter_all.clicked.connect(
                lambda: self._set_filter("all")
            )
            filter_row.addWidget(self.btn_filter_all)

            self.btn_filter_installed = QPushButton("Installed")
            self.btn_filter_installed.setStyleSheet(
                "padding: 3px 10px; border: 1px solid #333; "
                "color: #bdc3c7; border-radius: 3px;"
            )
            self.btn_filter_installed.clicked.connect(
                lambda: self._set_filter("installed")
            )
            filter_row.addWidget(self.btn_filter_installed)

            self.btn_filter_missing = QPushButton("Not Installed")
            self.btn_filter_missing.setStyleSheet(
                "padding: 3px 10px; border: 1px solid #333; "
                "color: #bdc3c7; border-radius: 3px;"
            )
            self.btn_filter_missing.clicked.connect(
                lambda: self._set_filter("missing")
            )
            filter_row.addWidget(self.btn_filter_missing)

            self.btn_filter_dirty = QPushButton("Dirty")
            self.btn_filter_dirty.setStyleSheet(
                "padding: 3px 10px; border: 1px solid #333; "
                "color: #bdc3c7; border-radius: 3px;"
            )
            self.btn_filter_dirty.clicked.connect(
                lambda: self._set_filter("dirty")
            )
            filter_row.addWidget(self.btn_filter_dirty)

            filter_row.addStretch()

            self.lbl_filter_info = QLabel("")
            self.lbl_filter_info.setStyleSheet("color: #7f8c8d; font-size: 10px;")
            filter_row.addWidget(self.lbl_filter_info)
            layout.addLayout(filter_row)

            # ── Progress bar ──────────────────────────────────────────
            self.progress_bar = QProgressBar()
            self.progress_bar.setMaximumHeight(3)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setStyleSheet(
                "QProgressBar { background: #1a1a1a; border: none; }"
                "QProgressBar::chunk { background: #2ecc71; }"
            )
            self.progress_bar.setVisible(False)
            layout.addWidget(self.progress_bar)

            # ── Main table ────────────────────────────────────────────
            self.table = QTableWidget(0, self._COLUMN_COUNT)
            self.table.setHorizontalHeaderLabels([
                "Tool ID", "Name", "Source URL", "Layer",
                "Category", "Type", "Branch", "Commit",
                "Tag", "Status", "Actions",
            ])
            self.table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeToContents,
            )
            self.table.horizontalHeader().setSectionResizeMode(
                self._COL_SOURCE, QHeaderView.Stretch,
            )
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table.setAlternatingRowColors(True)
            self.table.verticalHeader().setVisible(False)
            self.table.setStyleSheet(
                "QTableWidget { background-color: #0f0f0f; "
                "alternate-background-color: #141414; "
                "gridline-color: #252525; }"
                "QTableWidget::item { padding: 3px 6px; }"
                "QHeaderView::section { background-color: #1a1a1a; "
                "color: #bdc3c7; padding: 4px; border: none; "
                "border-bottom: 1px solid #333; }"
            )
            layout.addWidget(self.table)

            self._current_filter = "all"
            self._cached_rows: list[dict] = []
            self.refresh()

        # ── Public API ────────────────────────────────────────────────

        def refresh(self) -> None:
            """Re-scan the registry and refresh the table."""
            self._cached_rows = self._gather_git_tools()
            self._apply_filter()

        # ── Registry scan ─────────────────────────────────────────────

        def _gather_git_tools(self) -> list[dict]:
            """Collect every git/git_node tool from the registry + probe
            their on-disk status."""
            registry = self.main.registry_mgr.get_all_tools()
            env = enriched_env(self.main.base_bin_dir)
            rows: list[dict] = []

            for tool_id, meta in registry.items():
                installer = meta.get("installer", {})
                inst_type = installer.get("type", "")
                if inst_type not in _GIT_INSTALLER_TYPES:
                    continue

                source_url = installer.get("pkg", "")
                tools_root = self.main.tools_root
                git_dir = os.path.join(tools_root, tool_id)
                on_disk = os.path.isdir(os.path.join(git_dir, ".git"))

                row: dict = {
                    "tool_id": tool_id,
                    "name": meta.get("name", tool_id),
                    "source_url": source_url,
                    "layer": meta.get("layer", ""),
                    "category": meta.get("category", ""),
                    "installer_type": inst_type,
                    "git_dir": git_dir,
                    "on_disk": on_disk,
                    "branch": "",
                    "commit": "",
                    "tag": "",
                    "dirty": False,
                    "ahead": 0,
                    "behind": 0,
                }

                if on_disk:
                    status = _repo_status(git_dir, env)
                    row["branch"] = status.get("branch", "")
                    row["commit"] = status.get("commit", "")
                    row["tag"] = status.get("tag", "")
                    row["dirty"] = status.get("dirty") == "yes"
                    row["ahead"] = int(status.get("ahead") or 0)
                    row["behind"] = int(status.get("behind") or 0)

                rows.append(row)

            # Sort: installed first, then alphabetically by name
            rows.sort(key=lambda r: (not r["on_disk"], r["name"].lower()))
            return rows

        # ── Filtering ─────────────────────────────────────────────────

        def _set_filter(self, mode: str) -> None:
            """Set the active filter mode and re-render."""
            self._current_filter = mode
            # Reset all filter button styles
            buttons = {
                "all": self.btn_filter_all,
                "installed": self.btn_filter_installed,
                "missing": self.btn_filter_missing,
                "dirty": self.btn_filter_dirty,
            }
            for key, btn in buttons.items():
                active = key == mode
                btn.setStyleSheet(
                    "padding: 3px 10px; border-radius: 3px; "
                    f"border: 1px solid {'#2ecc71' if active else '#333'}; "
                    f"color: {'#2ecc71' if active else '#bdc3c7'}; "
                    f"background: {'rgba(46,204,113,0.08)' if active else 'transparent'};"
                )
            self._apply_filter()

        def _apply_filter(self) -> None:
            """Render the cached rows through the current filter."""
            filt = self._current_filter
            if filt == "installed":
                visible = [r for r in self._cached_rows if r["on_disk"]]
            elif filt == "missing":
                visible = [r for r in self._cached_rows if not r["on_disk"]]
            elif filt == "dirty":
                visible = [r for r in self._cached_rows if r["dirty"]]
            else:
                visible = self._cached_rows

            self._render_rows(visible)

            # Update count label
            total = len(self._cached_rows)
            installed = sum(1 for r in self._cached_rows if r["on_disk"])
            dirty = sum(1 for r in self._cached_rows if r["dirty"])
            self.lbl_counts.setText(
                f"{installed}/{total} installed  |  {dirty} dirty"
            )
            self.lbl_filter_info.setText(
                f"Showing {len(visible)} of {total} git sources"
            )

        # ── Table rendering ───────────────────────────────────────────

        def _render_rows(self, rows: list[dict]) -> None:
            """Populate the table widget from the given row dicts."""
            self.table.setRowCount(0)

            for row_data in rows:
                row = self.table.rowCount()
                self.table.insertRow(row)
                tool_id = row_data["tool_id"]

                # Tool ID
                self.table.setItem(
                    row, self._COL_TOOL_ID,
                    self._make_item(tool_id, mono=True),
                )

                # Name
                self.table.setItem(
                    row, self._COL_NAME,
                    self._make_item(row_data["name"]),
                )

                # Source URL
                self.table.setItem(
                    row, self._COL_SOURCE,
                    self._make_item(
                        row_data["source_url"],
                        color="#3498db",
                    ),
                )

                # Layer
                self.table.setItem(
                    row, self._COL_LAYER,
                    self._make_item(row_data["layer"]),
                )

                # Category
                self.table.setItem(
                    row, self._COL_CATEGORY,
                    self._make_item(row_data["category"], color="#7f8c8d"),
                )

                # Installer type badge
                inst_label = row_data["installer_type"]
                self.table.setItem(
                    row, self._COL_INSTALLER,
                    self._make_item(
                        inst_label,
                        color="#e67e22" if inst_label == "git_node" else "#95a5a6",
                    ),
                )

                # Branch
                self.table.setItem(
                    row, self._COL_BRANCH,
                    self._make_item(
                        row_data["branch"] or "—",
                        color="#2ecc71" if row_data["on_disk"] else "#555",
                    ),
                )

                # Commit
                self.table.setItem(
                    row, self._COL_COMMIT,
                    self._make_item(
                        row_data["commit"] or "—",
                        mono=True,
                        color="#bdc3c7" if row_data["on_disk"] else "#555",
                    ),
                )

                # Tag
                self.table.setItem(
                    row, self._COL_TAG,
                    self._make_item(
                        row_data["tag"] or "—",
                        color="#f39c12" if row_data["tag"] else "#555",
                    ),
                )

                # Status
                status_text, status_color = self._status_label(row_data)
                self.table.setItem(
                    row, self._COL_STATUS,
                    self._make_item(status_text, color=status_color),
                )

                # Actions widget
                self.table.setCellWidget(
                    row, self._COL_ACTIONS,
                    self._make_actions_widget(row_data),
                )

        @staticmethod
        def _make_item(
            text: str,
            mono: bool = False,
            color: str = "#ddd",
        ) -> QTableWidgetItem:
            item = QTableWidgetItem(text)
            item.setForeground(QColor(color))
            if mono:
                item.setFont(QFont("Consolas", 9))
            item.setTextAlignment(
                Qt.AlignCenter if mono else Qt.AlignLeft | Qt.AlignVCenter
            )
            return item

        def _status_label(self, row: dict) -> tuple[str, str]:
            """Return (label, color) for the status column."""
            if not row["on_disk"]:
                return ("Not Installed", "#e74c3c")
            if row["dirty"]:
                return ("Dirty", "#e67e22")
            if row["behind"] > 0:
                return (f"Behind ({row['behind']})", "#f39c12")
            return ("Clean", "#2ecc71")

        def _make_actions_widget(self, row: dict) -> QWidget:
            """Build the action buttons for a single row."""
            container = QWidget()
            h = QHBoxLayout(container)
            h.setContentsMargins(2, 0, 2, 0)
            h.setSpacing(4)

            tool_id = row["tool_id"]
            git_dir = row["git_dir"]
            on_disk = row["on_disk"]

            if on_disk:
                btn_update = QPushButton("Update")
                btn_update.setFixedWidth(64)
                btn_update.setStyleSheet(
                    "QPushButton { background: #2980b9; color: white; "
                    "padding: 2px 6px; border-radius: 3px; font-size: 10px; }"
                    "QPushButton:hover { background: #3498db; }"
                )
                btn_update.clicked.connect(
                    lambda checked, tid=tool_id, gd=git_dir: self._update_one(tid, gd)
                )
                h.addWidget(btn_update)

                btn_open = QPushButton("Open")
                btn_open.setFixedWidth(52)
                btn_open.setStyleSheet(
                    "QPushButton { background: #333; color: #bdc3c7; "
                    "padding: 2px 6px; border-radius: 3px; font-size: 10px; }"
                    "QPushButton:hover { background: #444; }"
                )
                btn_open.clicked.connect(
                    lambda checked, gd=git_dir: self._open_dir(gd)
                )
                h.addWidget(btn_open)
            else:
                btn_install = QPushButton("Install")
                btn_install.setFixedWidth(64)
                btn_install.setStyleSheet(
                    "QPushButton { background: #27ae60; color: white; "
                    "padding: 2px 6px; border-radius: 3px; font-size: 10px; }"
                    "QPushButton:hover { background: #2ecc71; }"
                )
                btn_install.clicked.connect(
                    lambda checked, tid=tool_id: self._install_tool(tid)
                )
                h.addWidget(btn_install)

            return container

        # ── Actions ───────────────────────────────────────────────────

        def _install_tool(self, tool_id: str) -> None:
            """Trigger installation of a git tool via the installer."""
            meta = self.main.registry_mgr.get_tool(tool_id)
            if not meta:
                self.main.log(
                    f"Tool {tool_id} not found in registry.", "GitRepo"
                )
                return

            installer = meta.get("installer", {})
            inst_type = installer.get("type", "")
            pkg = installer.get("pkg", "")
            post_install = installer.get("post_install")
            env_overrides = installer.get("env_overrides", {})

            from ai_lsc.runtime.installer import InstallerManager
            mgr = InstallerManager(
                tools_root=self.main.tools_root,
                base_bin_dir=self.main.base_bin_dir,
            )
            try:
                if inst_type == "git_node":
                    msg = mgr.install_git_node(pkg, tool_id, post_install)
                else:
                    msg = mgr.install_git(
                        pkg, tool_id, post_install, env_overrides or None,
                    )
                self.main.log(msg, "GitRepo")
                self.refresh()
            except Exception as exc:
                self.main.log(
                    f"Install failed for {tool_id}: {exc}", "GitRepo"
                )

        def _update_one(self, tool_id: str, git_dir: str) -> None:
            """Kick off a background git pull for one tool."""
            env = enriched_env(self.main.base_bin_dir)
            thread = _GitOpThread(tool_id, git_dir, env, parent=self)
            thread.finished.connect(self._on_git_op_finished)
            thread.progress.connect(self._on_git_op_progress)
            self._threads.append(thread)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            thread.start()

        def _update_all_installed(self) -> None:
            """Update every installed git repo."""
            env = enriched_env(self.main.base_bin_dir)
            installed = [
                r for r in self._cached_rows if r["on_disk"]
            ]
            if not installed:
                self.main.log("No installed git repos to update.", "GitRepo")
                return

            self._threads.clear()
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(installed) * 100)
            self.progress_bar.setValue(0)

            for row in installed:
                thread = _GitOpThread(
                    row["tool_id"], row["git_dir"], env, parent=self,
                )
                thread.finished.connect(self._on_git_op_finished)
                thread.progress.connect(self._on_git_op_progress)
                self._threads.append(thread)

            # Chain-start: run max 3 concurrent, start next as each finishes
            self._batch_queue = list(self._threads)
            self._batch_total = len(self._batch_queue)
            self._batch_idx = 0
            self._batch_done_count = 0
            for _ in range(min(3, len(self._batch_queue))):
                self._batch_queue[self._batch_idx].start()
                self._batch_idx += 1

            self.main.log(
                f"Updating {len(installed)} git repo(s)...", "GitRepo"
            )

        def _on_git_op_finished(
            self, tool_id: str, status: str, message: str,
        ) -> None:
            """Handle completion of a git operation."""
            if status == "ok":
                self.main.log(f"Updated {tool_id}: {message}", "GitRepo")
            else:
                self.main.log(
                    f"Update FAILED {tool_id}: {message}", "GitRepo"
                )

            # Batch progress tracking
            if hasattr(self, '_batch_total') and self._batch_total > 0:
                self._batch_done_count += 1
                pct = int(self._batch_done_count / self._batch_total * 100)
                self.progress_bar.setValue(pct)
                # Chain-start next queued thread
                if self._batch_idx < len(self._batch_queue):
                    self._batch_queue[self._batch_idx].start()
                    self._batch_idx += 1

            # Check if all threads are done
            all_done = all(not t.isRunning() for t in self._threads)
            if all_done and self._threads:
                self.progress_bar.setVisible(False)
                self._threads.clear()
                self.refresh()

        def _on_git_op_progress(self, tool_id: str, percent: int) -> None:
            """Handle progress from a single-thread update."""
            if len(self._threads) == 1:
                self.progress_bar.setValue(percent)

        def _open_dir(self, git_dir: str) -> None:
            """Open the git directory in the system file manager."""
            try:
                subprocess.Popen(
                    ["xdg-open", git_dir],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except FileNotFoundError:
                self.main.log(
                    "Cannot open directory: xdg-open not found.", "GitRepo"
                )

        # ── Legacy compat ─────────────────────────────────────────────

        def scan_repos(self):
            """Legacy compat — delegates to refresh."""
            self.refresh()

        def _current_repo_path(self) -> str | None:
            """Legacy compat — not used in new layout."""
            return None


else:
    GitWorktreeTab = None