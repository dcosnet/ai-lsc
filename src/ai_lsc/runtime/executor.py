"""Runtime executor -- the single entry point for all process management.

UI code calls ``RuntimeExecutor`` methods instead of touching
``subprocess`` directly.  This is the *only* class the UI should
import from ``ai_lsc.runtime``.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from ai_lsc.runtime.installer import InstallerManager
from ai_lsc.runtime.lxc import LxcManager
from ai_lsc.runtime.process import ProcessManager
from ai_lsc.runtime.status import StatusChecker
from ai_lsc.runtime.systemd import SystemdManager
from ai_lsc.runtime.tmux import TmuxManager
from ai_lsc.utils.process import enriched_env


# H-01 / H-11: reject tool_id values that could break out of file paths,
# tmux window names, or LXC container names.  Keep this conservative and
# limited to characters actually used by the registry.
_TOOL_ID_RE = re.compile(r"^[A-Za-z0-9_.:\-]+$")


def _validate_tool_id(tool_id: str) -> str:
    """Raise ``ValueError`` if *tool_id* is unsafe to use as a path/window name."""
    if not tool_id or not _TOOL_ID_RE.fullmatch(tool_id):
        raise ValueError(f"invalid tool_id: {tool_id!r}")
    # Also reject `.`, `..`, `foo/..`, etc. — these pass the regex but
    # escape the intended tools_root/<tool_id>/ directory when joined.
    if tool_id in {".", ".."} or os.path.normpath(tool_id) != tool_id:
        raise ValueError(f"tool_id contains path-traversal segments: {tool_id!r}")
    return tool_id


def _validate_port(port: int | str) -> int:
    """Coerce *port* to ``int`` and validate the 1..65535 range."""
    try:
        port_num = int(port)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid port: {port!r}") from exc
    if not 1 <= port_num <= 65535:
        raise ValueError(f"port out of range 1..65535: {port_num}")
    return port_num


class RuntimeExecutor:
    """Unified runtime facade for UI-layer delegation.

    Parameters
    ----------
    tools_root:
        Base directory for tool installations.
    models_root:
        Base directory for model files.
    workspaces_root:
        Base directory for workspace data.
    logs_root:
        Base directory for service log files.
    base_bin_dir:
        Colon-separated PATH string to prepend to all commands.
    dtach_bin:
        Path to the ``dtach`` binary (or ``None``).
    """

    def __init__(
        self,
        tools_root: str,
        models_root: str,
        workspaces_root: str,
        logs_root: str,
        base_bin_dir: str = "",
        dtach_bin: str | None = None,
        license_gate: Any = None,
    ) -> None:
        self.tools_root = tools_root
        self.models_root = models_root
        self.workspaces_root = workspaces_root
        self.logs_root = logs_root
        self.base_bin_dir = base_bin_dir
        self.dtach_bin = dtach_bin
        self.license_gate = license_gate

        self._tmux = TmuxManager()
        self._systemd = SystemdManager()
        self._lxc = LxcManager(tools_root, logs_root)
        self._process = ProcessManager()
        self._installer = InstallerManager(
            tools_root, base_bin_dir,
            license_gate=license_gate,
        )
        self._status = StatusChecker(tmux=self._tmux, systemd=self._systemd)

    # -- context formatting -----------------------------------------------

    def format_context(
        self,
        port: str = "",
        model_arg: str = "",
    ) -> dict[str, str]:
        """Build the ``{placeholders}`` dict used by launcher commands."""
        from ai_lsc.constants import BASE_DIR
        return {
            "base_dir": BASE_DIR,
            "tools_root": self.tools_root,
            "models_root": self.models_root,
            "workspaces_root": self.workspaces_root,
            "port": port,
            "model_arg": model_arg,
        }

    # -- service lifecycle -----------------------------------------------

    def start_service(
        self,
        tool_id: str,
        launcher_cmd: str,
        launcher_type: str,
        port: str = "",
        model_arg: str = "",
    ) -> str:
        """Start a service via the appropriate backend.

        Returns a description of what was done.
        """
        _validate_tool_id(tool_id)
        if port:
            _validate_port(port)
        ctx = self.format_context(port=port, model_arg=model_arg)
        final_cmd = launcher_cmd.format(**ctx)

        if launcher_type == "systemd":
            self._systemd.start(final_cmd)
            return f"Systemd activated for {tool_id}"

        if launcher_type == "desktop":
            self._process.launch_desktop(final_cmd)
            return f"Desktop spawned for {tool_id}"

        if launcher_type == "lxc":
            log_file = str(Path(self.logs_root) / f"{tool_id}.log")
            return self._lxc.launch_service(
                tool_id=tool_id,
                command=final_cmd,
                log_file=log_file,
                dtach_bin=self.dtach_bin,
                base_bin_dir=self.base_bin_dir,
            )

        # default: tmux (with optional dtach)
        log_file = str(Path(self.logs_root) / f"{tool_id}.log")
        self._tmux.launch_service(
            tool_id=tool_id,
            command=final_cmd,
            log_file=log_file,
            dtach_bin=self.dtach_bin,
            base_bin_dir=self.base_bin_dir,
        )
        return f"Component {tool_id} isolated in Tmux."

    def stop_service(
        self,
        tool_id: str,
        launcher_type: str,
        launcher_cmd: str = "",
        search_term: str = "",
    ) -> str:
        """Stop a service via the appropriate backend.

        Returns a description of what was done.
        """
        _validate_tool_id(tool_id)

        if launcher_type == "systemd":
            self._systemd.stop(launcher_cmd)
            return f"Systemd stop signal sent for {tool_id}"

        if launcher_type == "tmux":
            self._tmux.stop_service(tool_id)
            return f"Tmux window killed for {tool_id}"

        if launcher_type == "lxc":
            return self._lxc.stop_service(tool_id)

        # default: pkill
        self._process.kill_by_name(search_term)

        return f"Termination signal sent to {tool_id}."

    def is_service_running(
        self,
        launcher_type: str,
        tool_id: str = "",
        service_cmd: str = "",
        search_term: str = "",
    ) -> bool:
        """Check whether a service is currently live."""
        if launcher_type == "lxc":
            return self._lxc.is_running(f"ai-lsc-{tool_id}")
        return self._status.is_running(
            launcher_type=launcher_type,
            tool_id=tool_id,
            service_cmd=service_cmd,
            search_term=search_term,
        )

    # -- installation ----------------------------------------------------

    def install_tool(
        self,
        inst_type: str,
        pkg: str,
        cmd: str = "",
        tool_id: str = "",
        ctx: dict[str, str] | None = None,
        force: bool = False,
        post_install: str | None = None,
        env_overrides: dict[str, str] | None = None,
        filesystem: dict[str, str] | None = None,
        license_spdx: str | None = None,
    ) -> str:
        """Dispatch tool installation to the correct installer.

        If *tool_id* is provided, the installer uses preflight detection
        and routes artifacts to ``tools_root/<tool_id>/``.
        If *force* is True, skips preflight and installs unconditionally.

        *post_install* runs a shell command inside ``tools_root/<tool_id>``
        after clone (e.g. ``pip install -r requirements.txt``, ``make``).

        *env_overrides* remaps upstream environment variables (HF_HOME,
        TRANSFORMERS_CACHE, etc.) into ``/mnt/AI/`` paths.

        *filesystem* declares per-tool path mappings for the verification
        checklist (install, config, cache, logs).

        *license_spdx* is forwarded to the InstallerManager's license
        gate (if one was provided at construction time).  If the gate
        returns ``blocked`` or ``needs_acceptance``, the appropriate
        ``LicenseBlocked`` / ``LicenseAcceptanceRequired`` exception is
        raised before any subprocess call.

        Returns a description of the result.
        """
        if tool_id:
            return self._installer.install_with_preflight(
                tool_id=tool_id,
                inst_type=inst_type,
                pkg=pkg,
                cmd=cmd,
                ctx=ctx,
                force=force,
                post_install=post_install,
                env_overrides=env_overrides,
                license_spdx=license_spdx,
            )
        return self._installer.run(
            inst_type=inst_type,
            pkg=pkg,
            cmd=cmd,
            ctx=ctx,
            tool_id=tool_id,
            post_install=post_install,
            env_overrides=env_overrides,
            license_spdx=license_spdx,
        )

    # -- verification ---------------------------------------------------

    def verify_tool(
        self,
        tool_id: str,
        inst_type: str,
        pkg: str,
        cmd: str = "",
        filesystem: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Run the installation compliance checklist for a tool.

        Returns a dict with ``score``, ``checks``, and ``install_location``.
        """
        return self._installer.verify(
            tool_id=tool_id,
            inst_type=inst_type,
            pkg=pkg,
            cmd=cmd,
            filesystem=filesystem,
        )

    # -- model management ------------------------------------------------

    def pull_model(self, model_name: str) -> subprocess.Popen:
        """Start an ``ollama pull`` and return the live process."""
        from ai_lsc.utils.ollama import ollama_env
        env = enriched_env(self.base_bin_dir)
        ollama_env_overrides = ollama_env(self.models_root)
        env.update(ollama_env_overrides)
        # SE-06: redirect to log file instead of PIPE to avoid deadlock
        log_path = os.path.join(
            str(self.models_root).rsplit("/models", 1)[0], "logs",
            f"pull_{model_name.replace(':', '_')}.log",
        )
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_fh = open(log_path, "w", encoding="utf-8")
        return subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )

    # -- CLI launch -------------------------------------------------------

    def launch_cli(
        self,
        tool_id: str,
        launcher_type: str,
    ) -> str:
        """Open a terminal for the tool's CLI interface."""
        _validate_tool_id(tool_id)
        cmd = ""
        if launcher_type == "tmux":
            cmd = self._tmux.attach_cli(tool_id)
        elif launcher_type == "lxc":
            return self._lxc.launch_cli(f"ai-lsc-{tool_id}")
        env = enriched_env(self.base_bin_dir)
        from ai_lsc.constants import BASE_DIR
        self._process.launch_terminal(
            f"{cmd}cd {BASE_DIR} && echo 'Spawning CLI...' && exec bash",
            env=env,
        )
        return f"Spawned CLI terminal for {tool_id}"

    # -- web launch -------------------------------------------------------

    @staticmethod
    def open_web_url(port: str | int) -> str:
        """Open a browser tab for the given port. Returns the URL."""
        port_num = _validate_port(port)
        import webbrowser
        url = f"http://127.0.0.1:{port_num}"
        webbrowser.open(url)
        return url
