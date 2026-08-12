"""SettingsPage widget — ecosystem system configurations and hardening policies.

Presents a set of security-policy checkboxes in a grouped layout.
"""

try:
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QCheckBox,
        QGridLayout,
        QGroupBox,
        QLabel,
        QVBoxLayout,
        QWidget,
    )
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

if _HAS_QT:

    # UX-07: v4.0 notice for non-functional settings
    _V40_NOTICE_HTML = (
        '<p style="color: #e67e22; padding: 4px 0;">'
        '<b>Note:</b> The settings below are placeholders scheduled for '
        'implementation in v4.0. They are not yet connected to any backend.</p>'
    )

    class SettingsPage(QWidget):
        """Ecosystem system configurations and core hardening policies."""

        def __init__(self, main_window):
            super().__init__()
            self.main = main_window
            layout = QVBoxLayout(self)

            lbl = QLabel(
                "<b>Ecosystem System Configurations & Core Hardening Policies</b>"
            )
            lbl.setFont(QFont("Segoe UI", 14))
            layout.addWidget(lbl)

            box = QGroupBox("Bare-Metal Operational Environment Security Rules")
            box_layout = QGridLayout(box)

            policies = [
                "Enforce Strict Clean-Room Local Sandbox Isolation Rules",
                "Disable External Network Cloud Access Topology Check Handlers",
                "Auto-Rollback Infrastructure Layers on Failure Mismatches",
                "Inject Kernel Hardened Telemetry Constraints",
                "Enable Zero-Drift Registry Integrity Verification",
                "Require Explicit Approval for Container Network Bridges",
            ]
            for idx, policy_text in enumerate(policies):
                box_layout.addWidget(QCheckBox(policy_text), idx, 0)

            layout.addWidget(box)
            layout.addStretch()

else:
    SettingsPage = None