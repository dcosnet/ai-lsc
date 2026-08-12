#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# AI Local Stack Control v3.1.0 — Ankh of Jah
# Bootstrap Script
#
# Fully portable: works wherever the tarball lands.
# Resolves the base directory from cwd or env var.
# Creates venv in-project.  On Arch, uses pacman's
# pre-built PySide6 to avoid pip compile hell.
# ──────────────────────────────────────────────────────────────
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Resolve paths (current-path aware) ────────────────────────
# SCRIPT_DIR = wherever bootstrap.sh lives (the project root)
# AI_BASE    = the managed working directory for all AI tools
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
VENV_PYTHON_STAMP="${VENV_DIR}/.python-version-stamp"

# Base directory: env var > parent of SCRIPT_DIR if named "tools" > /mnt/AI
# This lets you extract to /mnt/AI/tools/ai_lsc-v3/ and have it detect
# /mnt/AI as the base.  If extracted elsewhere, defaults to /mnt/AI or
# whatever AI_LSC_BASE_DIR says.
_PARENT_DIR="$(dirname "$SCRIPT_DIR")"
_PARENT_NAME="$(basename "$_PARENT_DIR")"
if [ -n "${AI_LSC_BASE_DIR:-}" ]; then
    AI_BASE="$AI_LSC_BASE_DIR"
elif [ "$_PARENT_NAME" = "tools" ] && [ -d "$(dirname "$_PARENT_DIR")/models" ]; then
    # We're inside .../tools/ai_lsc-v3/ — base is the parent of tools/
    AI_BASE="$(dirname "$_PARENT_DIR")"
else
    AI_BASE="${AI_LSC_BASE_DIR:-/mnt/AI}"
fi
export AI_LSC_BASE_DIR="$AI_BASE"

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     AI Local Stack Control v3.1.0 — Ankh of Jah       ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}  Project root : ${SCRIPT_DIR}${NC}"
echo -e "${CYAN}  Base dir     : ${AI_BASE}${NC}"
echo -e "${CYAN}  Venv         : ${VENV_DIR}${NC}"
echo ""

# ── Clean stale ~/.local/bin/ai-lsc from old pip/pipx installs ──
STALE_BIN="${HOME}/.local/bin/ai-lsc"
if [ -f "$STALE_BIN" ]; then
    warn "Found stale entry-point: ${STALE_BIN}"
    warn "Removing — everything runs via the project venv now"
    rm -f "$STALE_BIN"
fi

if command -v pipx &>/dev/null && pipx list 2>/dev/null | grep -q "ai-lsc"; then
    warn "Found pipx-installed ai-lsc — uninstalling"
    pipx uninstall ai-lsc 2>/dev/null || true
fi

# ── Ensure AI_BASE exists ─────────────────────────────────────
if [ ! -d "$AI_BASE" ]; then
    if [ "$(id -u)" -eq 0 ]; then
        mkdir -p "$AI_BASE"
        info "Created ${AI_BASE} (running as root)"
    else
        echo ""
        echo -e "${YELLOW}${AI_BASE} does not exist.${NC}"
        echo "  This is the managed working directory for all AI tools."
        echo ""
        read -p "Create ${AI_BASE} now? [Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            if command -v sudo &>/dev/null; then
                sudo mkdir -p "$AI_BASE"
                sudo chown "$(id -u):$(id -g)" "$AI_BASE"
                info "Created ${AI_BASE}"
            else
                error "Need sudo/root to create ${AI_BASE}. Create it manually and re-run."
            fi
        else
            echo ""
            read -p "Alternative base directory? [${SCRIPT_DIR}/ai-stack] " ALT_BASE
            ALT_BASE="${ALT_BASE:-${SCRIPT_DIR}/ai-stack}"
            mkdir -p "$ALT_BASE"
            warn "Using ${ALT_BASE}"
            AI_BASE="$ALT_BASE"
            export AI_LSC_BASE_DIR="$AI_BASE"
        fi
    fi
fi

# ── Helper: get system Python version string ──────────────────
_sys_python_version() {
    python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
}

