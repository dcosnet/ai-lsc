"""
AI-LSC — Process utilities.

Wrappers around ``subprocess``, ``shutil.which``, ``psutil``, and
environment construction.  Every subprocess call in the application
should go through one of these helpers so we get consistent PATH
enrichment and timeout handling in one place.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Sequence


def enriched_env(extra_bin_dirs: str | Sequence[str] = "") -> dict[str, str]:
    """Return a copy of ``os.environ`` with extra dirs prepended to PATH.

    Parameters
    ----------
    extra_bin_dirs:
        One or more directory paths to prepend, separated by ``:``
        (if a single string) or as an iterable.
    """
    env = os.environ.copy()

    # Remap ~/.local to /mnt/AI/tools/.local so that pip/pipx/uv
    # user installs land in the managed tools directory instead of
    # leaking into the user's home directory.
    from ai_lsc.constants import BASE_DIR
    managed_local = os.path.join(BASE_DIR, "tools", ".local", "bin")
    home_local = str(Path.home() / ".local" / "bin")

    if isinstance(extra_bin_dirs, str):
        dirs = [d.strip() for d in extra_bin_dirs.split(":") if d.strip()]
    else:
        dirs = list(extra_bin_dirs)

    extra = ":".join(d for d in dirs if d)
    # Prefer managed ~/.local over real ~/.local
    bin_dirs = []
    if extra:
        bin_dirs.append(extra)
    if os.path.isdir(managed_local):
        bin_dirs.append(managed_local)
    if home_local not in bin_dirs:
        bin_dirs.append(home_local)

    env["PATH"] = ":".join(d for d in bin_dirs if d) + ":" + env.get("PATH", "")
    return env


def find_binary(*candidates: str) -> str | None:
    """Return the first candidate found on ``$PATH``, or ``None``."""
    return next(
        (c for c in candidates if shutil.which(c)),
        None,
    )


def run_subprocess(
    cmd: str | list[str],
    timeout: float = 120.0,
    capture: bool = True,
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
) -> subprocess.CompletedProcess:
    """Centralised subprocess runner.

    Parameters
    ----------
    cmd:
        Command string or arg list.
    timeout:
        Max seconds before killing the process.
    capture:
        If *True* (default), capture stdout/stderr.
    env:
        Override environment (else inherits current).
    cwd:
        Working directory.
    """
    return subprocess.run(
        cmd if isinstance(cmd, list) else cmd,
        timeout=timeout,
        capture_output=capture,
        text=True,
        env=env or None,
        cwd=str(cwd) if cwd else None,
    )


# ── psutil helpers ────────────────────────────────────────────────────

def _process_matches(proc, search_term: str) -> bool:
    """Check if a process matches *search_term* by name or cmdline."""
    try:
        cmdline = " ".join(proc.info.get("cmdline") or [])
        return (
            search_term in (proc.info.get("name") or "")
            or search_term in cmdline
        )
    except Exception:
        # psutil.NoSuchProcess / AccessDenied / Zombie
        return False


def first_matching_process(search_term: str):
    """Return the first ``psutil.Process`` whose name/cmdline matches."""
    import psutil
    return next(
        (p for p in psutil.process_iter(["name", "cmdline"])
         if _process_matches(p, search_term)),
        None,
    )


def cpu_load_for_processes(search_term: str) -> float:
    """Return the aggregate CPU % for all matching processes."""
    import psutil
    return sum(
        p.cpu_percent(interval=0.1)
        for p in psutil.process_iter(["name", "cmdline"])
        if _process_matches(p, search_term)
    )
