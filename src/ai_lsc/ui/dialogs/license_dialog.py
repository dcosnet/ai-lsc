"""AI-LSC — License acceptance dialog.

Shown when the user tries to install a tool whose license has not yet
been accepted.  The dialog shows:

* The tool's name and tool_id
* The license name + SPDX ID
* A short summary of what the license permits / restricts
* A prominent disclaimer for source-available and proprietary licenses
* A link to the full license text (opens in the user's browser)
* Three buttons:
    - **Accept & Install** — record per-tool acceptance and proceed
    - **Accept all <license>** — add the license to the auto-approval
      registry (only enabled for OSI-approved licenses) and proceed
    - **Cancel** — abort the install

For tools on the SaaS blocklist (e.g. lm_studio), the dialog is never
shown — the gate raises :class:`LicenseBlocked` and the UI shows a
simple "blocked" message instead.
"""

from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ai_lsc.registry.licenses import Category, LicenseInfo

if TYPE_CHECKING:
    pass


class LicenseAcceptanceDialog(QDialog):
    """License acceptance dialog.

    Parameters
    ----------
    tool_id :
        The tool_id being installed.
    tool_name :
        Human-readable tool name.
    license_info :
        The :class:`~ai_lsc.registry.licenses.LicenseInfo` for the
        tool's license.
    parent :
        Parent widget (the main window).
    """

    accepted_individual = Signal(str, str)  # (tool_id, spdx)
    """Emitted when the user clicks 'Accept & Install'.  Payload is
    (tool_id, spdx)."""

    accepted_all_of_type = Signal(str, str)  # (tool_id, spdx)
    """Emitted when the user clicks 'Accept all <license>'.  Payload
    is (tool_id, spdx).  The caller should add the SPDX to the
    auto-approval registry AND record the per-tool acceptance."""

    def __init__(
        self,
        tool_id: str,
        tool_name: str,
        license_info: LicenseInfo,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.tool_id = tool_id
        self.tool_name = tool_name
        self.license_info = license_info

        self.setWindowTitle(f"License Acceptance — {tool_name}")
        self.setMinimumWidth(560)
        self.setMinimumHeight(440)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # ── Header ───────────────────────────────────────────────────
        header = QLabel(f"<b>{tool_name}</b>")
        header.setFont(QFont("Sans", 14, QFont.Bold))
        layout.addWidget(header)

        subheader = QLabel(
            f"tool_id: <code>{tool_id}</code> &nbsp;&nbsp; "
            f"license: <code>{license_info.spdx}</code> "
            f"({license_info.name})"
        )
        subheader.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(subheader)

        # ── Category banner ──────────────────────────────────────────
        category_label = {
            Category.OSI: "✓ OSI-Approved Open Source",
            Category.SOURCE_AVAILABLE: "⚠ Source-Available / Fair-Code",
            Category.PROPRIETARY: "⛔ Proprietary / ToS-Governed",
        }.get(license_info.category, license_info.category.value)

        category_color = {
            Category.OSI: "#16a34a",       # green
            Category.SOURCE_AVAILABLE: "#ea580c",  # orange
            Category.PROPRIETARY: "#dc2626",      # red
        }.get(license_info.category, "#64748b")

        category_banner = QLabel(category_label)
        category_banner.setStyleSheet(
            f"background: {category_color}22; "
            f"color: {category_color}; "
            f"padding: 6px 12px; border-radius: 4px; "
            f"font-weight: bold; border: 1px solid {category_color}66;"
        )
        layout.addWidget(category_banner)

        # ── Summary ──────────────────────────────────────────────────
        summary_label = QLabel("<b>License summary</b>")
        layout.addWidget(summary_label)
        summary = QTextEdit()
        summary.setReadOnly(True)
        summary.setPlainText(license_info.summary)
        summary.setMaximumHeight(80)
        summary.setStyleSheet(
            "background: #1e1e1e; border: 1px solid #444; "
            "border-radius: 4px; padding: 6px; color: #e0e0e0;"
        )
        layout.addWidget(summary)

        # ── Disclaimer (only for source-available / proprietary) ─────
        if license_info.disclaimer:
            disclaimer_label = QLabel("<b>Disclaimer</b>")
            disclaimer_label.setStyleSheet("color: #dc2626;")
            layout.addWidget(disclaimer_label)
            disclaimer = QTextEdit()
            disclaimer.setReadOnly(True)
            disclaimer.setPlainText(license_info.disclaimer)
            disclaimer.setMaximumHeight(100)
            disclaimer.setStyleSheet(
                "background: #fef2f2; border: 1px solid #fecaca; "
                "border-radius: 4px; padding: 6px; color: #991b1b;"
            )
            layout.addWidget(disclaimer)

        # ── Full text link ───────────────────────────────────────────
        if license_info.url:
            link_layout = QHBoxLayout()
            link_label = QLabel("Full license text:")
            link_layout.addWidget(link_label)
            link_btn = QPushButton("Open in browser ↗")
            link_btn.setCursor(Qt.PointingHandCursor)
            link_btn.setStyleSheet(
                "padding: 2px 8px; background: #2c3e50; color: #3498db; "
                "border: 1px solid #444; border-radius: 3px;"
            )
            link_btn.clicked.connect(
                lambda: webbrowser.open(license_info.url)
            )
            link_layout.addWidget(link_btn)
            link_layout.addStretch()
            link_widget = QWidget()
            link_widget.setLayout(link_layout)
            layout.addWidget(link_widget)

        # ── Confirmation checkbox (required for proprietary) ─────────
        self.confirm_checkbox = QCheckBox(
            "I have read and understand the license terms and any "
            "applicable Terms of Service, and I agree to be bound by them."
        )
        # For proprietary tools, the checkbox starts unchecked and
        # must be checked before Accept is enabled.  For OSI tools,
        # the checkbox starts checked (less friction — the license is
        # permissive) but can still be unchecked to Cancel.
        if license_info.category is Category.OSI:
            self.confirm_checkbox.setChecked(True)
        else:
            self.confirm_checkbox.setChecked(False)
        self.confirm_checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self.confirm_checkbox)

        layout.addStretch()

        # ── Button box ───────────────────────────────────────────────
        button_box = QDialogButtonBox()
        self.accept_btn = button_box.addButton(
            "Accept & Install", QDialogButtonBox.AcceptRole,
        )
        self.accept_btn.setStyleSheet(
            "padding: 8px 20px; background: #2563eb; color: white; "
            "border-radius: 4px; font-weight: bold;"
        )
        # "Accept all <license>" button — only for OSI licenses
        if license_info.category is Category.OSI:
            self.accept_all_btn = button_box.addButton(
                f"Accept all {license_info.spdx}", QDialogButtonBox.AcceptRole,
            )
            self.accept_all_btn.setStyleSheet(
                "padding: 8px 16px; background: #16a34a; color: white; "
                "border-radius: 4px;"
            )
            self.accept_all_btn.setToolTip(
                f"Add {license_info.spdx} to the auto-approval registry "
                f"so you won't be prompted for other {license_info.spdx} "
                f"tools in the future."
            )
            self.accept_all_btn.clicked.connect(self._on_accept_all)
        else:
            self.accept_all_btn = None

        cancel_btn = button_box.addButton("Cancel", QDialogButtonBox.RejectRole)
        cancel_btn.setStyleSheet(
            "padding: 8px 16px; background: #e2e8f0; color: #475569; "
            "border-radius: 4px;"
        )

        self.accept_btn.clicked.connect(self._on_accept_individual)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Initial button state
        self._on_checkbox_changed()

    # ── Handlers ─────────────────────────────────────────────────────

    def _on_checkbox_changed(self) -> None:
        """Enable Accept buttons only when the checkbox is checked
        (for non-OSI licenses)."""
        checked = self.confirm_checkbox.isChecked()
        self.accept_btn.setEnabled(checked)
        if self.accept_all_btn is not None:
            self.accept_all_btn.setEnabled(checked)

    def _on_accept_individual(self) -> None:
        self.accepted_individual.emit(self.tool_id, self.license_info.spdx)
        self.accept()

    def _on_accept_all(self) -> None:
        self.accepted_all_of_type.emit(self.tool_id, self.license_info.spdx)
        self.accept()


