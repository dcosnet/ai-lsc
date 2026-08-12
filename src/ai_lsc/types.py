"""
AI-LSC — Typed data structures.

Every module in the package should import types from here instead of passing
around raw ``dict`` objects.  Each dataclass has a ``from_dict`` classmethod
so we can hydrate from existing JSON / registry data with zero breakage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── Enumerations ────────────────────────────────────────────────────────

class LauncherType(Enum):
    """How a tool's process is managed."""
    SYSTEMD = "systemd"
    TMUX = "tmux"
    DESKTOP = "desktop"
    LXC = "lxc"


class InstallerType(Enum):
    """How a tool is installed on the host.

    Step-down containment order (most isolated first):
        ollama → uv → pipx → pip → git → git_node → npm → pacman → script → custom

    - **ollama**: Native ollama pull / model management.
    - **uv**:    ``uv tool install`` with ``--install-dir`` pinned to
                ``/mnt/AI/tools/<id>`` for full isolation.
    - **pipx**:  ``pipx install`` with ``PIPX_BIN_DIR`` and
                ``PIPX_HOME`` remapped into ``/mnt/AI/tools/<id>/.pipx``.
    - **pip**:   ``pip install --user --target`` into a per-tool venv
                under ``/mnt/AI/tools/<id>/.venv``.
    - **git**:   ``git clone`` into ``/mnt/AI/tools/<id>``.
    - **git_node**: git clone + npm/yarn setup in ``/mnt/AI/tools/<id>``.
    - **npm**:   ``npm install --prefix /mnt/AI/tools/<id>``.
    - **pacman**: System package (cannot relocate).
    - **dnf**:   Red Hat / Fedora system package (cannot relocate).
    - **apt**:   Debian / Ubuntu system package (cannot relocate).
    - **script**: Arbitrary shell command (must reference {tools_root}).
    - **custom**: Manual install — opens the install URL in browser.
    """
    OLLAMA = "ollama"
    UV = "uv"
    PIPX = "pipx"
    PIP = "pip"
    NPM = "npm"
    GIT = "git"
    GIT_NODE = "git_node"
    PACMAN = "pacman"
    DNF = "dnf"
    APT = "apt"
    SCRIPT = "script"
    CUSTOM = "custom"


# ── Tool metadata ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class InstallerSpec:
    """Immutable description of how to install a tool."""
    type: InstallerType
    pkg: str
    cmd: str | None = None          # only for "script" type
    post_install: str | None = None  # post-clone setup (pip install -r, make, etc.)
    update_cmd: str | None = None   # explicit update command (git pull, pip --upgrade, etc.)
    env_overrides: tuple[tuple[str, str], ...] = ()  # per-tool env var remappings


@dataclass(frozen=True)
class FilesystemSpec:
    """Declares where a tool's artifacts live relative to base_dir.

    All paths are relative and expanded against ``BASE_DIR``
    at runtime.  This keeps the registry portable — change one setting
    and every tool follows.

    Example::

        fs = FilesystemSpec(
            install="tools/vllm",
            config="configs/vllm",
            cache="cache/vllm",
            logs="logs/vllm",
        )
    """
    install: str = ""           # Primary install dir (relative to base_dir)
    config: str = ""            # Configuration files
    cache: str = ""             # Download / build caches
    data: str = ""              # Runtime databases / state
    logs: str = ""              # Log files
    runtime: str = ""            # PID files, sockets, tmp runtime
    models: str = ""             # Model files (if tool has own models)


@dataclass(frozen=True)
class LauncherSpec:
    """Immutable description of how to launch a tool."""
    type: LauncherType
    cmd: str
    default_port: int | None = None


