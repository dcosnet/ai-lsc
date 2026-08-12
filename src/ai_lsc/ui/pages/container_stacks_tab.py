"""ContainerStacksTab widget — lists exported stack files.

Displays available stack snapshots and provides export buttons for
Podman Compose and Docker Compose outputs.
"""

import os

try:
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QListWidget,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

if _HAS_QT:

    class ContainerStacksTab(QWidget):
        """Lists exported stack files and provides export buttons."""

        def __init__(self, main_window):
            super().__init__()
            self.main = main_window
            layout = QVBoxLayout(self)

            header = QHBoxLayout()
            header.addWidget(QLabel("<b>Stack Execution Snapshots & Images</b>"))
            header.addStretch()

            btn_podman = QPushButton("Export -> Podman Compose")
            btn_podman.setStyleSheet("background-color: #8e44ad;")
            btn_podman.clicked.connect(
                lambda: self.main.finalize_stack_export("podman")
            )
            header.addWidget(btn_podman)

            btn_docker = QPushButton("Export -> Docker Compose")
            btn_docker.setStyleSheet("background-color: #2980b9;")
            btn_docker.clicked.connect(
                lambda: self.main.finalize_stack_export("docker")
            )
            header.addWidget(btn_docker)

            btn_lxc = QPushButton("Export -> LXC")
            btn_lxc.setStyleSheet("background-color: #16a085;")
            btn_lxc.clicked.connect(
                lambda: self.main.finalize_stack_export("lxc")
            )
            header.addWidget(btn_lxc)

            btn_firecracker = QPushButton("Export -> Firecracker")
            btn_firecracker.setStyleSheet("background-color: #c0392b;")
            btn_firecracker.clicked.connect(
                lambda: self.main.finalize_stack_export("firecracker")
            )
            header.addWidget(btn_firecracker)
            layout.addLayout(header)

            self.file_list = QListWidget()
            layout.addWidget(self.file_list)
            self.refresh()

        def refresh(self):
            self.file_list.clear()
            if not os.path.exists(self.main.exports_root):
                return
            for fname in sorted(os.listdir(self.main.exports_root)):
                # Compose YAML, JSON specs, and launch scripts (.sh) for
                # the LXC and Firecracker backends.
                if fname.endswith((".yml", ".yaml", ".json", ".sh")):
                    self.file_list.addItem(fname)
                # Also surface subdirectories that hold per-container /
                # per-VM configs (lxc/, firecracker/).
            for fname in sorted(os.listdir(self.main.exports_root)):
                fpath = os.path.join(self.main.exports_root, fname)
                if os.path.isdir(fpath):
                    self.file_list.addItem(f"{fname}/ (directory)")

else:
    ContainerStacksTab = None
