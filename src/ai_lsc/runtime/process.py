"""Generic process manager.

Handles desktop-app launching, process killing via ``pkill``, and
bare ``subprocess.Popen`` calls for non-tmux/non-systemd tools.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import threading
from collections.abc import Iterable

# Terminal emulator candidates, ordered by preference.
_TERMINALS = [
    "xterm", "konsole", "gnome-terminal", "xfce4-terminal",
    "lxterminal", "alacritty", "kitty", "wezterm",
]


def detect_terminal() -> str:
    """Return the first available terminal emulator on the system."""
    return next((t for t in _TERMINALS if shutil.which(t)), "xterm")


def _to_arg_list(command: str | list[str]) -> list[str]:
    """Coerce a registry command into a safe argv list.

    Accepts either a pre-split argv list (preferred) or a single shell-style
    string (which is split with :func:`shlex.split`, never passed to a shell).
    """
    if isinstance(command, (list, tuple)):
        return [str(c) for c in command]
    return shlex.split(command)


class ProcessManager:
    """Launch and terminate generic (desktop / CLI) processes.

    All launched processes are tracked in :attr:`_launched` so they can be
    polled / reaped periodically, preventing zombie accumulation in a
    long-lived GUI process.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._launched: list[subprocess.Popen] = []

    def launch_desktop(self, command: str | list[str]) -> None:
        """Fire-and-forget launch of a desktop command."""
        argv = _to_arg_list(command)
        if not argv:
            raise ValueError("launch_desktop received an empty command")
        with self._lock:
            self._launched.append(subprocess.Popen(argv))

    def launch_terminal(self, command: str | list[str], env: dict[str, str] | None = None) -> None:
        """Open *command* inside a new terminal emulator window."""
        term = detect_terminal()
        # xterm, alacritty, kitty, wezterm use -e; others use --
        sep = "-e" if term in ("xterm", "alacritty", "kitty", "wezterm") else "--"
        cmd_str = shlex.join(_to_arg_list(command)) if isinstance(command, (list, tuple)) else command
        argv = [term, sep, "bash", "-c", cmd_str]
        with self._lock:
            self._launched.append(subprocess.Popen(argv, env=env))

    def kill_by_name(self, search_term: str) -> None:
        """Send SIGTERM to all processes matching *search_term*."""
        subprocess.run(
            ["pkill", "-f", search_term],
            timeout=5,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    def reap(self) -> None:
        """Poll and drop finished children; call periodically from the GUI."""
        with self._lock:
            still_alive: list[subprocess.Popen] = []
            for proc in self._launched:
                if proc.poll() is None:
                    still_alive.append(proc)
            self._launched = still_alive

    def shutdown(self, timeout: float = 2.0) -> None:
        """Terminate every still-running child on application quit."""
        with self._lock:
            for proc in self._launched:
                if proc.poll() is None:
                    proc.terminate()
            for proc in self._launched:
                try:
                    proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    proc.kill()
            self._launched.clear()

    def __del__(self) -> None:  # noqa: D401 - best-effort cleanup
        try:
            self.shutdown()
        except Exception:
            pass


def safe_env(base: dict[str, str] | None = None, **overrides: str) -> dict[str, str]:
    """Build a clean environment for child processes.

    Merges the current ``os.environ`` with any explicit *base* dict and
    keyword overrides.  Values are coerced to ``str``.
    """
    env = dict(os.environ)
    if base:
        env.update(base)
    env.update({k: str(v) for k, v in overrides.items()})
    return env


__all__ = [
    "ProcessManager",
    "detect_terminal",
    "safe_env",
    "_to_arg_list",
    "_TERMINALS",
]
