"""Status checker -- unified interface for checking if a service is live.

Delegates to backend-specific strategies (tmux, systemd, or psutil
process scan) based on the launcher type.
"""

from __future__ import annotations

from ai_lsc.runtime.systemd import SystemdManager
from ai_lsc.runtime.tmux import TmuxManager
from ai_lsc.utils.process import first_matching_process


class StatusChecker:
    """Check service liveness regardless of launcher backend."""

    def __init__(
        self,
        tmux: TmuxManager | None = None,
        systemd: SystemdManager | None = None,
    ) -> None:
        self._tmux = tmux or TmuxManager()
        self._systemd = systemd or SystemdManager()

    def is_running(
        self,
        launcher_type: str,
        tool_id: str,
        service_cmd: str = "",
        search_term: str = "",
    ) -> bool:
        """Return ``True`` if the service is currently running.

        Parameters
        ----------
        launcher_type:
            One of ``"tmux"``, ``"systemd"``, or anything else (psutil).
        tool_id:
            Used by tmux to identify the window.
        service_cmd:
            Used by systemd ``is-active``.
        search_term:
            Used by psutil ``process_iter`` scan.
        """
        strategy = {
            "systemd": lambda: self._systemd.is_active(service_cmd),
            "tmux": lambda: self._tmux.is_running(tool_id),
        }.get(launcher_type)

        if strategy is not None:
            return strategy()

        # fallback: psutil scan
        return first_matching_process(search_term) is not None
