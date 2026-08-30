"""
AI-LSC v3.1 — Application-wide constants.
Release codename: Ankh of Jah
Pure data: file names, schema version, required directories, default ports,
status styles, log colours, service licences, tree-skip patterns,
and the reorganized 10-layer navigation layer order.
"""

import os

# ── Base directory ─────────────────────────────────────────────────────
# Overridable via AI_LSC_BASE_DIR environment variable.
# Bootstrap sets this; the app resolves everything relative to it.
BASE_DIR: str = os.environ.get("AI_LSC_BASE_DIR", "/mnt/AI")
CANONICAL_BASE_DIR: str = BASE_DIR

# ── Filenames ────────────────────────────────────────────────────────────
APP_VERSION: str = "3.3.0"
APP_CODENAME: str = "Decalogue"
APP_DISPLAY_NAME: str = f"AI - Local Stack Control v{APP_VERSION} - http://dcos.net"
CONFIG_FILE: str = "controller_config.json"
APP_ICON_FILE: str = "ai-lsc-logo.png"
STATE_FILE_NAME: str = "pipeline_state.json"
PIPELINE_FILE_NAME: str = "pipeline.json"
STACK_SCHEMA_VERSION: str = "3.0"
MANIFEST_FILE_NAME: str = ".ai-lsc-project.json"
JCL_FILE_NAME: str = ".ai-lsc-jobs.json"

# ── Required sub-directories under BASE_DIR ────────────────────
# The canonical /mnt/AI/ folder layout (v3.1.1b, 24 dirs).
REQUIRED_DIRS: list[str] = [
    "backends",                 # S3/MinIO/Ceph connection profiles + topology
    "distfiles",                # permanent mirror of raw source tarballs + installers
    "runtime",                  # native compiled binaries (Ollama, llama.cpp, MinIO…)
    "models/hot",               # active weights; loaded or VRAM-ready (SSD)
    "models/cold",              # archived weights; offline / long-term retention (HDD)
    "corpus/hot",               # active text indexed in Vector DBs, used by agents
    "corpus/cold",              # raw, uningested, or unprocessed text archives
    "datasets/wordlists",       # fuzzing lists, dictionaries, tokenization test strings
    "datasets/huggingface",     # downloaded bulk datasets from Hugging Face
    "datasets/github",          # scraped or exported repository data
    "pipelines",                # ETL, chunking, and routing scripts (backends <-> DBs)
    "configs",                  # app configs templated for native runtime + app state
    "agents",                   # configs and chains for autonomous AI actors
    "skills",                   # 3rd-party skill files (QA and MoE templates, …)
    "projects/active",          # primary focus; actively developed codebases
    "projects/labs",            # experimental, beta, or throwaway POC code
    "projects/vault",           # archived masters, cloned refs, strict git histories
    "blueprints",               # Dockerfiles and build contexts for Podman exports
    "workspaces",               # interactive execution envs (Jupyter, OpenNotebook…)
    "dashboards",               # web UIs and landing pages (Dashy, Open-WebUI, …)
    "tools",                    # standalone compiles (built from distfiles)
    "exports/oci-images",       # finalized Podman .tar snapshots (-> MinIO registry)
    "scripts",                  # system admin / maintenance automation for the stack
    "logs",                     # system, runtime, and pipeline service logs
]

# ── Default ports for every known tool ───────────────────────────────────
DEFAULT_PORTS: dict[str, int | None] = {
    "postgresql": 5432,
    "mariadb": 3306,
    "redis": 6379,
    "sqlite3": None,
    "python": None,
    "cuda": None,
    "ollama": 11434,
    "llamacpp": 8080,
    "vllm": 8000,
    "litellm": 4000,
    "chromadb": 8000,
    "whisper": None,
    "docling": None,
    "aider": None,
    "claude_code": None,
    "fabric": None,
    "btop": None,
    "glances": 61208,
    "crewai": None,
    "autogen": None,
    "hermes": 17050,
    "openwebui": 8080,
    "anythingllm": 3001,
    "flowise": 3000,
    "dify": 80,
    "stack_exporter": None,
    "qdrant": 6333,
    "librechat": 3080,
    "n8n": 5678,
}

# ── UI status label formatting ──────────────────────────────────────────
STATUS_STYLES: dict[bool, tuple[str, str]] = {
    True:  ("[ LIVE ]",    "#2ecc71"),
    False: ("[ OFFLINE ]", "#7f8c8d"),
}

# ── Log source colours for the activity feed ────────────────────────────
LOG_SOURCE_COLORS: dict[str, str] = {
    "Ollama": "#e67e22",
    "Tmux": "#3498db",
    "Installer": "#2ecc71",
    "Audit": "#f39c12",
    "Container": "#9b59b6",
    "SkillRuntime": "#1abc9c",
    "Pipeline": "#e74c3c",
    "Lifecycle": "#2980b9",
    "SelfHeal": "#8e44ad",
    "Compiler": "#e67e22",
}
LOG_COLOR_DEFAULT: str = "#bdc3c7"