# ── Helper: check if venv is stale (Python version mismatch) ──
_venv_is_stale() {
    if [ ! -f "$VENV_PYTHON_STAMP" ]; then
        return 0  # no stamp → treat as stale
    fi
    local stamp_version
    stamp_version="$(cat "$VENV_PYTHON_STAMP")"
    local sys_version
    sys_version="$(_sys_python_version)"
    if [ "$stamp_version" != "$sys_version" ]; then
        return 0  # version mismatch → stale
    fi
    return 1  # versions match → fresh
}

# ── Detect OS ──────────────────────────────────────────────────
if command -v pacman &>/dev/null; then
    PKG_MANAGER="pacman"
    info "Detected Arch Linux (pacman)"
elif command -v apt-get &>/dev/null; then
    PKG_MANAGER="apt"
    warn "Detected Debian/Ubuntu — some packages may differ from Arch names"
elif command -v dnf &>/dev/null; then
    PKG_MANAGER="dnf"
    warn "Detected Fedora/RHEL — some packages may differ from Arch names"
else
    warn "Unknown package manager. You may need to install dependencies manually."
    PKG_MANAGER="manual"
fi

# ── System Dependencies ───────────────────────────────────────
echo ""
info "Installing system dependencies..."

if [ "$PKG_MANAGER" = "pacman" ]; then
    SUDO=""
    if [ "$(id -u)" -ne 0 ]; then
        if command -v sudo &>/dev/null; then
            SUDO="sudo"
        fi
    fi

    # Core system packages (python-pyside6 is NOT in official repos —
    # we attempt it, then fall back to pip inside the venv below)
    $SUDO pacman -Sy --noconfirm --needed \
        python \
        python-pip \
        git \
        tmux \
        ripgrep \
        fd \
        tree-sitter \
        sqlite \
        redis \
        base-devel \
        || warn "Some system packages failed to install (non-critical)"

    # Try python-pyside6 from pacman if available (AUR / community)
    if $SUDO pacman -Si python-pyside6 &>/dev/null; then
        $SUDO pacman -Sy --noconfirm --needed python-pyside6 \
            || warn "python-pyside6 pacman install failed (will try pip fallback)"
    else
        warn "python-pyside6 not available in repos — will install via pip"
    fi

    info "Core system packages installed."

    echo ""
    read -p "Install NVIDIA CUDA support? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $SUDO pacman -Sy --noconfirm --needed cuda || warn "CUDA install failed"
        info "CUDA toolkit installed."
    fi

    read -p "Install container runtimes (podman, docker)? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $SUDO pacman -Sy --noconfirm --needed podman docker || warn "Container runtimes install failed"
        info "Container runtimes installed."
    fi

    read -p "Install LXC support? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $SUDO pacman -Sy --noconfirm --needed lxc lxcfs || warn "LXC install failed"
        info "LXC support installed."
    fi

elif [ "$PKG_MANAGER" = "apt" ]; then
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv python3-pyside6.qt6 \
        git tmux ripgrep fd-find sqlite3 redis-server \
        build-essential \
        || warn "Some system packages failed to install"
    info "Core system packages installed."

elif [ "$PKG_MANAGER" = "dnf" ]; then
    sudo dnf install -y \
        python3 python3-pip git tmux ripgrep fd-find sqlite redis \
        || warn "Some system packages failed to install"
    info "Core system packages installed."
fi

# ── Python Virtual Environment ─────────────────────────────────
echo ""

_create_venv() {
    if [ "$PKG_MANAGER" = "pacman" ]; then
        # Arch: --system-site-packages so venv sees pacman-installed PySide6
        python3 -m venv --system-site-packages "$VENV_DIR"
    else
        python3 -m venv "$VENV_DIR"
    fi
    _sys_python_version > "$VENV_PYTHON_STAMP"
}

if [ ! -d "$VENV_DIR" ]; then
    info "Creating Python virtual environment at ${VENV_DIR}..."
    _create_venv
