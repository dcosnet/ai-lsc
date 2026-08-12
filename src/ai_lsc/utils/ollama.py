"""Ollama server path resolution and environment helpers.

Probes multiple candidate paths under ``BASE_DIR`` to locate
the ollama server binary, data directory, and configuration.  All other
modules should import from here instead of hardcoding paths.

Detection order (first match wins):
    1. ``<base_dir>/ollama``
    2. ``<base_dir>/tools/ollama``
    3. ``<base_dir>/runtime/ollama``
    4. ``<base_dir>/bin/ollama``
    5. System PATH fallback via ``shutil.which("ollama")``
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def detect_ollama_server_dir(base_dir: str) -> str:
    """Return the first candidate ollama server directory that exists.

    Probes paths defined in ``OLLAMA_SERVER_CANDIDATES`` under *base_dir*.
    Falls back to the parent of the system ``ollama`` binary if none of
    the managed paths exist.
    """
    from ai_lsc.constants import OLLAMA_SERVER_CANDIDATES

    for rel in OLLAMA_SERVER_CANDIDATES:
        full = os.path.join(base_dir, rel)
        if os.path.isdir(full):
            return full

    # System PATH fallback
    system_bin = shutil.which("ollama")
    if system_bin:
        return str(Path(system_bin).resolve().parent.parent)

    # Default: first candidate (will be created on install)
    return os.path.join(base_dir, OLLAMA_SERVER_CANDIDATES[0])


def ollama_models_dir(base_dir: str) -> str:
    """Return the models directory for ollama.

    Checks both the dedicated ``models/ollama`` tree and the ollama
    server's own ``~/.ollama/models`` directory.
    """
    primary = os.path.join(base_dir, "models", "ollama")
    if os.path.isdir(primary):
        return primary
    return os.path.join(detect_ollama_server_dir(base_dir), "models")


def ollama_env(base_dir: str) -> dict[str, str]:
    """Build the environment dict for ollama commands.

    Sets ``OLLAMA_MODELS`` and ``OLLAMA_HOST`` to use managed paths
    under *base_dir*.
    """
    return {
        "OLLAMA_MODELS": ollama_models_dir(base_dir),
        "OLLAMA_HOST": "127.0.0.1:11434",
    }


def ollama_binary(base_dir: str) -> str | None:
    """Find the ollama binary path.

    Checks the managed ``bin`` directories first, then falls back to
    the system PATH.
    """
    from ai_lsc.constants import OLLAMA_SERVER_CANDIDATES

    for rel in OLLAMA_SERVER_CANDIDATES:
        candidate = os.path.join(base_dir, rel, "bin", "ollama")
        if os.path.isfile(candidate):
            return candidate

    return shutil.which("ollama")


def ollama_is_installed(base_dir: str) -> bool:
    """Return True if ollama appears to be installed (binary found)."""
    return ollama_binary(base_dir) is not None
