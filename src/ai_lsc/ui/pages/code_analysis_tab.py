"""Code Analysis Workbench tab widget.

Provides ripgrep search, fd file-finding, Python AST inspection,
and tree-sitter parse utilities — extracted from the monolith.
"""

import json
import os
import os.path
import subprocess
import threading

from ai_lsc.utils.process import enriched_env

try:
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

if _HAS_QT:

    class CodeAnalysisTab(QWidget):
        """Code analysis: ripgrep search, tree-sitter parse, Python AST inspection."""

        def __init__(self, main_window):
            super().__init__()
            self.main = main_window
            layout = QVBoxLayout(self)

            header = QHBoxLayout()
            header.addWidget(QLabel("<b>Code Analysis Workbench</b>"))
            header.addStretch()
            layout.addLayout(header)

            self.analysis_tabs = QTabWidget()

            # --- ripgrep / fd panel ---
            rg_page = QWidget()
            rg_layout = QVBoxLayout(rg_page)
            rg_ctrl = QHBoxLayout()
            rg_ctrl.addWidget(QLabel("Pattern:"))
            self.txt_rg_pattern = QLineEdit()
            self.txt_rg_pattern.setPlaceholderText("regex pattern...")
            rg_ctrl.addWidget(self.txt_rg_pattern)
            rg_ctrl.addWidget(QLabel("Path:"))
            self.txt_rg_path = QLineEdit(self.main.base_dir)
            rg_ctrl.addWidget(self.txt_rg_path)
            btn_rg = QPushButton("Search (rg)")
            btn_rg.setStyleSheet("background-color: #2980b9; color: white;")
            btn_rg.clicked.connect(self.run_ripgrep)
            rg_ctrl.addWidget(btn_rg)
            btn_fd = QPushButton("Find (fd)")
            btn_fd.setStyleSheet("background-color: #8e44ad; color: white;")
            btn_fd.clicked.connect(self.run_fd)
            rg_ctrl.addWidget(btn_fd)
            rg_layout.addLayout(rg_ctrl)
            self.rg_output = QTextEdit()
            self.rg_output.setReadOnly(True)
            self.rg_output.setFont(QFont("Consolas", 10))
            self.rg_output.setStyleSheet(
                "background-color: #0d0d0d; color: #cfd8dc; padding: 8px;"
            )
            rg_layout.addWidget(self.rg_output)
            self.analysis_tabs.addTab(rg_page, "ripgrep / fd")

            # --- AST inspection panel ---
            ast_page = QWidget()
            ast_layout = QVBoxLayout(ast_page)
            ast_ctrl = QHBoxLayout()
            ast_ctrl.addWidget(QLabel("Python File:"))
            self.txt_ast_file = QLineEdit()
            self.txt_ast_file.setPlaceholderText("/path/to/file.py")
            ast_ctrl.addWidget(self.txt_ast_file)
            btn_browse = QPushButton("Browse")
            btn_browse.clicked.connect(self.browse_ast_file)
            ast_ctrl.addWidget(btn_browse)
            btn_ast = QPushButton("Inspect AST")
            btn_ast.setStyleSheet(
                "background-color: #e67e22; color: white; font-weight: bold;"
            )
            btn_ast.clicked.connect(self.run_ast_inspect)
            ast_ctrl.addWidget(btn_ast)
            ast_layout.addLayout(ast_ctrl)
            self.ast_output = QTextEdit()
            self.ast_output.setReadOnly(True)
            self.ast_output.setFont(QFont("Consolas", 10))
            self.ast_output.setStyleSheet(
                "background-color: #0d0d0d; color: #cfd8dc; padding: 8px;"
            )
            ast_layout.addWidget(self.ast_output)
            self.analysis_tabs.addTab(ast_page, "AST Inspection")

            # --- tree-sitter panel ---
            ts_page = QWidget()
            ts_layout = QVBoxLayout(ts_page)
            ts_ctrl = QHBoxLayout()
            ts_ctrl.addWidget(QLabel("File:"))
            self.txt_ts_file = QLineEdit()
            self.txt_ts_file.setPlaceholderText("/path/to/source")
            ts_ctrl.addWidget(self.txt_ts_file)
            btn_ts = QPushButton("Parse (tree-sitter)")
            btn_ts.setStyleSheet(
                "background-color: #1abc9c; color: white; font-weight: bold;"
            )
            btn_ts.clicked.connect(self.run_tree_sitter)
            ts_ctrl.addWidget(btn_ts)
            ts_layout.addLayout(ts_ctrl)
            self.ts_output = QTextEdit()
            self.ts_output.setReadOnly(True)
            self.ts_output.setFont(QFont("Consolas", 10))
            self.ts_output.setStyleSheet(
                "background-color: #0d0d0d; color: #cfd8dc; padding: 8px;"
            )
            ts_layout.addWidget(self.ts_output)
            self.analysis_tabs.addTab(ts_page, "tree-sitter")

            layout.addWidget(self.analysis_tabs)

        def browse_ast_file(self):
            path, _ = QFileDialog.getOpenFileName(
                self, "Select Python File", self.main.base_dir,
                "Python (*.py)"
            )
            if path:
                self.txt_ast_file.setText(path)
                self.txt_ts_file.setText(path)

        def run_ripgrep(self):
            pattern = self.txt_rg_pattern.text().strip()
            search_path = self.txt_rg_path.text().strip()
            if not pattern or not search_path:
                self.main.log("Pattern and path required.", "CodeAnalysis")
                return
            self.rg_output.clear()
            self.main.log(f"rg: searching '{pattern}' in {search_path}", "CodeAnalysis")
            def _run():
                env = enriched_env(self.main.base_bin_dir)
                try:
                    proc = subprocess.run(
                        ["rg", "--json", pattern, search_path],
                        capture_output=True, text=True, env=env, timeout=15,
                    )
                    lines = [l for l in proc.stdout.splitlines() if l.strip()]
                    html_parts = []
                    for line in lines[:200]:
                        try:
                            data = json.loads(line)
                            match_type = data.get("type", "match")
                            if match_type == "match":
                                d = data["data"]
                                html_parts.append(
                                    f'<span style="color:#2ecc71;">'
                                    f'{d["path"]["text"]}:{d["line_number"]}</span>'
                                    f': <span style="color:#e0e0e0;">'
                                    f'{d["lines"]["text"].strip()}</span>'
                                )
                            elif match_type == "summary":
                                stats = data["data"]["stats"]
                                html_parts.append(
                                    f'<span style="color:#f39c12;">'
                                    f'{stats["matched_lines"]} matches in '
                                    f'{stats["matched_files"]} files '
                                    f'({stats["elapsed"]["total"]}s)</span>'
                                )
                        except (json.JSONDecodeError, KeyError):
                            html_parts.append(line)
                    result = "<br/>".join(html_parts) if html_parts else "No results."
                    QTimer.singleShot(
                        0, lambda: self.rg_output.setHtml(result)
                    )
                except FileNotFoundError:
                    QTimer.singleShot(
                        0, lambda: self.rg_output.setPlainText(
                            "ripgrep not found. Install: pacman -S ripgrep"
                        )
                    )
                except Exception as exc:
                    QTimer.singleShot(
                        0, lambda: self.rg_output.setPlainText(f"Error: {exc}")
                    )
            threading.Thread(target=_run, daemon=True).start()

        def run_fd(self):
            pattern = self.txt_rg_pattern.text().strip()
            search_path = self.txt_rg_path.text().strip()
            if not search_path:
                self.main.log("Path required.", "CodeAnalysis")
                return
            self.rg_output.clear()
            self.main.log(f"fd: finding '{pattern}' in {search_path}", "CodeAnalysis")
            def _run():
                env = enriched_env(self.main.base_bin_dir)
                try:
                    args = ["fd", search_path] if not pattern else ["fd", pattern, search_path]
                    proc = subprocess.run(
                        args, capture_output=True, text=True, env=env, timeout=10,
                    )
                    lines = proc.stdout.strip().splitlines()[:200]
                    html = "<br/>".join(
                        f'<span style="color:#3498db;">{l}</span>' for l in lines
                    ) if lines else "No results."
                    QTimer.singleShot(0, lambda: self.rg_output.setHtml(html))
                except FileNotFoundError:
                    QTimer.singleShot(
                        0, lambda: self.rg_output.setPlainText(
                            "fd not found. Install: pacman -S fd"
                        )
                    )
                except Exception as exc:
                    QTimer.singleShot(
                        0, lambda: self.rg_output.setPlainText(f"Error: {exc}")
                    )
            threading.Thread(target=_run, daemon=True).start()

        def run_ast_inspect(self):
            file_path = self.txt_ast_file.text().strip()
            if not file_path or not os.path.exists(file_path):
                self.main.log("Valid Python file path required.", "CodeAnalysis")
                return
            import ast as ast_mod
            self.ast_output.clear()
            try:
                with open(file_path, encoding="utf-8") as f:
                    source = f.read()
                tree = ast_mod.parse(source)
                sections = []

                imports = [
                    f"import {n.name}" if not n.asname
                    else f"import {n.name} as {n.asname}"
                    for n in ast_mod.walk(tree)
                    if isinstance(n, (ast_mod.Import, ast_mod.ImportFrom))
                    and isinstance(n, ast_mod.Import)
                ]
                from_imports = [
                    f"from {n.module} import {', '.join(a.name for a in n.names)}"
                    for n in ast_mod.walk(tree)
                    if isinstance(n, ast_mod.ImportFrom) and n.module
                ]
                classes = [
                    (n.name, n.lineno, [
                        m.name for m in n.body
                        if isinstance(m, (ast_mod.FunctionDef, ast_mod.AsyncFunctionDef))
                    ])
                    for n in ast_mod.walk(tree)
                    if isinstance(n, ast_mod.ClassDef)
                ]
                functions = [
                    (n.name, n.lineno)
                    for n in ast_mod.walk(tree)
                    if isinstance(n, (ast_mod.FunctionDef, ast_mod.AsyncFunctionDef))
                    and not any(
                        isinstance(p, ast_mod.ClassDef)
                        for p in ast_mod.walk(tree)
                        if hasattr(p, 'body') and n in p.body
                    )
                ]

                if imports:
                    sections.append(
                        "<b>Imports:</b><br/>" +
                        "<br/>".join(f'<span style="color:#3498db;">{i}</span>' for i in imports)
                    )
                if from_imports:
                    sections.append(
                        "<b>From Imports:</b><br/>" +
                        "<br/>".join(f'<span style="color:#e67e22;">{i}</span>' for i in from_imports)
                    )
                if classes:
                    cls_lines = []
                    for cname, lineno, methods in classes:
                        methods_str = ", ".join(methods) if methods else "(none)"
                        cls_lines.append(
                            f'<span style="color:#2ecc71;">L{lineno}</span> '
                            f'<b>{cname}</b>: {methods_str}'
                        )
                    sections.append(
                        "<b>Classes:</b><br/>" + "<br/>".join(cls_lines)
                    )
                if functions:
                    fn_lines = [
                        f'<span style="color:#f39c12;">L{lineno}</span> {fname}'
                        for fname, lineno in functions
                    ]
                    sections.append(
                        "<b>Top-Level Functions:</b><br/>" + "<br/>".join(fn_lines)
                    )

                result = "<br/><br/>".join(sections) if sections else "Empty module."
                self.ast_output.setHtml(result)
                self.main.log(
                    f"AST: {len(classes)} classes, {len(functions)} functions, "
                    f"{len(imports)} imports in {os.path.basename(file_path)}",
                    "CodeAnalysis",
                )
            except SyntaxError as exc:
                self.ast_output.setPlainText(f"Syntax Error: {exc}")
            except Exception as exc:
                self.ast_output.setPlainText(f"Error: {exc}")

        def run_tree_sitter(self):
            file_path = self.txt_ts_file.text().strip()
            if not file_path or not os.path.exists(file_path):
                self.main.log("Valid file path required.", "CodeAnalysis")
                return
            self.ts_output.clear()
            try:
                import tree_sitter_api as ts_api  # noqa: F401
            except ImportError:
                try:
                    from tree_sitter import Language, Parser  # noqa: F401
                    ts_api = None  # noqa: F841
                except ImportError:
                    QTimer.singleShot(
                        0, lambda: self.ts_output.setPlainText(
                            "tree-sitter Python bindings not installed. "
                            "Install: uv tool install tree-sitter"
                        )
                    )
                    self.main.log(
                        "tree-sitter not available.", "CodeAnalysis"
                    )
                    return

            def _run():
                try:
                    from tree_sitter_languages import get_language, get_parser
                    ext_map = {
                        ".py": "python", ".js": "javascript",
                        ".ts": "typescript", ".rs": "rust",
                        ".go": "go", ".c": "c", ".cpp": "cpp",
                        ".java": "java", ".rb": "ruby",
                    }
                    ext = os.path.splitext(file_path)[1].lower()
                    lang_name = ext_map.get(ext)
                    if not lang_name:
                        QTimer.singleShot(
                            0, lambda: self.ts_output.setPlainText(
                                f"Unsupported file type: {ext}"
                            )
                        )
                        return
                    lang = get_language(lang_name)  # noqa: F841
                    parser = get_parser(lang_name)
                    with open(file_path, "rb") as f:
                        tree = parser.parse(f.read())
                    lines = []
                    def walk(node, depth=0):
                        prefix = "  " * depth
                        lines.append(
                            f"{prefix}{node.type} "
                            f"[{node.start_point[0]+1}:{node.start_point[1]}-"
                            f"{node.end_point[0]+1}:{node.end_point[1]}]"
                        )
                        for child in node.children:
                            walk(child, depth + 1)
                    walk(tree.root_node)
                    result = "<br/>".join(
                        f'<span style="color:#a5d6a7;">{l}</span>'
                        for l in lines[:500]
                    )
                    QTimer.singleShot(
                        0, lambda: self.ts_output.setHtml(result)
                    )
                    self.main.log(
                        f"tree-sitter: parsed {file_path} ({lang_name})",
                        "CodeAnalysis",
                    )
                except Exception as exc:
                    QTimer.singleShot(
                        0, lambda: self.ts_output.setPlainText(
                            f"tree-sitter error: {exc}"
                        )
                    )
            threading.Thread(target=_run, daemon=True).start()

else:
    CodeAnalysisTab = None
