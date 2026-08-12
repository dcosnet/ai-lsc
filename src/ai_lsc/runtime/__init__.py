"""AI-LSC runtime sub-package.

Process management abstraction layer.  All subprocess / psutil calls
live here so that UI code never touches the OS directly.

UI code calls :class:`RuntimeExecutor`, which delegates to backend-
specific managers (tmux, systemd, process, installer).
"""

from ai_lsc.runtime.executor import RuntimeExecutor
from ai_lsc.runtime.installer import InstallerManager
from ai_lsc.runtime.lxc import LxcManager
from ai_lsc.runtime.status import StatusChecker

__all__ = [
    "RuntimeExecutor",
    "InstallerManager",
    "LxcManager",
    "StatusChecker",
]
