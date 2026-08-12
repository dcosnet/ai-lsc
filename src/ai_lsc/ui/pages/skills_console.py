"""SkillsConsole widget — recursive Modelfile tree scanner and skill compiler.

Scans the skills root directory for Modelfile blueprints, presents them in a
checkable tree, and compiles checked skills via ``ollama create`` in daemon
threads.  Event feedback is appended to an on-screen console log.
"""

import os
import re
import subprocess
import threading
from datetime import datetime

from ai_lsc.constants import TREE_SKIP_PATTERNS
from ai_lsc.utils.process import enriched_env

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QFont
    from PySide6.QtWidgets import (
        QComboBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QPushButton,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

if _HAS_QT:

    class SkillsConsole(QWidget):
        """Scans Modelfile blueprints via recursive tree, compiles checked skills."""

        def __init__(self, parent):
            super().__init__()
            self.parent = parent
            layout = QVBoxLayout(self)

            top = QHBoxLayout()
            top.addWidget(QLabel("Target Runtime Engine:"))
            self.agent_combo = QComboBox()
            self.agent_combo.addItems([
                "Ollama Local Cluster", "Hermes Orchestrator",
                "Odysseus Matrix", "Dify Upstream Pipeline",
            ])
            top.addWidget(self.agent_combo)

            btn_build = QPushButton("Build/Register Selected Skills")
            btn_build.setStyleSheet(
                "background-color: #d35400; color: white; font-weight: bold; "
                "padding: 5px 15px;"
            )
            btn_build.clicked.connect(self.compile_checked_skills)
            top.addWidget(btn_build)
            top.addStretch()
            layout.addLayout(top)

            layout.addWidget(QLabel(
                "Discovered Modelfiles Cluster (Checked = Active):"
            ))
            self.skills_tree = QTreeWidget()
            self.skills_tree.setColumnCount(2)
            self.skills_tree.setHeaderLabels([
                "Skill / Modelfile Model Name",
                "Inferred Functional System Description",
            ])
            self.skills_tree.header().setSectionResizeMode(
                0, QHeaderView.Interactive
            )
            self.skills_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
            self.skills_tree.setColumnWidth(0, 260)
            self.skills_tree.setStyleSheet("""
                QTreeWidget { background-color: #1e1e1e; color: #d4d4d4;
                             border: 1px solid #333; }
                QTreeWidget::item:hover { background-color: #2d2d2d; }
                QHeaderView::section { background-color: #2d2d2d; color: #b2bec3;
                    padding: 4px; border: 1px solid #1e1e1e; }
            """)
            layout.addWidget(self.skills_tree)

            layout.addWidget(QLabel("Skill Generation Event Feedback Log:"))
            self.console_output = QTextEdit()
            self.console_output.setReadOnly(True)
            self.console_output.setFont(QFont("Consolas", 10))
            layout.addWidget(self.console_output)
            self.refresh_skills()

        @staticmethod
        def parse_modelfile_description(file_path: str) -> str:
            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for pattern, flags in [
                    (r'SYSTEM\s+"""(.*?)"""',
                     re.DOTALL | re.IGNORECASE),
                    (r'SYSTEM\s+"(.*?)"', re.IGNORECASE),
                ]:
                    match = re.search(pattern, content, flags)
                    if match:
                        desc = " ".join(match.group(1).strip().splitlines())
                        return desc[:110] + "..." if len(desc) > 110 else desc
                for line in content.splitlines():
                    stripped = line.strip()
                    if (stripped.startswith("#")
                            and "ollama run" not in stripped.lower()
                            and "ollama create" not in stripped.lower()):
                        clean = stripped.lstrip("# ").strip()
                        if clean:
                            return clean
            except Exception:
                pass
            return "Configured Model Template (No embedded description found)"

        def refresh_skills(self):
            self.skills_tree.clear()
            skills_dir = self.parent.skills_root
            if not os.path.exists(skills_dir):
                return
            self._build_tree(self.skills_tree, skills_dir)
            self.skills_tree.expandToDepth(0)

        def _build_tree(self, parent_item, path: str):
            try:
                entries = sorted(os.listdir(path))
            except PermissionError:
                return
            for entry in entries:
                if entry.startswith(".") or entry in TREE_SKIP_PATTERNS:
                    continue
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    if not any(os.scandir(full_path)):
                        continue
                    folder_item = QTreeWidgetItem(parent_item)
                    folder_item.setText(
                        0, entry.replace("-", " ").replace("_", " ").title()
                    )
                    folder_item.setForeground(0, QColor("#e67e22"))
                    font = QFont()
                    font.setBold(True)
                    folder_item.setFont(0, font)
                    self._build_tree(folder_item, full_path)
                elif self._is_valid_modelfile(full_path):
                    desc = self.parse_modelfile_description(full_path)
                    item = QTreeWidgetItem(parent_item)
                    item.setText(0, entry)
                    item.setText(1, desc)
                    item.setToolTip(1, desc)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    item.setCheckState(0, Qt.Unchecked)
                    item.setData(0, Qt.UserRole, full_path)

        @staticmethod
        def _is_valid_modelfile(path: str) -> bool:
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    head = f.read(1024)
                return any(
                    kw in head for kw in ("FROM", "SYSTEM", "# Run `ollama")
                )
            except Exception:
                return False

        def _traverse_checked(self) -> list[tuple[str, str]]:
            results = []

            def walk(item):
                for i in range(item.childCount()):
                    child = item.child(i)
                    if (child.checkState(0) == Qt.Checked
                            and child.data(0, Qt.UserRole)):
                        results.append((child.text(0), child.data(0, Qt.UserRole)))
                    walk(child)

            walk(self.skills_tree.invisibleRootItem())
            return results

        def get_checked_skills(self) -> list[str]:
            return [name for name, _ in self._traverse_checked()]

        def get_all_skills_map(self) -> dict[str, str]:
            mapping = {}

            def walk(item):
                for i in range(item.childCount()):
                    child = item.child(i)
                    fp = child.data(0, Qt.UserRole)
                    if fp:
                        mapping[child.text(0)] = fp
                    walk(child)

            walk(self.skills_tree.invisibleRootItem())
            return mapping

        def compile_checked_skills(self):
            targets = self._traverse_checked()
            if not targets:
                ts = datetime.now().strftime("%H:%M:%S")
                self.console_output.append(
                    f"[{ts}] Compilation bypassed: No model checkboxes active."
                )
                return
            for model_name, path in targets:
                ts = datetime.now().strftime("%H:%M:%S")
                self.console_output.append(
                    f"[{ts}] Injecting Modelfile -> Building: '{model_name}'..."
                )
                threading.Thread(
                    target=self._build_one,
                    args=(model_name, path),
                    daemon=True,
                ).start()

        def _build_one(self, model_name: str, modelfile_path: str):
            try:
                env = enriched_env(self.parent.base_bin_dir)
                proc = subprocess.run(
                    ["ollama", "create", model_name, "-f", modelfile_path],
                    capture_output=True, text=True, env=env,
                    cwd=os.path.dirname(modelfile_path),
                )
                ts = datetime.now().strftime("%H:%M:%S")
                if proc.returncode == 0:
                    html = (
                        f"<span style='color:#2ecc71;'>[{ts}] "
                        f"SUCCESS: '{model_name}' compiled and active.</span>"
                    )
                    QTimer.singleShot(0, self.parent.refresh_all_models)
                else:
                    err = proc.stderr.strip().replace("\n", " ")
                    html = (
                        f"<span style='color:#e74c3c;'>[{ts}] "
                        f"ERROR on '{model_name}': {err}</span>"
                    )
                QTimer.singleShot(0, lambda: self.console_output.append(html))
            except Exception as exc:
                ts = datetime.now().strftime("%H:%M:%S")
                QTimer.singleShot(
                    0, lambda: self.console_output.append(
                        f"[{ts}] Exception: {exc}"
                    )
                )

else:
    SkillsConsole = None
