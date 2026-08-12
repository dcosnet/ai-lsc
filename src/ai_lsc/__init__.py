"""
AI Local Stack Control v3.1 — Release codename: Ankh of Jah.

Extracted from the monolithic ``ai_lsc_v11.py`` in incremental phases.
Currently contains:

* **Phase 0** — constants, typed data structures, the 10-layer registry
  system, and utility modules.
* **Phase 1** — chat API worker, skill runtime resolver, stack export /
  container backend, and manifest support.
* **Phase 2** — LXC container backend, stack template system.
* **Phase 3** — Expanded IaC registry (Pulumi, SST, Bicep, OpenTofu,
  AWS CDK, Crossplane, Terragrunt).
* **v3.0** — Verification UI, ollama server path detection, packaging
  overhaul, agentic layer deferred to v4.0.
* **v3.1 (initial)** — Open Engineer integration: OE context record schema,
  markdown parser, import pipeline, standard template bridge,
  and 6 OE-derived stack templates with full engineering context.
* **v3.1 (2026-07-07 hardening + polish pass)** — Applied the full master
  code critique (91 of 93 findings addressed; see CHANGES.md and
  whatremains.txt).  Added the Pipeline Ticker (scrolling wiring-topology
  status bar at the top of every tab) and the Workspace Tab (peek-style
  orchestration with embedded QWebEngineView for web tools and tmux
  capture-pane polling for CLI tools).  Strengthened the registry
  validator to enforce the full 8-key flags schema.  Three latent bugs
  caught during the post-pass double-check are fixed.

All with **zero behavioural change** from the original monolith (where
behaviour was correct to begin with — the critique pass changed
behaviour only where the original behaviour was a bug).

Public API
----------
The ``__init__.py`` re-exports the most commonly used symbols so that
existing code can do::

    from ai_lsc import BASE_DIR, DEFAULT_REGISTRY, RegistryManager

instead of reaching into sub-packages.
"""

# ── Constants ─────────────────────────────────────────────────────────
from ai_lsc.constants import (
    APP_CODENAME,
    APP_DISPLAY_NAME,
    APP_VERSION,
    BASE_DIR,
    CONFIG_FILE,
    APP_ICON_FILE,
    STATE_FILE_NAME,
    PIPELINE_FILE_NAME,
    STACK_SCHEMA_VERSION,
    MANIFEST_FILE_NAME,
    JCL_FILE_NAME,
    REQUIRED_DIRS,
    DEFAULT_PORTS,
    STATUS_STYLES,
    LOG_SOURCE_COLORS,
    LOG_COLOR_DEFAULT,
    SERVICE_LICENSES,
    TREE_SKIP_PATTERNS,
    NAV_LAYER_ORDER,
    GLOBAL_STYLE,
    SIDEBAR_TREE_STYLE,
    MODEL_TIERS,
    OLLAMA_SERVER_CANDIDATES,
)

# ── Types ─────────────────────────────────────────────────────────────
from ai_lsc.types import (
    InstallerType,
    LauncherType,
    InstallerSpec,
    LauncherSpec,
    ToolFlags,
    ToolMetadata,
    FilesystemSpec,
    VerifyCheck,
    VerificationResult,
    PreflightResult,
    ServiceState,
    PipelineState,
)

# ── Registry ──────────────────────────────────────────────────────────
from ai_lsc.registry.defaults import DEFAULT_REGISTRY
from ai_lsc.registry.manager import RegistryManager
from ai_lsc.registry.stack_templates.manager import StackTemplateManager
from ai_lsc.registry.validator import validate_registry

# ── Utils ─────────────────────────────────────────────────────────────
from ai_lsc.utils.paths import build_path_tree, resolve_launcher_cmd
from ai_lsc.utils.process import (
    enriched_env,
    find_binary,
    run_subprocess,
    first_matching_process,
    cpu_load_for_processes,
)
from ai_lsc.utils.filesystem import ensure_base_dirs, walk_tree
from ai_lsc.utils.logging import setup_logging, get_logger
from ai_lsc.utils.ollama import (
    detect_ollama_server_dir,
    ollama_binary,
    ollama_env,
    ollama_is_installed,
    ollama_models_dir,
)