class LicenseBlockedDialog(QDialog):
    """Simple 'this tool is blocked' dialog shown when the gate
    returns ``status="blocked"``.

    No accept button — just an OK button to dismiss.
    """

    def __init__(
        self,
        tool_id: str,
        tool_name: str,
        reason: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Tool Blocked — {tool_name}")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QLabel(f"⛔ {tool_name} is blocked")
        header.setFont(QFont("Sans", 14, QFont.Bold))
        header.setStyleSheet("color: #dc2626;")
        layout.addWidget(header)

        subheader = QLabel(
            f"tool_id: <code>{tool_id}</code>"
        )
        subheader.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(subheader)

        reason_label = QLabel(reason)
        reason_label.setWordWrap(True)
        reason_label.setStyleSheet(
            "background: #fef2f2; border: 1px solid #fecaca; "
            "border-radius: 4px; padding: 8px; color: #991b1b;"
        )
        layout.addWidget(reason_label)

        suggestion = QLabel(
            "Use a local alternative (Ollama, vLLM, llama.cpp, LiteLLM, "
            "etc.) instead.  See CHANGES.md → 'SaaS-only tool blocklist' "
            "for the rationale."
        )
        suggestion.setWordWrap(True)
        suggestion.setStyleSheet("color: #475569; padding: 4px;")
        layout.addWidget(suggestion)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


__all__ = ["LicenseAcceptanceDialog", "LicenseBlockedDialog"]
