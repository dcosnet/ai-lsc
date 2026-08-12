"""LXC runtime manager -- Linux Container lifecycle operations.

Provides start / stop / status / create / destroy / attach operations
for LXC containers.  LXC is a lighter-weight alternative to Docker/Podman
that shares the host kernel without the containerd daemon overhead.

All ``subprocess`` calls are confined here -- UI code never touches LXC
commands directly.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any


# LXC container names must match ``[a-zA-Z0-9_.-]+``.  We use this regex
# at every public entry point so a malicious tool_id cannot escape the
# ``-n <name>`` slot.
_LXC_NAME_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")


def _validate_lxc_name(name: str) -> str:
    if not name or not _LXC_NAME_RE.fullmatch(name):
        raise ValueError(f"invalid LXC container name: {name!r}")
    if name in {".", ".."} or os.path.normpath(name) != name:
        raise ValueError(f"LXC name contains path-traversal segments: {name!r}")
    return name


def _validate_tool_id(tool_id: str) -> str:
    if not tool_id or not re.fullmatch(r"[A-Za-z0-9_.\-]+", tool_id):
        raise ValueError(f"invalid tool_id for LXC: {tool_id!r}")
    if tool_id in {".", ".."} or os.path.normpath(tool_id) != tool_id:
        raise ValueError(f"tool_id contains path-traversal segments: {tool_id!r}")
    return tool_id


class LxcManager:
    """Manages LXC container lifecycle via the ``lxc`` CLI.

    Parameters
    ----------
    tools_root :
        Base directory for tool installations (used as container
        mount source).
    logs_root :
        Directory for container log files.
    lxc_profile :
        Default LXC profile name (``"default"`` unless overridden).
    """

    def __init__(
        self,
        tools_root: str,
        logs_root: str,
        lxc_profile: str = "default",
    ) -> None:
        self.tools_root = tools_root
        self.logs_root = logs_root
        self.lxc_profile = lxc_profile

    # ── Container lifecycle ──────────────────────────────────────────

    def create(
        self,
        container_name: str,
        image: str = "ubuntu:22.04",
        config: dict[str, Any] | None = None,
    ) -> str:
        """Create a new LXC container.

        Parameters
        ----------
        container_name :
            Name for the new container.
        image :
            LXC image template (e.g. ``"ubuntu:22.04"``,
            ``"alpine"``, ``"archlinux"``).
        config :
            Optional dict of LXC config key-value pairs that are
            written to the container's local config file after
            creation.

        Returns
        -------
        Description of what was done.
        """
        _validate_lxc_name(container_name)
        cmd = [
            "lxc-create",
            "-n", container_name,
            "-t", image.split(":")[0],
            "--", image.split(":")[1] if ":" in image else "",
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        except FileNotFoundError:
            return self._install_hint("lxc-create")

        # Apply custom config if provided
        if config:
            self._apply_config(container_name, config)

        return f"LXC container '{container_name}' created from {image}"

    def start(self, container_name: str) -> str:
        """Start an LXC container."""
        cmd = ["lxc-start", "-n", container_name, "-d"]  # -d = daemonize
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        except FileNotFoundError:
            return self._install_hint("lxc-start")
        except subprocess.CalledProcessError as e:
            return f"LXC start failed: {e.stderr.strip()}"
        return f"LXC container '{container_name}' started"

    def stop(self, container_name: str) -> str:
        """Stop a running LXC container."""
        cmd = ["lxc-stop", "-n", container_name, "-t", "5"]  # 5s timeout
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        except FileNotFoundError:
            return self._install_hint("lxc-stop")
        except subprocess.CalledProcessError as e:
            return f"LXC stop failed: {e.stderr.strip()}"
        return f"LXC container '{container_name}' stopped"

    def destroy(self, container_name: str) -> str:
        """Destroy (remove) an LXC container."""
        cmd = ["lxc-destroy", "-n", container_name]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        except FileNotFoundError:
            return self._install_hint("lxc-destroy")
        except subprocess.CalledProcessError as e:
            return f"LXC destroy failed: {e.stderr.strip()}"
        return f"LXC container '{container_name}' destroyed"

    def freeze(self, container_name: str) -> str:
        """Freeze (pause) a running container without stopping it."""
        cmd = ["lxc-freeze", "-n", container_name]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            return f"LXC freeze failed: {getattr(e, 'stderr', str(e))}"
        return f"LXC container '{container_name}' frozen"

    def unfreeze(self, container_name: str) -> str:
        """Unfreeze (resume) a paused container."""
        cmd = ["lxc-unfreeze", "-n", container_name]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            return f"LXC unfreeze failed: {getattr(e, 'stderr', str(e))}"
        return f"LXC container '{container_name}' resumed"

    # ── Status / inspection ───────────────────────────────────────────

    def is_running(self, container_name: str) -> bool:
        """Check if a container is currently running."""
        cmd = ["lxc-info", "-n", container_name, "-s"]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5
            )
            return "RUNNING" in result.stdout.upper()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_state(self, container_name: str) -> str:
        """Return the container state (RUNNING, STOPPED, FROZEN)."""
        cmd = ["lxc-info", "-n", container_name, "-s"]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5
            )
            for state in ("RUNNING", "STOPPED", "FROZEN"):
                if state in result.stdout.upper():
                    return state
            return "UNKNOWN"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return "UNKNOWN"

    def list_containers(self, running_only: bool = False) -> list[str]:
        """List container names.

        Parameters
        ----------
        running_only :
            If ``True`` only return running containers.

        Returns
        -------
        List of container name strings.
        """
        cmd = ["lxc-ls"]
        if running_only:
            cmd.append("--running")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5
            )
            return [
                name.strip() for name in result.stdout.strip().splitlines()
                if name.strip()
            ]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []

    # ── Execution ────────────────────────────────────────────────────

    def attach_exec(
        self,
        container_name: str,
        command: str = "/bin/bash",
    ) -> str:
        """Execute a command inside a running container (non-interactive)."""
        _validate_lxc_name(container_name)
        # H-12: use shlex.split so quoted arguments survive.  The previous
        # `command.split()` mangled inputs like `echo 'hello world'` into
        # ['echo', '"hello', 'world"'].
        argv = shlex.split(command) or ["/bin/bash"]
        cmd = ["lxc-attach", "-n", container_name, "--", *argv]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            return f"LXC attach failed: {getattr(e, 'stderr', str(e))}"
        return f"Executed in '{container_name}': {command}"

    def launch_cli(
        self,
        container_name: str,
    ) -> str:
        """Open an interactive terminal inside the container.

        Launches an x-terminal-emulator with ``lxc-attach``.
        """
        import shutil
        term = shutil.which("x-terminal-emulator") or shutil.which("gnome-terminal") or shutil.which("konsole")
        if not term:
            return "No terminal emulator found for LXC CLI attach."

        subprocess.Popen(
            [term, "-e", "bash", "-c",
             f"lxc-attach -n {container_name} --clear-env -- "
             f"env TERM=xterm-256color /bin/bash"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return f"Interactive terminal opened for '{container_name}'"

    # ── Config helpers ──────────────────────────────────────────────

    def _apply_config(
        self,
        container_name: str,
        config: dict[str, Any],
    ) -> None:
        """Append config key-value pairs to a container's config file."""
        _validate_lxc_name(container_name)
        config_path = Path("/var/lib/lxc") / container_name / "config"
        if not config_path.exists():
            return

        # M-21: build the formatted config lines via comprehension.
        lines = [
            (f"lxc.{key} = {','.join(str(v) for v in value)}"
             if isinstance(value, (list, tuple))
             else f"lxc.{key} = {value}")
            for key, value in config.items()
        ]

        # M-05: explicit encoding + flush + fsync so a crash mid-write
        # cannot corrupt the LXC config file.
        with open(config_path, "a", encoding="utf-8") as f:
            f.write("\n# ai-lsc generated\n")
            for line in lines:
                f.write(f"{line}\n")
            f.flush()
            os.fsync(f.fileno())

    @staticmethod
    def _install_hint(cmd: str) -> str:
        # M-39: don't assume Arch's pacman; the app advertises multi-distro
        # support, so keep the hint generic.
        return (
            f"LXC not installed. Install the `lxc` package for your "
            f"distribution (e.g. `sudo pacman -S lxc` on Arch, "
            f"`sudo apt-get install lxc` on Debian/Ubuntu, "
            f"`sudo dnf install lxc` on Fedora).\n"
            f"Missing command: {cmd}"
        )

    # ── Service delegation (mirrors TmuxManager interface) ───────────

    def launch_service(
        self,
        tool_id: str,
        command: str,
        log_file: str = "",
        dtach_bin: str | None = None,
        base_bin_dir: str = "",
    ) -> str:
        """Start a tool as an LXC container service.

        Creates the container if it does not exist, starts it,
        and runs the tool command inside.  The container is named
        ``ai-lsc-<tool_id>`` for consistency.

        Returns a description of what was done.
        """
        _validate_tool_id(tool_id)
        container_name = f"ai-lsc-{tool_id}"

        if not self.is_running(container_name):
            if container_name not in self.list_containers():
                self.create(
                    container_name,
                    image="ubuntu:22.04",
                    config={
                        "mount.auto": f"{self.tools_root} opt none bind 0 0",
                    },
                )
            self.start(container_name)

        # Run the tool command inside the container
        if command:
            self.attach_exec(container_name, command)

        return f"Tool {tool_id} running in LXC container '{container_name}'"

    def stop_service(self, tool_id: str) -> str:
        """Stop the LXC container for a tool."""
        _validate_tool_id(tool_id)
        container_name = f"ai-lsc-{tool_id}"
        self.stop(container_name)
        return f"LXC container '{container_name}' stopped for {tool_id}"