@dataclass(frozen=True)
class ToolFlags:
    """Structured boolean flags from the registry entry.

    Interface awareness is split into two groups:

    * **Active surfaces** -- ``has_cli`` / ``has_gui`` / ``has_web`` describe
      how a user (or another tool) actually interacts with the running tool.
      Multiple can be true at once (e.g. Open WebUI ships both a CLI and a
      web frontend).

    * **Passive / role flags** -- ``is_passive`` is true for libraries,
      collections, MCP API definitions, or skill bundles that are *consumed*
      by other tools rather than launched as services.  ``is_mcp`` marks
      MCP (Model Context Protocol) API tools; ``is_skills_collection`` marks
      bundled skill / capability definitions.  These three let the UI
      visually separate "things you launch" from "things you reference".
    """
    has_cli: bool = False
    has_gui: bool = False
    has_web: bool = False
    is_ollama: bool = False
    is_passive: bool = False             # library / collection / no daemon
    is_mcp: bool = False                 # MCP (Model Context Protocol) API tool
    is_skills_collection: bool = False   # bundled skill / capability definitions

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ToolFlags:
        return cls(
            has_cli=raw.get("has_cli", False),
            has_gui=raw.get("has_gui", False),
            has_web=raw.get("has_web", False),
            is_ollama=raw.get("is_ollama", False),
            is_passive=raw.get("is_passive", False),
            is_mcp=raw.get("is_mcp", False),
            is_skills_collection=raw.get("is_skills_collection", False),
        )


@dataclass(frozen=True)
class ToolMetadata:
    """The strongly-typed representation of a single registry entry.

    Construction from a raw dict is lossy by design — unknown keys are
    silently dropped so new optional fields added to the registry schema
    do not break deserialization.
    """
    tool_id: str
    name: str
    level: int
    layer: str
    role: str
    category: str
    installer: InstallerSpec
    launcher: LauncherSpec
    deps: tuple[str, ...] = ()
    description: str = ""
    flags: ToolFlags = field(default_factory=ToolFlags)
    filesystem: FilesystemSpec = field(default_factory=FilesystemSpec)

    @classmethod
    def from_dict(cls, tool_id: str, raw: dict[str, Any]) -> ToolMetadata:
        inst_raw = raw.get("installer", {})
        launch_raw = raw.get("launcher", {})
        fs_raw = raw.get("filesystem", {})

        installer = InstallerSpec(
            type=InstallerType(inst_raw.get("type", "pacman")),
            pkg=inst_raw.get("pkg", ""),
            cmd=inst_raw.get("cmd"),
            post_install=inst_raw.get("post_install"),
            update_cmd=inst_raw.get("update_cmd"),
            env_overrides=tuple(
                (k, v) for k, v in inst_raw.get("env_overrides", {}).items()
            ),
        )
        launcher = LauncherSpec(
            type=LauncherType(launch_raw.get("type", "desktop")),
            cmd=launch_raw.get("cmd", ""),
            default_port=launch_raw.get("default_port"),
        )
        flags = ToolFlags.from_dict(raw.get("flags", {}))
        filesystem = FilesystemSpec(
            install=fs_raw.get("install", ""),
            config=fs_raw.get("config", ""),
            cache=fs_raw.get("cache", ""),
            data=fs_raw.get("data", ""),
            logs=fs_raw.get("logs", ""),
            runtime=fs_raw.get("runtime", ""),
            models=fs_raw.get("models", ""),
        )

        return cls(
            tool_id=tool_id,
            name=raw.get("name", tool_id),
            level=raw.get("level", 0),
            layer=raw.get("layer", "Uncategorized"),
            role=raw.get("role", ""),
            category=raw.get("category", ""),
            installer=installer,
            launcher=launcher,
            deps=tuple(raw.get("deps", [])),
            description=raw.get("description", ""),
            flags=flags,
            filesystem=filesystem,
        )

    @property
    def search_term(self) -> str:
        """Default process name used for status polling."""
        return self.installer.pkg or self.tool_id

    @property
    def is_skill(self) -> bool:
        return self.tool_id.startswith("skill:")

    @property
    def interface_summary(self) -> str:
        """Compact one-line summary of how the tool is interacted with.

        Used by the Tools tab to surface "what kind of thing is this" at a
        glance.  Examples::

            'Web UI'                       # Open WebUI
            'CLI + Web UI'                 # Aider
            'GUI + Web UI'                 # InvokeAI
            'CLI'                          # ripgrep
            'Passive (library)'            # langchain
            'Passive (skills collection)'  # nvidia_agent_skills
            'Passive (MCP API)'            # an MCP-only tool
        """
        surfaces: list[str] = []
        if self.flags.has_cli:
            surfaces.append("CLI")
        if self.flags.has_gui:
            surfaces.append("GUI")
        if self.flags.has_web:
            surfaces.append("Web UI")

        if self.flags.is_skills_collection:
            return "Passive (skills collection)"
        if self.flags.is_mcp:
            return "Passive (MCP API)"
        if self.flags.is_passive:
            return "Passive (library)"

        return " + ".join(surfaces) if surfaces else "—"


