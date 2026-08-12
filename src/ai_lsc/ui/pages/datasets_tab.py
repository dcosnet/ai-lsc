"""DatasetsTab widget — managed knowledge repositories browser.

Provides a table view of files under ``datasets/raw`` with an import
dialog and stub vectorize buttons per row.
"""

import os
import shutil

try:
    from PySide6.QtWidgets import (
        QFileDialog,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

if _HAS_QT:

    class DatasetsTab(QWidget):
        """Managed knowledge repositories browser."""

        def __init__(self, main_window):
            super().__init__()
            self.main = main_window
            layout = QVBoxLayout(self)

            header = QHBoxLayout()
            header.addWidget(QLabel(
                "<b>Managed Knowledge Repositories (datasets/raw)</b>"
            ))
            header.addStretch()
            btn_add = QPushButton("+ Ingest Knowledge File")
            btn_add.setStyleSheet("background-color: #009688; color: white;")
            btn_add.clicked.connect(self.import_asset)
            header.addWidget(btn_add)
            layout.addLayout(header)

            self.table = QTableWidget(0, 3)
            self.table.setHorizontalHeaderLabels(
                ["Filename", "Size (MB)", "Action"]
            )
            self.table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.Stretch
            )
            layout.addWidget(self.table)
            self.refresh_table()

        @property
        def raw_dir(self) -> str:
            d = os.path.join(self.main.datasets_root, "raw")
            os.makedirs(d, exist_ok=True)
            return d

        def import_asset(self):
            path, _ = QFileDialog.getOpenFileName(
                self, "Select Asset", "",
                "Data (*.txt *.csv *.jsonl *.md *.pdf)",
            )
            if not path:
                return
            dest = os.path.join(self.raw_dir, os.path.basename(path))
            shutil.copy(path, dest)
            self.main.log(f"Ingested: {os.path.basename(path)}", "Data")
            self.refresh_table()

        def refresh_table(self):
            self.table.setRowCount(0)
            if not os.path.exists(self.raw_dir):
                return
            for f in sorted(os.listdir(self.raw_dir)):
                p = os.path.join(self.raw_dir, f)
                if not os.path.isfile(p):
                    continue
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(f))
                self.table.setItem(
                    row, 1,
                    QTableWidgetItem(f"{os.path.getsize(p) / (1024 * 1024):.2f} MB"),
                )
                btn = QPushButton("Vectorize")
                # UX-09: connect the button; for now log a placeholder
                # since the actual vectorization pipeline is deferred.
                btn.setEnabled(False)
                btn.setToolTip("Vectorization pipeline not yet implemented")
                self.table.setCellWidget(row, 2, btn)

else:
    DatasetsTab = None