# ── Service licence notices ────────────────────────────────────────────
SERVICE_LICENSES: dict[str, str] = {
    "Open WebUI": "MIT License: github.com/open-webui/open-webui",
    "Aider": "Apache License 2.0: github.com/aider-chat/aider",
    "Hermes": "MIT License (Hermes Orchestrator)",
    "Odysseus": "MIT License (Local/Proprietary)",
    "Dify": "Dify Open Source License: github.com/langgenius/dify",
    "Flowise": "Apache License 2.0: github.com/FlowiseAI/Flowise",
    "AnythingLLM": "MIT License: github.com/Mintplex-Labs/anything-llm",
    "LiteLLM Proxy": "MIT License: github.com/BerriAI/litellm",
    "Claude Code": "Anthropic Terms of Service: anthropic.com",
    "CrewAI": "MIT License: github.com/joaomdmoura/crewAI",
    "AutoGen": "MIT License: github.com/microsoft/autogen",
    "LangChain": "MIT License: github.com/langchain-ai/langchain",
    "LangFlow": "Apache License 2.0: github.com/langflow-ai/langflow",
    "Ollama": "MIT License: github.com/ollama/ollama",
    "llama.cpp": "MIT License: github.com/ggerganov/llama.cpp",
    "Grafana": "AGPL-3.0: github.com/grafana/grafana",
    "Prometheus": "Apache License 2.0: github.com/prometheus/prometheus",
    "Qdrant": "Apache License 2.0: github.com/qdrant/qdrant",
    "n8n": "Apache License 2.0 (with Fair Code): github.com/n8n-io/n8n",
    "LibreChat": "MIT License: github.com/danny-avila/LibreChat",
    "InvokeAI": "MIT License: github.com/invoke-ai/InvokeAI",
    "Terraform": "BSL-1.1: github.com/hashicorp/terraform",
    "Ansible": "GPL-3.0: github.com/ansible/ansible",
    "Pulumi": "Apache License 2.0: github.com/pulumi/pulumi",
    "OpenTofu": "MPL-2.0: github.com/opentofu/opentofu",
    "MCP Drift State Tracker": "AGPL-3.0: git.dcos.net/dcosnet/MCP-Drift-State-Tracker",
}

# ── Tree-widget skip patterns ──────────────────────────────────────────
TREE_SKIP_PATTERNS: set[str] = {".", "__pycache__", "node_modules", "vendor"}

# ── Navigation layer order for the sidebar rack diagram ───────────────
# Updated to the new reorganized 10-Layer Architecture
NAV_LAYER_ORDER: list[str] = [
    "Host Platform & Infrastructure",
    "Development Runtime & Environment",
    "GPU Acceleration & Optimization",
    "Local Inference Engines",
    "Intelligent API Routers & Proxies",
    "Multi-Agent Orchestration Runtimes",
    "Agentic Software Engineering & Sandboxes",
    "Decentralized Knowledge & Vector Stores",
    "Data Extraction & Pipeline Harvest",
    "Human Interface & System Operations",
]

# ── Ollama server candidate paths (probed in order) ────────────────
OLLAMA_SERVER_CANDIDATES: list[str] = [
    "ollama",                  # /mnt/AI/ollama
    "tools/ollama",            # /mnt/AI/tools/ollama
    "runtime/ollama",          # /mnt/AI/runtime/ollama
    "bin/ollama"               # /mnt/AI/bin/ollama
]

# ── Model tier routing (reserved for v4.0 agentic layer) ──────────
MODEL_TIERS: dict[str, dict] = {
    "8b":  {"max_vram_gb": 8,  "desc": "Classification, routing, intent detection"},
    "14b": {"max_vram_gb": 14, "desc": "Utility, summarization, clarification"},
    "32b": {"max_vram_gb": 32, "desc": "Reasoning, analysis, code generation"},
    "70b": {"max_vram_gb": 70, "desc": "Heavy generation, complex reasoning, documents"},
}

# ── Agent runtime constants (reserved for v4.0 agentic layer) ────
AGENT_DEFAULT_MODEL: str = "qwen2.5:32b"
AGENT_MAX_ROUNDS: int = 20
CLARIFICATION_SKIP_THRESHOLD: float = 0.95
CLARIFICATION_CONFIRM_THRESHOLD: float = 0.70

# ── Qt Stylesheets ──────────────────────────────────────────────────────
GLOBAL_STYLE: str = """
QWidget {
    background-color: #161616;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #333;
    border-radius: 6px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: bold;
    color: #a5d6a7;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    left: 10px;
}
QPushButton {
    background-color: #2c3e50;
    color: white;
    border: 1px solid #1a252f;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #34495e;
}
QPushButton:pressed {
    background-color: #1a252f;
}
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1e1e1e;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 5px;
    color: white;
}
QTabWidget::pane {
    border: 1px solid #333;
    background-color: #1a1a1a;
    border-radius: 4px;
}
QTabBar::tab {
    background-color: #222;
    border: 1px solid #333;
    padding: 8px 15px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #3498db;
    color: white;
    font-weight: bold;
}
QTableWidget, QTreeWidget, QListWidget {
    background-color: #1e1e1e;
    gridline-color: #333;
    border: 1px solid #333;
    border-radius: 4px;
}
QHeaderView::section {
    background-color: #2c3e50;
    color: white;
    padding: 4px;
    border: 1px solid #1a252f;
    font-weight: bold;
}
"""

SIDEBAR_TREE_STYLE: str = """
QTreeWidget {
    background-color: #111111;
    border: none;
    color: #bdc3c7;
    font-family: 'Segoe UI';
    font-size: 11px;
}
QTreeWidget::item {
    padding: 6px;
    border-bottom: 1px solid #161616;
}
QTreeWidget::item:hover {
    background-color: #1c1c1c;
    color: #fff;
}
QTreeWidget::item:selected {
    background-color: #2c3e50;
    color: #2ecc71;
    font-weight: bold;
}
"""