# ── Chat API (requires PySide6) ───────────────────────────────────────
try:
    from ai_lsc.chat.api import WorkerSignals, ApiRunnable
except ImportError:
    WorkerSignals = None   # PySide6 not installed
    ApiRunnable = None

# ── Skills ──────────────────────────────────────────────────────────────
try:
    from ai_lsc.skills.resolver import SkillRuntimeResolver
except ImportError:
    SkillRuntimeResolver = None  # skills subsystem deferred to v4.0

# ── Stack export ───────────────────────────────────────────────────────
from ai_lsc.stack.export import build_stack_spec, ContainerBackend

# ── Manifest support ────────────────────────────────────────────────────
from ai_lsc.manifest.support import ManifestSupport

# ── Open Engineer integration ────────────────────────────────────────
try:
    from ai_lsc.registry.openengineer import (
        OE_CONTEXT_FIELDS,
        OE_REQUIRED_FIELDS,
        OE_SUPPLEMENTARY_FIELDS,
        OE_CONFORMANCE_CRITERIA,
        StandardTemplate,
        standard_template_to_ai_lsc,
        OEContextParser,
        OpenEngineerImporter,
    )
except ImportError:
    OE_CONTEXT_FIELDS = None
    OE_REQUIRED_FIELDS = None
    OE_SUPPLEMENTARY_FIELDS = None
    OE_CONFORMANCE_CRITERIA = None
    StandardTemplate = None
    standard_template_to_ai_lsc = None
    OEContextParser = None
    OpenEngineerImporter = None

# ── Agents: DEFERRED to v4.0 ──────────────────────────────────────────
# The agentic tool-use bridge (ToolBridge, AgentLoop, AgentOrchestrator,
# etc.) has been removed from the v3.0 release.  It will return in
# v4.0 with a redesigned architecture.

__all__ = [
    # Constants
    "APP_VERSION", "APP_CODENAME", "APP_DISPLAY_NAME",
    "BASE_DIR", "CONFIG_FILE", "APP_ICON_FILE",
    "STATE_FILE_NAME", "PIPELINE_FILE_NAME", "STACK_SCHEMA_VERSION",
    "MANIFEST_FILE_NAME", "JCL_FILE_NAME", "REQUIRED_DIRS",
    "DEFAULT_PORTS", "STATUS_STYLES", "LOG_SOURCE_COLORS",
    "LOG_COLOR_DEFAULT", "SERVICE_LICENSES", "TREE_SKIP_PATTERNS",
    "NAV_LAYER_ORDER", "GLOBAL_STYLE", "SIDEBAR_TREE_STYLE",
    "MODEL_TIERS", "OLLAMA_SERVER_CANDIDATES",
    # Types
    "InstallerType", "LauncherType", "InstallerSpec", "LauncherSpec",
    "ToolFlags", "ToolMetadata", "FilesystemSpec", "VerifyCheck",
    "VerificationResult", "PreflightResult", "ServiceState", "PipelineState",
    # Registry
    "DEFAULT_REGISTRY", "RegistryManager", "StackTemplateManager", "validate_registry",
    # Utils
    "build_path_tree", "resolve_launcher_cmd",
    "enriched_env", "find_binary", "run_subprocess",
    "first_matching_process", "cpu_load_for_processes",
    "ensure_base_dirs", "walk_tree",
    "setup_logging", "get_logger",
    # Ollama helpers
    "detect_ollama_server_dir", "ollama_binary", "ollama_env",
    "ollama_is_installed", "ollama_models_dir",
    # Chat API
    "WorkerSignals", "ApiRunnable",
    # Skills
    "SkillRuntimeResolver",
    # Stack export
    "build_stack_spec", "ContainerBackend",
    # Manifest
    "ManifestSupport",
    # Open Engineer integration
    "OE_CONTEXT_FIELDS", "OE_REQUIRED_FIELDS", "OE_SUPPLEMENTARY_FIELDS",
    "OE_CONFORMANCE_CRITERIA", "StandardTemplate", "standard_template_to_ai_lsc",
    "OEContextParser", "OpenEngineerImporter",
]
