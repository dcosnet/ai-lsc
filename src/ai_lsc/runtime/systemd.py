"""Systemd service manager.

Wraps ``systemctl`` calls for tools that launch as system services.
"""

from __future__ import annotations

import subprocess

from ai_lsc.runtime.process import detect_terminal


class SystemdManager:
    """Start, stop, and query systemd services."""

    def start(self, service_cmd: str) -> None:
        """Enable + start a systemd service via a terminal emulator."""
        term = detect_terminal()
        sep = "-e" if term in ("xterm", "alacritty", "kitty", "wezterm") else "--"
        subprocess.Popen(
            [term, sep, "sudo", "systemctl", "start", service_cmd],
            start_new_session=True,
        )

    def stop(self, service_cmd: str) -> None:
        """Stop a systemd service via a terminal emulator."""
        term = detect_terminal()
        sep = "-e" if term in ("xterm", "alacritty", "kitty", "wezterm") else "--"
        subprocess.Popen(
            [term, sep, "sudo", "systemctl", "stop", service_cmd],
            start_new_session=True,
        )

    def is_active(self, service_cmd: str) -> bool:
        """Return ``True`` if the service reports 'active'."""
        return (
            subprocess.run(
                ["systemctl", "is-active", service_cmd],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            == "active"
        )
