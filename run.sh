#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# AI-LSC v3.0 — Quick launch script
#
# Usage:
#   bash run.sh              # activates venv, launches GUI
#   bash run.sh --headless   # activates venv, runs without GUI
# ──────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
VENV_PYTHON="${VENV_DIR}/bin/python"

# ── Load .env for AI_LSC_BASE_DIR ────────────────────────────────
_ENV_FILE="${SCRIPT_DIR}/.env"
if [ -f "$_ENV_FILE" ]; then
    set -a  # auto-export all variables
    source "$_ENV_FILE"
    set +a
fi

# ── Ensure venv exists ────────────────────────────────────────
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] Virtual environment not found at ${VENV_DIR}"
    echo "  Run first:  bash bootstrap.sh"
    exit 1
fi

# ── Detect stale venv (Python version mismatch after pacman upgrade)
if [ -f "${VENV_DIR}/.python-version-stamp" ]; then
    STAMP="$(cat "${VENV_DIR}/.python-version-stamp")"
    SYS_VER="$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")"
    if [ "$STAMP" != "$SYS_VER" ]; then
        echo "[WARN] Virtual environment is stale (venv: ${STAMP}, system: ${SYS_VER})"
        echo "  Run:  bash bootstrap.sh"
        exit 1
    fi
fi

# ── Check for leftover ~/.local/bin/ai-lsc from old installs
STALE_BIN="${HOME}/.local/bin/ai-lsc"
if [ -f "$STALE_BIN" ]; then
    echo "[WARN] Found stale entry-point at ${STALE_BIN}"
    echo "  This is from a previous pip/pipx install. Remove it:"
    echo "    rm -f ${STALE_BIN}"
    echo ""
fi

# ── Launch ────────────────────────────────────────────────────
echo "  Base dir: ${AI_LSC_BASE_DIR:-/mnt/AI}"
echo "  Project : ${SCRIPT_DIR}"
echo ""

if [ "${1:-}" = "--headless" ]; then
    exec "$VENV_PYTHON" -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}/src')
from ai_lsc.constants import APP_DISPLAY_NAME, CANONICAL_BASE_DIR
print(f'{APP_DISPLAY_NAME}')
print(f'  Base dir: {CANONICAL_BASE_DIR}')
"
else
    exec "$VENV_PYTHON" "${SCRIPT_DIR}/ai_lsc.py" "$@"
fi