# ── Installation verification ────────────────────────────────────────

@dataclass(frozen=True)
class VerifyCheck:
    """A single verification check for a tool installation."""
    name: str
    passed: bool
    detail: str = ""


@dataclass
class VerificationResult:
    """Complete verification result for a single tool.

    Produces a quality score 0–100 based on how many checks pass.
    """
    tool_id: str
    checks: list[VerifyCheck] = field(default_factory=list)
    install_method: str = ""      # how the tool was actually installed
    install_location: str = ""    # where it was found

    @property
    def score(self) -> int:
        """Quality score 0–100."""
        if not self.checks:
            return 0
        passed = sum(1 for c in self.checks if c.passed)
        return int((passed / len(self.checks)) * 100)

    @property
    def summary(self) -> str:
        lines = [f"{self.tool_id} — Score: {self.score}%"]
        for c in self.checks:
            status = "PASS" if c.passed else "FAIL"
            lines.append(f"  [{status}] {c.name}: {c.detail}")
        return "\n".join(lines)


# ── Installation state ──────────────────────────────────────────────────

@dataclass
class PreflightResult:
    """Result of a pre-installation existence check.

    Returned by ``InstallerManager.preflight()`` so the UI can show
    "already installed → update?" or "not found → install?".
    """
    tool_id: str
    found: bool = False
    install_type: str = ""       # InstallerType value that owns the tool
    location: str = ""          # Where the binary/artifact was detected
    version: str = ""           # Detected version string (if any)
    is_update_available: bool = False
    suggested_action: str = "install"  # "install" | "update" | "none"

    @property
    def summary(self) -> str:
        if not self.found:
            return f"{self.tool_id}: not found — ready to install"
        action = "update available" if self.is_update_available else "up to date"
        return f"{self.tool_id}: {self.version or 'installed'} at {self.location} ({action})"


# ── Runtime state ──────────────────────────────────────────────────────

@dataclass
class ServiceState:
    """Mutable snapshot of a single tool's runtime status."""
    tool_id: str
    running: bool = False
    pid: int | None = None
    cpu_percent: float = 0.0


@dataclass
class PipelineState:
    """On-disk state representation (maps to ``pipeline_state.json``)."""
    session_name: str = "ai_lsc"
    base_dir: str = ""
    active_tools: list[str] = field(default_factory=list)
    port_map: dict[str, int | None] = field(default_factory=dict)
    stack_ready: bool = False
    compiled_pipelines: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.base_dir:
            from ai_lsc.constants import BASE_DIR
            self.base_dir = BASE_DIR

    @classmethod
    def from_dict(cls, raw: dict) -> PipelineState:
        return cls(
            session_name=raw.get("session_name", "ai_lsc"),
            base_dir=raw.get("base_dir", ""),
            active_tools=raw.get("active_tools", []),
            port_map=raw.get("port_map", {}),
            stack_ready=raw.get("stack_ready", False),
            compiled_pipelines=raw.get("compiled_pipelines", []),
        )

    def to_dict(self) -> dict:
        return {
            "session_name": self.session_name,
            "base_dir": self.base_dir,
            "active_tools": self.active_tools,
            "port_map": self.port_map,
            "stack_ready": self.stack_ready,
            "compiled_pipelines": self.compiled_pipelines,
        }
