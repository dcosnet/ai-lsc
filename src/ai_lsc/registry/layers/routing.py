"""Registry entries for the Routing layer (L5).

Restored layer (v3.1.1b): model gateways, LLM proxies, request routers,
mesh transport, and the model-routing tier that sits between the Engines
(who serve weights) and the Orchestrators (who build agent workflows on
top of a single OpenAI-compatible endpoint).  This re-unites the old
13-layer model's "AI Endpoints" tier (LiteLLM, model routers, API
gateways) that had been folded into Orchestrators during the 13-to-10
reorg, plus the mesh-aware clients that ride on it.

This module is consumed by :mod:`ai_lsc.registry.loader`.

Structural fields (layer, level) follow the 10-Layer Systems
Architecture Taxonomy; tools may be regrouped across files in a
future pass — the loader merges by tool, not by filename.
"""

TOOLS: dict[str, dict] = {
    'litellm': {
    "name": "LiteLLM Proxy",
    "level": 5,
    "layer": 'Intelligent API Routers & Proxies',
    "role": 'Unified API Gateway',
    "category": 'Unified API Gateway',
    "installer": {
        "type": "uv",
        "pkg": "litellm"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "litellm --port {port}",
        "default_port": 4000
    },
    "deps": [],
    "description": "Call 100+ LLMs using the OpenAI format.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},

    '9router_proxy': {
    "name": "9Router Proxy",
    "level": 5,
    "layer": 'Intelligent API Routers & Proxies',
    "role": 'Load Balancer',
    "category": 'Load Balancer',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/decolua/9router"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/9router && python3 main.py --port {port}",
        "default_port": 4001
    },
    "deps": [
        "ollama"
    ],
    "description": "Intelligent LLM request router and load balancer.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},

# ---- meshllm ----------------------------------------------------------------
# MeshLLM is its own native binary — NOT a LiteLLM re-skin. It pools GPUs
# and memory across machines, exposes one OpenAI-compat API at :9337, and
# has a web console at :3131. Install via the official curl installer.
    'meshllm': {
    "name": "MeshLLM",
    "level": 5,
    "layer": 'Intelligent API Routers & Proxies',
    "role": 'API Gateway',
    "category": 'LLM Mesh',
    "installer": {
        "type": "script",
        "cmd": "mkdir -p {tools_root}/meshllm/bin && curl -fsSL https://raw.githubusercontent.com/Mesh-LLM/mesh-llm/main/install.sh | MESH_LLM_INSTALL_DIR={tools_root}/meshllm/bin bash"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "mesh-llm serve --auto --port {port}",
        "default_port": 9337
    },
    "deps": [],
    "description": "Native binary that pools GPUs and memory across "
                  "machines and exposes the result as one OpenAI-"
                  "compatible API at http://localhost:9337/v1. Start "
                  "one node, add more nodes later — the mesh decides "
                  "whether a model runs locally, routes to a peer, or "
                  "uses Skippy stage splits for models too large for "
                  "one box. Web console on :3131. Has subcommands "
                  "(`mesh-llm goose`, `mesh-llm opencode`, `mesh-llm "
                  "claude`, `mesh-llm pi`) that wrap other coding agents "
                  "to use the mesh. QUIC-encrypted peer transport via "
                  "Iroh relays. NOT a LiteLLM derivative — distinct "
                  "project at https://github.com/Mesh-LLM/mesh-llm.",
    "license": "MIT",
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},

    'dify': {
    "name": "Dify",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Platform Workspace',
    "category": 'Platform Workspace',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/langgenius/dify.git"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/dify/api && poetry run flask run --host 0.0.0.0 --port={port}",
        "default_port": 5001
    },
    "deps": [
        "postgresql",
        "redis",
        "python",
        "nodejs"
    ],
    "description": "LLM application development platform (native install). Requires Poetry, Node.js 18+, FFmpeg. Backend (Flask) + Celery worker + Next.js frontend run as separate services.",
    "license": 'Dify-OSL',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},

'picode': {
    "name": "PiCode",
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Coding Agent',
    "category": 'Mesh Client',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/jasonjmcghee/picode.git"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "picode --version",
        "default_port": None
    },
    "deps": [
        "ollama"
    ],
    "description": "Local code-tinker agent. Speaks OpenAI-compat — point "
                  "OPENAI_API_BASE at the mesh (localhost:9337 for MeshLLM, "
                  "localhost:4000 for LiteLLM) or directly at Ollama "
                  "(localhost:11434/v1).",
    "license": "MIT",
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},

}