else
    if _venv_is_stale; then
        old_ver=""
        if [ -f "$VENV_PYTHON_STAMP" ]; then
            old_ver="$(cat "$VENV_PYTHON_STAMP")"
        fi
        warn "Virtual environment is stale (was Python ${old_ver}, system is now $(_sys_python_version))"
        warn "Removing old venv and recreating..."
        rm -rf "$VENV_DIR"
        _create_venv
        info "Virtual environment recreated with Python $(_sys_python_version)"
    else
        info "Virtual environment already exists and is up-to-date at ${VENV_DIR}"
    fi
fi

info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# ── Verify venv activation (critical on Arch) ───────────────────
if [ ! -f "${VENV_DIR}/bin/pip" ]; then
    error "Virtual environment pip not found at ${VENV_DIR}/bin/pip — venv may be broken. Delete ${VENV_DIR} and re-run."
fi

VENV_PIP="${VENV_DIR}/bin/pip"

# ── Python Dependencies (inside venv — safe from EXTERNALLY-MANAGED) ──
echo ""
info "Installing Python dependencies into venv..."

$VENV_PIP install --upgrade pip setuptools wheel --quiet

# PySide6 — on Arch this comes from pacman (already installed above).
if [ "$PKG_MANAGER" = "pacman" ]; then
    if "${VENV_DIR}/bin/python3" -c "import PySide6" 2>/dev/null; then
        info "PySide6 (system) — OK"
    else
        warn "PySide6 (system) not visible in venv — attempting pip install..."
        $VENV_PIP install PySide6 --quiet 2>/dev/null || {
            warn "PySide6 installation failed. The app will run in headless mode."
        }
    fi
else
    $VENV_PIP install PySide6 --quiet 2>/dev/null || {
        warn "PySide6 installation failed. The app will run in headless mode."
    }
fi

# uv — fast Python package manager
$VENV_PIP install uv --quiet 2>/dev/null || warn "uv installation failed (non-critical)"

# ── Verify Installation ──────────────────────────────────────
echo ""
info "Verifying installation..."

ERRORS=0

PY_VER="${VENV_DIR}/bin/python3"
PY_VER_STR=$("$PY_VER" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$("$PY_VER" -c "import sys; print(sys.version_info.major)")
PY_MINOR=$("$PY_VER" -c "import sys; print(sys.version_info.minor)")
if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
    info "Python ${PY_VER_STR} (venv) — OK"
else
    warn "Python ${PY_VER_STR} (venv) — recommend 3.11+"
fi

if "$PY_VER" -c "import PySide6" 2>/dev/null; then
    info "PySide6 — OK"
else
    warn "PySide6 — NOT FOUND (UI will be unavailable)"
    ERRORS=$((ERRORS + 1))
fi

# Check registry loads (pass AI_LSC_BASE_DIR so it resolves correctly)
cd "$SCRIPT_DIR"
if AI_LSC_BASE_DIR="$AI_BASE" "$PY_VER" -c "
import sys
sys.path.insert(0, 'src')
from ai_lsc.registry.loader import load_merged_registry
reg = load_merged_registry()
print(f'  Registry: {len(reg)} tools loaded')
" 2>/dev/null; then
    info "Registry — OK"
else
    warn "Registry — could not load (check file structure)"
    ERRORS=$((ERRORS + 1))
fi

for cmd in ollama podman docker tmux ripgrep fd tree-sitter; do
    if command -v "$cmd" &>/dev/null; then
        info "${cmd} — found"
    else
        warn "${cmd} — not found (optional)"
    fi
done

# ── Summary ───────────────────────────────────────────────────
echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}Bootstrap complete! AI Local Stack Control is ready.${NC}"
    echo ""
    echo -e "  ${CYAN}Base dir: ${AI_BASE}${NC}"
    echo ""
    echo "  Launch the application:"
    echo "    cd ${SCRIPT_DIR}"
    echo "    python ai_lsc.py"
    echo ""
    echo "  Or use the convenience launcher:"
    echo "    bash run.sh"
    echo ""
else
    echo -e "${YELLOW}Bootstrap complete with ${ERRORS} warning(s).${NC}"
    echo "The application may run in limited mode. Review warnings above."
fi

# ── Write env file so run.sh and ai_lsc.py can pick it up ────
cat > "${SCRIPT_DIR}/.env" <<ENVEOF
AI_LSC_BASE_DIR=${AI_BASE}
ENVEOF
