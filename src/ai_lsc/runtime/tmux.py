"""Tmux session/window manager.

Wraps all ``tmux`` CLI interactions: session creation, window
management, command sending, and live-window querying.

Every public method returns a value or raises -- no UI imports.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path

# Valid tmux window / session name characters.  Anything outside this
# set is rejected to prevent tmux-command injection.
_NAME_RE = re.compile(r"^[A-Za-z0-9_.:@\-]+$")


def _validate_name(name: str, *, what: str = "name") -> None:
    """Reject tmux target names that could break out of the argument slot."""
    if not name or not _NAME_RE.fullmatch(name):
        raise ValueError(f"invalid tmux {what}: {name!r}")


def _socket_path_for(tool_id: str) -> str:
    """Return a safe, user-scoped socket path for a tmux service."""
    runtime_dir = os.environ.get(
        "XDG_RUNTIME_DIR",
        f"/tmp/ai-lsc-{os.getuid()}",
    )
    base = Path(runtime_dir) / "ai-lsc"
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    safe_id = re.sub(r"[^A-Za-z0-9_.\-]", "_", tool_id)
    return str(base / f"{safe_id}.sock")


class TmuxManager:
    """Manages tmux sessions and windows for service isolation."""

    SESSION = f"ai_lsc_{os.getuid()}"

    def __init__(self, env: dict[str, str] | None = None) -> None:
        self.env = env

    # -- session lifecycle ------------------------------------------------

    def ensure_session(self) -> None:
        """Create the master session if it does not already exist."""
        _validate_name(self.SESSION, what="session name")
        has = subprocess.run(
            ["tmux", "has-session", "-t", self.SESSION],
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if has.returncode != 0:
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", self.SESSION, "-n", "Master"],
                stderr=subprocess.DEVNULL,
                check=False,
            )

    def window_exists(self, window_name: str) -> bool:
        """Check if a named window exists in the session."""
        _validate_name(window_name, what="window name")
        listing = subprocess.run(
            ["tmux", "list-windows", "-t", self.SESSION, "-F",
             "#{window_name}"],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            text=True,
            check=False,
        )
        if listing.returncode != 0:
            return False
        # SE-07: exact match instead of substring
        return window_name in listing.stdout.splitlines()

    def kill_window(self, window_name: str) -> None:
        """Safely kill a window (ignores errors if missing)."""
        _validate_name(window_name, what="window name")
        subprocess.run(
            ["tmux", "kill-window", "-t", f"{self.SESSION}:{window_name}"],
            stderr=subprocess.DEVNULL,
            check=False,
        )

    def create_window(self, window_name: str) -> None:
        """Create a new detached window inside the session.

        Retries up to 5 times with a short sleep when tmux reports
        an index collision (happens when concurrent launches race).
        """
        import time

        _validate_name(window_name, what="window name")
        for attempt in range(5):
            proc = subprocess.run(
                [
                    "tmux", "new-window",
                    "-t", self.SESSION,
                    "-n", window_name,
                    "-d",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0:
                return
            # If window already exists with this name, that's fine too
            if self.window_exists(window_name):
                return
            # Index collision — wait and retry
            if "index" in proc.stderr and "in use" in proc.stderr:
                time.sleep(0.1 * (attempt + 1))
                continue
            break  # some other error, stop retrying

    def send_command(
        self,
        window_name: str,
        command: str,
        extra_env: str = "",
    ) -> None:
        """Send a command string to a window, optionally prepending env."""
        _validate_name(window_name, what="window name")
        payload = f"{extra_env} {command}".strip()
        # tmux send-keys receives the payload as a single argv element;
        # no shell is involved, so quoting is preserved.
        subprocess.run(
            [
                "tmux", "send-keys",
                "-t", f"{self.SESSION}:{window_name}",
                payload, "C-m",
            ],
            stderr=subprocess.DEVNULL,
            check=False,
        )

    # -- high-level service lifecycle -------------------------------------

    def launch_service(
        self,
        tool_id: str,
        command: str,
        log_file: str,
        dtach_bin: str | None = None,
        base_bin_dir: str = "",
    ) -> None:
        """Isolate a service in its own tmux window (optionally via dtach).

        Parameters
        ----------
        tool_id:
            Service identifier used as the window name.
        command:
            Shell command to run inside the window.
        log_file:
            Path where stdout/stderr should be redirected.
        dtach_bin:
            Path to dtach binary for persistent attach/detach.
        base_bin_dir:
            PATH colon-separated string to prepend.
        """
        _validate_name(tool_id, what="tool_id")
        window_name = f"{self.SESSION}::{tool_id}"
        track_cmd = f"({command}) > {shlex.quote(log_file)} 2>&1"

        wrapped = track_cmd
        if dtach_bin:
            socket_path = _socket_path_for(tool_id)
            wrapped = f"{shlex.quote(dtach_bin)} -n {shlex.quote(socket_path)} bash -c {shlex.quote(track_cmd)}"

        self.ensure_session()
        self.kill_window(window_name)
        self.create_window(window_name)

        env_exports = ""
        if base_bin_dir:
            env_exports = f"export PATH={shlex.quote(base_bin_dir)}:$PATH; "

        self.send_command(window_name, wrapped, extra_env=env_exports)

    def stop_service(self, tool_id: str) -> None:
        """Kill the tmux window for a service."""
        _validate_name(tool_id, what="tool_id")
        window_name = f"{self.SESSION}::{tool_id}"
        self.kill_window(window_name)

    def is_running(self, tool_id: str) -> bool:
        """Check whether the tmux window for *tool_id* is live."""
        _validate_name(tool_id, what="tool_id")
        return self.window_exists(f"{self.SESSION}::{tool_id}")

    def attach_cli(self, tool_id: str) -> str:
        """Return a shell fragment that attaches to the service window."""
        _validate_name(tool_id, what="tool_id")
        target = shlex.quote(f"{self.SESSION}:{self.SESSION}::{tool_id}")
        return f"tmux attach -t {target} || "


__all__ = ["TmuxManager", "_validate_name", "_socket_path_for"]
