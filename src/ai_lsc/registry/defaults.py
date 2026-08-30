"""
AI-LSC — Default tool registry (108 tools, 10-Layer Systems Architecture).

This is the first-boot seed registry.  The canonical source of truth at
runtime is the set of modular per-layer files under
``ai_lsc/registry/layers`` (discovered by :mod:`ai_lsc.registry.loader`);
``RegistryManager`` seeds ``ecosystem.json`` from the merged layer files
and syncs structural fields (layer, level, role, category) from them on
every start while preserving user customisations.

Convention
----------
Every entry has the same top-level shape::

    {
        "name":       <Human-readable display name>,
        "level":      <1–10 taxonomy level (int)>,
        "layer":      <Layer name matching NAV_LAYER_ORDER>,
        "role":       <Functional role within the layer>,
        "category":   <UI grouping category>,
        "installer":  {"type": <pacman|uv|pipx|pip|npm|git|git_node|script|custom>,
                        "pkg": <package name or URL>,
                        "cmd": <only for "script" type>,
                        "post_install" / "update_cmd" / "env_overrides": optional},
        "launcher":  {"type": <systemd|tmux|desktop>,
                        "cmd": <shell command with {placeholders}>,
                        "default_port": <int | None>},
        "deps":       [<tool_ids this tool depends on>],
        "description": <One-line human description>,
        "license":    <SPDX ID from registry/licenses.py>,
        "flags":      {<ToolFlags boolean fields>},
        "filesystem": {optional install/config/cache/logs/models paths},
    }

Launcher command placeholders
-----------------------------
``{port}``, ``{tools_root}``, ``{models_root}``,
``{workspaces_root}``, ``{base_dir}`` are resolved at launch time by
the ``ServiceRow`` dispatcher.

Layer map (10-Layer Systems Architecture Taxonomy)
---------------------------------------------------
L1  Host Platform & Infrastructure          — databases, caches, isolation, edge daemons
L2  Development Runtime & Environment       — runtimes, compilers, build, debug, search, VCS
L3  GPU Acceleration & Optimization          — CUDA, mixed precision, tensor libraries
L4  Local Inference Engines                  — local LLM servers (vLLM, llama.cpp, Ollama)
L5  Intelligent API Routers & Proxies        — LiteLLM, routers, mesh transport
L6  Multi-Agent Orchestration Runtimes       — Swarm, AutoGen, CrewAI, reasoning engines
L7  Agentic Software Engineering & Sandboxes — OpenHands, Aider, Claude Code, code skills
L8  Decentralized Knowledge & Vector Stores  — Chroma, Qdrant, Neo4j, agent memory
L9  Data Extraction & Pipeline Harvest       — Docling, Crawl4AI, Whisper, ETL
L10 Human Interface & System Operations      — chat consoles, telemetry, flow canvases, IaC

Flags
-----
``has_cli`` / ``has_gui`` / ``has_web`` describe the active surface(s) a
user can interact with once the tool is running.

``is_passive`` marks tools that are *consumed* (libraries, model packs,
CLIs without a daemon) rather than launched as long-running services.
``is_mcp`` marks MCP (Model Context Protocol) API tools.
``is_skills_collection`` marks bundled skill / capability definitions.

NOTE: This dict is intentionally kept as a *literal* so that it can be
      round-tripped through JSON without loss.  Do NOT add non-serialisable
      objects (Path, Enum, etc.) here.
"""

# NOTE: This dict is intentionally kept as a *literal* so that it can be
#       round-tripped through JSON without loss.  Do NOT add non-serialisable
#       objects (Path, Enum, etc.) here.


DEFAULT_REGISTRY: dict = {

    # ── L1: Host Platform & Infrastructure ────────────────────────────

    'container_tool': {
    "name": 'Container Toolkit',
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Isolation',
    "category": 'Isolation',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/container',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'container --help',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Lightweight bare-metal native container sandbox for direct code execution.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'duckdb': {
    "name": 'DuckDB',
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Analytical Database',
    "category": 'Analytical Database',
    "installer": {
        "type": 'uv',
        "pkg": 'duckdb',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import duckdb; print(duckdb.__version__)"',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'In-process analytical database engine supporting SQL for deep vector and metadata analytics.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'mariadb': {
    "name": 'MariaDB',
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Database',
    "category": 'Database',
    "installer": {
        "type": 'pacman',
        "pkg": 'mariadb',
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'mariadb',
        "default_port": 3306,
    },
    "deps": [
    ],
    "filesystem": {
        "install": '',
        "config": 'configs/mariadb',
        "data": 'data/mariadb',
        "logs": 'logs/mariadb',
    },
    "description": 'Open-source relational database serving transactional data across cluster networks.',
    "license": 'GPL-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'opensandbox': {
    "name": 'OpenSandbox',
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Isolation',
    "category": 'Isolation',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/opensandbox',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/opensandbox && python3 serve.py --port {port}',
        "default_port": 9100,
    },
    "deps": [
    ],
    "description": 'Secure sandboxed execution environment for testing agent output and running volatile bash routines.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'postgresql': {
    "name": 'PostgreSQL',
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Database',
    "category": 'Database',
    "installer": {
        "type": 'pacman',
        "pkg": 'postgresql',
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'postgresql',
        "default_port": 5432,
    },
    "deps": [
    ],
    "filesystem": {
        "install": '',
        "config": 'configs/postgresql',
        "data": 'data/postgresql',
        "logs": 'logs/postgresql',
    },
    "description": 'Relational database used by many frameworks for persistent storage, user logs, and key metadata.',
    "license": 'PostgreSQL',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'redis': {
    "name": 'Redis',
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Cache',
    "category": 'Cache',
    "installer": {
        "type": 'pacman',
        "pkg": 'redis',
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'redis',
        "default_port": 6379,
    },
    "deps": [
    ],
    "filesystem": {
        "install": '',
        "config": 'configs/redis',
        "data": 'data/redis',
        "logs": 'logs/redis',
    },
    "description": 'In-memory cache and message broker for fast key-value lookups, rate limiting, and chat session state management.',
    "license": 'RSALv2',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'sqlite3': {
    "name": 'SQLite3',
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Database',
    "category": 'Database',
    "installer": {
        "type": 'pacman',
        "pkg": 'sqlite',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'sqlite3',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'C-language library implementing a self-contained, serverless, zero-configuration SQL database engine.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'stack_exporter': {
    "name": 'Stack Container Packager',
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Runtime Packaging',
    "category": 'Runtime Packaging',
    "installer": {
        "type": 'pacman',
        "pkg": 'podman',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'podman --version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Compiles validated pipeline matrices into clean, native Podman or Docker specifications.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },

    # ── L2: Development Runtime & Environment ─────────────────────────

    'fd': {
    "name": 'fd',
    "level": 2,
    "layer": 'Development Runtime & Environment',
    "role": 'File Discovery',
    "category": 'File Discovery',
    "installer": {
        "type": 'pacman',
        "pkg": 'fd',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'fd --version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'A simple, fast, and user-friendly alternative to find, enabling agents to scan filesystems in milliseconds.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'python': {
    "name": 'Python Environment',
    "level": 2,
    "layer": 'Development Runtime & Environment',
    "role": 'Runtime Environment',
    "category": 'Runtime Environment',
    "installer": {
        "type": 'pacman',
        "pkg": 'python-pip',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 --version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Python core interpreter and virtual environments (venv), the foundation for almost all local AI libraries.',
    "license": 'Python',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'ripgrep': {
    "name": 'ripgrep (rg)',
    "level": 2,
    "layer": 'Development Runtime & Environment',
    "role": 'Text Search',
    "category": 'Text Search',
    "installer": {
        "type": 'pacman',
        "pkg": 'ripgrep',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'rg --version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Fast recursive search tool that respects gitignore rules, serving as the text retrieval engine for coding agents.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'sst': {
    "name": 'SST (Serverless Stack)',
    "level": 2,
    "layer": 'Development Runtime & Environment',
    "role": 'Infrastructure as Code',
    "category": 'Infrastructure as Code',
    "installer": {
        "type": 'npm',
        "pkg": 'sst',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'sst --version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Framework for building full-stack applications on local bare-metal cluster infrastructure.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'tree_sitter': {
    "name": 'tree-sitter',
    "level": 2,
    "layer": 'Development Runtime & Environment',
    "role": 'Parsing Engine',
    "category": 'Parsing Engine',
    "installer": {
        "type": 'uv',
        "pkg": 'tree-sitter',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'tree-sitter --version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Incremental parsing system for source code, allowing real-time syntax tree generation for coding agents.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },

    # ── L3: GPU Acceleration & Optimization ───────────────────────────

    'apex': {
    "name": 'NVIDIA Apex',
    "level": 3,
    "layer": 'GPU Acceleration & Optimization',
    "role": 'Mixed Precision',
    "category": 'Mixed Precision',
    "installer": {
        "type": 'pip',
        "pkg": 'apex',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import apex; print(apex.__version__)"',
        "default_port": None,
    },
    "deps": [
        'cuda',
    ],
    "description": 'NVIDIA mixed-precision utilities to accelerate training, optimization, and local model fine-tuning.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'cuda': {
    "name": 'CUDA Toolkit',
    "level": 3,
    "layer": 'GPU Acceleration & Optimization',
    "role": 'Hardware Acceleration',
    "category": 'Hardware Acceleration',
    "installer": {
        "type": 'pacman',
        "pkg": 'cuda',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'nvcc --version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'NVIDIA parallel computing platform and SDK, enabling direct bare-metal access to physical GPU execution cores.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'cupy': {
    "name": 'CuPy',
    "level": 3,
    "layer": 'GPU Acceleration & Optimization',
    "role": 'GPU Computing',
    "category": 'GPU Computing',
    "installer": {
        "type": 'uv',
        "pkg": 'cupy-cuda12x',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import cupy; print(cupy.__version__)"',
        "default_port": None,
    },
    "deps": [
        'cuda',
    ],
    "description": 'NumPy-compatible array computing library engineered specifically for high-throughput GPU computations.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'unsloth': {
    "name": 'Unsloth',
    "level": 3,
    "layer": 'GPU Acceleration & Optimization',
    "role": 'Model Optimization',
    "category": 'Model Optimization',
    "installer": {
        "type": 'uv',
        "pkg": 'unsloth',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import unsloth; print(\'ok\')"',
        "default_port": None,
    },
    "deps": [
        'cuda',
    ],
    "description": 'Advanced model training package providing 2x faster local LLM fine-tuning with 80% less physical VRAM memory.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },

    # ── L4: Local Inference Engines ───────────────────────────────────

    'airllm': {
    "name": 'AirLLM',
    "level": 4,
    "layer": 'Local Inference Engines',
    "role": 'Layer-wise Inference',
    "category": 'Layer-wise Inference',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/liguodongiot/llm-airforce',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/airllm && python3 -m airllm serve --port {port}',
        "default_port": 8001,
    },
    "deps": [
        'cuda',
    ],
    "description": 'Executes massive 70B+ model files on consumer-grade 4GB GPUs by streaming layers sequentially from NVMe SSD arrays.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'heretic': {
    "name": 'Heretic',
    "level": 4,
    "layer": 'Local Inference Engines',
    "role": 'Model Surgery',
    "category": 'Model Surgery',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/p-e-w/heretic',
        "post_install": 'pip install -e .',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import heretic; print(\'ok\')"',
        "default_port": None,
    },
    "deps": [
        'cuda',
    ],
    "description": 'Fully automatic censorship and safety-alignment removal tool via optimized abliteration of model weights.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'koboldcpp': {
    "name": 'KoboldCPP',
    "level": 4,
    "layer": 'Local Inference Engines',
    "role": 'GGUF Runtime',
    "category": 'GGUF Runtime',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/LostRuins/koboldcpp',
        "post_install": 'make',
        "update_cmd": 'git pull --ff-only && make clean && make',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/koboldcpp && make && ./koboldcpp --port {port}',
        "default_port": 5001,
    },
    "deps": [
    ],
    "description": 'GGUF-based inference runtime with a built-in user interface, supporting CUDA, OpenCL, and Vulkan backends.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'llamacpp': {
    "name": 'llama.cpp',
    "level": 4,
    "layer": 'Local Inference Engines',
    "role": 'Native Inference',
    "category": 'Native Inference',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/ggerganov/llama.cpp',
        "post_install": 'make',
        "update_cmd": 'git pull --ff-only && make clean && make',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/llamacpp && make && ./server --port {port}',
        "default_port": 8080,
    },
    "deps": [
    ],
    "description": 'Direct port of LLaMA models in pure C/C++, optimized for both CPU and GPU execution across multiple architectures.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'llamafile': {
    "name": 'Llamafile',
    "level": 4,
    "layer": 'Local Inference Engines',
    "role": 'Single-File Runtime',
    "category": 'Single-File Runtime',
    "installer": {
        "type": 'script',
        "pkg": 'llamafile',
        "cmd": 'mkdir -p {tools_root}/llamafile && curl -L -o {tools_root}/bin/llamafile https://github.com/Mozilla-Ocho/llamafile/releases/latest/download/llamafile && chmod +x {tools_root}/bin/llamafile',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": '{tools_root}/bin/llamafile',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Distributes and runs LLMs inside a single, cross-platform executable file with zero configuration required.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'locally_uncensored': {
    "name": 'Locally-Uncensored',
    "level": 4,
    "layer": 'Local Inference Engines',
    "role": 'Model Curation',
    "category": 'Model Curation',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/locally-uncensored',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'ollama list',
        "default_port": None,
    },
    "deps": [
        'ollama',
    ],
    "description": 'Curated collection of safety-unaligned GGUF models and terminal-based injection tools.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": True,
    }
    },
    'ollama': {
    "name": 'Ollama',
    "level": 4,
    "layer": 'Local Inference Engines',
    "role": 'Local LLM Runner',
    "category": 'Local LLM Runner',
    "installer": {
        "type": 'script',
        "pkg": 'ollama',
        "cmd": 'curl -fsSL https://ollama.com/install.sh | sh',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'OLLAMA_HOST=0.0.0.0:{port} OLLAMA_MODELS={models_root}/ollama ollama serve',
        "default_port": 11434,
    },
    "deps": [
    ],
    "filesystem": {
        "install": 'tools/ollama',
        "logs": 'logs/ollama',
        "models": 'models/ollama',
    },
    "description": 'Ecosystem and runner that manages model downloads, serving, and API routing through a streamlined terminal interface.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": True,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'turbollm': {
    "name": 'TurboLLM',
    "level": 4,
    "layer": 'Local Inference Engines',
    "role": 'Performance Engine',
    "category": 'Performance Engine',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/turbollm',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/turbollm && python3 -m turbollm serve --port {port}',
        "default_port": 8000,
    },
    "deps": [
        'cuda',
    ],
    "description": 'High-speed LLM serving engine designed for raw performance utilizing native C++ and tensor parallelism.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'vllm': {
    "name": 'vLLM',
    "level": 4,
    "layer": 'Local Inference Engines',
    "role": 'Datacenter Inference',
    "category": 'Datacenter Inference',
    "installer": {
        "type": 'uv',
        "pkg": 'vllm',
        "env_overrides": {
            'HF_HOME': '{base_dir}/cache/huggingface',
            'TRANSFORMERS_CACHE': '{base_dir}/cache/huggingface',
        },
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'python -m vllm.entrypoints.openai.api_server --port {port}',
        "default_port": 8000,
    },
    "deps": [
        'cuda',
    ],
    "filesystem": {
        "install": 'tools/vllm',
        "config": 'configs/vllm',
        "cache": 'cache/vllm',
        "logs": 'logs/vllm',
    },
    "description": 'High-throughput and memory-efficient local LLM serving engine utilizing PagedAttention to optimize GPU memory.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },

    # ── L5: Intelligent API Routers & Proxies ─────────────────────────

    '9router_proxy': {
    "name": '9Router Proxy',
    "level": 5,
    "layer": 'Intelligent API Routers & Proxies',
    "role": 'Load Balancer',
    "category": 'Load Balancer',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/9router',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/9router && python3 main.py --port {port}',
        "default_port": 4001,
    },
    "deps": [
        'ollama',
    ],
    "description": 'Intelligent, lightweight request router and backend balancer designed for local-first setups.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'fabric': {
    "name": 'Fabric',
    "level": 5,
    "layer": 'Intelligent API Routers & Proxies',
    "role": 'Curation Pipeline',
    "category": 'Curation Pipeline',
    "installer": {
        "type": 'script',
        "pkg": 'fabric',
        "cmd": 'curl -L https://github.com/danielmiessler/fabric/releases/latest/download/fabric-linux-amd64 > {tools_root}/bin/fabric && chmod +x {tools_root}/bin/fabric',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'OPENAI_API_BASE=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local fabric',
        "default_port": None,
    },
    "deps": [
        'litellm',
    ],
    "description": 'Command-line pipeline framework that curates prompt templates and pipes standard streams to local API routers.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'litellm': {
    "name": 'LiteLLM Proxy',
    "level": 5,
    "layer": 'Intelligent API Routers & Proxies',
    "role": 'Unified API Gateway',
    "category": 'Unified API Gateway',
    "installer": {
        "type": 'uv',
        "pkg": 'litellm',
        "env_overrides": {
            'LITELLM_CONFIG_DIR': '{base_dir}/configs/litellm',
        },
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'litellm --port {port}',
        "default_port": 4000,
    },
    "deps": [
    ],
    "filesystem": {
        "install": 'tools/litellm',
        "config": 'configs/litellm',
        "logs": 'logs/litellm',
    },
    "description": 'Multi-provider gateway that multiplexes queries, load-balances requests, and exposes all engines under a standard OpenAI API spec.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },

    # ── L6: Multi-Agent Orchestration Runtimes ────────────────────────

    'agentic_os': {
    "name": 'Agentic OS',
    "level": 6,
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Agent Shell',
    "category": 'Agent Shell',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/agentic-os',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/agentic_os && python3 main.py',
        "default_port": None,
    },
    "deps": [
        'ollama',
    ],
    "description": 'Autonomous operating system wrapper providing agents with safe API blocks and filesystem boundaries.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'agno': {
    "name": 'Agno',
    "level": 6,
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Production Multi-Agent',
    "category": 'Production Multi-Agent',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/agno-agi/agno',
        "cmd": 'pip install -e .',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'agno',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Enterprise agent builder featuring persistent memory, knowledge vectors, tracing, and granular user scheduling (formerly Phidata).',
    "license": 'MPL-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'autogen': {
    "name": 'AutoGen',
    "level": 6,
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Multi-Agent Framework',
    "category": 'Multi-Agent Framework',
    "installer": {
        "type": 'pipx',
        "pkg": 'pyautogen',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'autogen',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Framework enabling next-generation LLM applications with conversable, role-playing agents.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'crewai': {
    "name": 'CrewAI',
    "level": 6,
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Role-Playing Agent',
    "category": 'Role-Playing Agent',
    "installer": {
        "type": 'pipx',
        "pkg": 'crewai',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'crewai',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Orchestrates teams of specialized autonomous agents with built-in task delegation, tools, and visual loops.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'hermes_agent': {
    "name": 'Hermes Agent',
    "level": 6,
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Agent Daemon',
    "category": 'Agent Daemon',
    "installer": {
        "type": 'npm',
        "pkg": 'hermes-agent',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'hermes agent --port {port}',
        "default_port": 17051,
    },
    "deps": [
        'ollama',
    ],
    "description": 'Node.js-based autonomous agent executor designed to run long-running diagnostic scripts.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'hivemind': {
    "name": 'HiveMind',
    "level": 6,
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Coordination Protocol',
    "category": 'Coordination Protocol',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/hivemind',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/hivemind && python3 -m hivemind serve --port {port}',
        "default_port": 8700,
    },
    "deps": [
        'ollama',
    ],
    "description": 'Distributed multi-agent coordination daemon that enables direct consensus-based task solving across local peers.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'langchain': {
    "name": 'LangChain',
    "level": 6,
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Integration Library',
    "category": 'Integration Library',
    "installer": {
        "type": 'uv',
        "pkg": 'langchain',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import langchain; print(langchain.__version__)"',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Comprehensive standard library to connect language models with external APIs, databases, and structural flows.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'openai_swarm': {
    "name": 'OpenAI Swarm',
    "level": 6,
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Stateless Orchestration',
    "category": 'Stateless Orchestration',
    "installer": {
        "type": 'uv',
        "pkg": 'swarm',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import swarm; print(\'ok\')"',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Lightweight, client-side agent coordination library implementing ergonomic handoffs and direct procedural routines.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'synapscli': {
    "name": 'SynapsCLI',
    "level": 6,
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Terminal Agent',
    "category": 'Terminal Agent',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/HaseebKhalid1507/SynapsCLI',
        "cmd": 'cargo build --release',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'synapscli',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'High-performance, terminal-native agent executor written in Rust for parallel workflows and autonomous supervision.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'wayland_ai': {
    "name": 'Wayland AI',
    "level": 6,
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Desktop Agent Core',
    "category": 'Desktop Agent Core',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/ferroxlabs/wayland',
        "cmd": 'npx @ferroxlabs/wayland-core',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'wayland',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Unifies Claude Code, Codex, and other assistants under a single Rust-powered local orchestration runtime.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },

    # ── L7: Agentic Software Engineering & Sandboxes ──────────────────

    'aider': {
    "name": 'Aider',
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'CLI Pair Programmer',
    "category": 'CLI Pair Programmer',
    "installer": {
        "type": 'pipx',
        "pkg": 'aider-chat',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'OPENAI_API_BASE=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local aider --model {model_arg}',
        "default_port": None,
    },
    "deps": [
        'ollama',
        'litellm',
    ],
    "description": 'Git-integrated terminal assistant designed to edit files, write commits, and solve complex refactoring tasks in-place.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'claude_code': {
    "name": 'Claude Code',
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Terminal Coding Agent',
    "category": 'Terminal Coding Agent',
    "installer": {
        "type": 'npm',
        "pkg": '@anthropic-ai/claude-code',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'ANTHROPIC_BASE_URL=http://127.0.0.1:4000 ANTHROPIC_API_KEY=sk-ai-lsc-local claude',
        "default_port": None,
    },
    "deps": [
        'litellm',
    ],
    "description": 'Anthropic\'s terminal agent designed to execute codebase search, test diagnostics, and terminal commands natively.',
    "license": 'Anthropic-ToS',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'codex': {
    "name": 'Codex CLI',
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Codex Developer',
    "category": 'Codex Developer',
    "installer": {
        "type": 'npm',
        "pkg": '@openai/codex',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'OPENAI_BASE_URL=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local codex',
        "default_port": None,
    },
    "deps": [
        'litellm',
    ],
    "description": 'OpenAI\'s terminal interface providing interactive code generation and terminal command synthesis.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'loop_engineering': {
    "name": 'Loop Engineering',
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'CI/CD Orchestration',
    "category": 'CI/CD Orchestration',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/loop-engineering',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'loop-engineering --help',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Local development loop automation daemon designed to execute test sweeps and compile targets upon file triggers.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'mcp_drift_state_tracker': {
    "name": 'MCP Drift State Tracker',
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Context Integrity Core',
    "category": 'Context Integrity Core',
    "installer": {
        "type": 'git_node',
        "pkg": 'https://git.dcos.net/dcosnet/MCP-Drift-State-Tracker.git',
        "post_install": 'npm install && npm run build',
        "update_cmd": 'git pull --ff-only && npm install && npm run build',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/mcp_drift_state_tracker && node dist/index.js',
        "default_port": None,
    },
    "deps": [
    ],
    "filesystem": {
        "install": 'tools/mcp_drift_state_tracker',
        "config": 'configs/mcp_drift_state_tracker',
        "logs": 'logs/mcp_drift_state_tracker',
    },
    "description": 'TypeScript-based MCP server enforcing code completeness and neutralizing context erosion across active agent sessions.',
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": True,
        "is_skills_collection": False,
    }
    },
    'openhands': {
    "name": 'OpenHands',
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Sovereign Software Agent',
    "category": 'Sovereign Software Agent',
    "installer": {
        "type": 'git_node',
        "pkg": 'https://github.com/All-Hands-AI/OpenHands.git',
        "update_cmd": 'git pull --ff-only && pip install -e .',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/openhands && OPENAI_API_BASE=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local python -m openhands.server --port {port}',
        "default_port": 3000,
    },
    "deps": [
        'ollama',
        'litellm',
    ],
    "filesystem": {
        "install": 'tools/openhands',
        "config": 'workspaces/openhands/config',
        "cache": 'cache/openhands',
        "logs": 'logs/openhands',
    },
    "description": 'Full-stack AI developer agent that plans, writes, compiles, and tests code in secure sandboxed terminal containers.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'ponytail': {
    "name": 'Ponytail',
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Code Refactoring',
    "category": 'Code Refactoring',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/ponytail',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'ponytail generate',
        "default_port": None,
    },
    "deps": [
        'ollama',
    ],
    "description": 'Local-first refactoring engine designed to restructure complex directories and optimize file lengths.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'promptops': {
    "name": 'PromptOps.it',
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Prompt Tester',
    "category": 'Prompt Tester',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/promptops',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'promptops --help',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Version control, regression testing, and evaluation toolkit designed specifically for local prompt templates.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'skillspector': {
    "name": 'Skillspector',
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Skill Auditor',
    "category": 'Skill Auditor',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/skillspector',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'skillspector inspect',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Static analyzer designed to scan, inspect, and validate custom skills and tools exposed to local agents.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'spec_kit': {
    "name": 'Spec Kit',
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Requirement Builder',
    "category": 'Requirement Builder',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/spec-kit',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'spec-kit init',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Automated architectural specification writer that builds code blueprints based on raw developer prompts.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },

    # ── L8: Decentralized Knowledge & Vector Stores ───────────────────

    'chromadb': {
    "name": 'ChromaDB',
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Vector Engine',
    "category": 'Vector Engine',
    "installer": {
        "type": 'uv',
        "pkg": 'chromadb',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'chroma run --path {models_root}/chroma --port {port}',
        "default_port": 8000,
    },
    "deps": [
    ],
    "filesystem": {
        "install": 'tools/chromadb',
        "data": 'models/chroma',
        "logs": 'logs/chromadb',
    },
    "description": 'AI-native vector database optimized for embedded indexing, structured search, and agent memory caching.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'elasticsearch': {
    "name": 'Elasticsearch',
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Distributed Search',
    "category": 'Distributed Search',
    "installer": {
        "type": 'pacman',
        "pkg": 'elasticsearch',
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'elasticsearch',
        "default_port": 9200,
    },
    "deps": [
    ],
    "description": 'Distributed search and analytics engine for lexical queries, BM25 matches, and hybrid search pipelines.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'graphrag': {
    "name": 'GraphRAG',
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Structured Synthesis',
    "category": 'Structured Synthesis',
    "installer": {
        "type": 'uv',
        "pkg": 'graphrag',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -m graphrag init',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Microsoft\'s graph-based retrieval augmented generation system, converting raw text dumps into conceptual maps.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'lancedb': {
    "name": 'LanceDB',
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Serverless Database',
    "category": 'Serverless Database',
    "installer": {
        "type": 'uv',
        "pkg": 'lancedb',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'python3 -m lancedb serve --port {port}',
        "default_port": 8484,
    },
    "deps": [
    ],
    "description": 'Serverless vector store designed for fast, memory-mapped query execution and local disk offloading.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'meilisearch': {
    "name": 'Meilisearch',
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Lexical Search',
    "category": 'Lexical Search',
    "installer": {
        "type": 'script',
        "pkg": 'meilisearch',
        "cmd": 'curl -L https://install.meilisearch.com | sed \'s|/usr/local/bin|{tools_root}/meilisearch/bin|g\' | PREFIX={tools_root}/meilisearch sh',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'meilisearch --port {port}',
        "default_port": 7700,
    },
    "deps": [
    ],
    "description": 'Blazing fast, relevant, and typo-tolerant search engine designed to serve local codebase indexing.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'neo4j': {
    "name": 'Neo4j',
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Graph Database',
    "category": 'Graph Database',
    "installer": {
        "type": 'pacman',
        "pkg": 'neo4j',
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'neo4j',
        "default_port": 7474,
    },
    "deps": [
    ],
    "description": 'Native graph database server providing agent reasoning engines with high-speed relationship mapping and traversal.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'qdrant': {
    "name": 'Qdrant',
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'High-Performance Vector',
    "category": 'High-Performance Vector',
    "installer": {
        "type": 'script',
        "cmd": 'curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-musl.tar.gz | tar xz -C {tools_root}/qdrant && chmod +x {tools_root}/qdrant/qdrant',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": './qdrant --storage-path {models_root}/qdrant --host 127.0.0.1 --port {port}',
        "default_port": 6333,
    },
    "deps": [
    ],
    "filesystem": {
        "install": 'tools/qdrant',
        "data": 'data/qdrant',
        "logs": 'logs/qdrant',
    },
    "description": 'Rust-powered vector database with native mmap support, complex payload filtering, and sub-millisecond similarity search.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },

    # ── L9: Data Extraction & Pipeline Harvest ────────────────────────

    'airweave': {
    "name": 'Airweave',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Synchronization Layer',
    "category": 'Synchronization Layer',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/airweave',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/airweave && python3 -m airweave serve --port {port}',
        "default_port": 8600,
    },
    "deps": [
    ],
    "description": 'Real-time synchronization and integration manager connecting local databases directly with active model pipelines.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'crawl4ai': {
    "name": 'Crawl4AI',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Web Scraper',
    "category": 'Web Scraper',
    "installer": {
        "type": 'pipx',
        "pkg": 'crawl4ai',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'crawl4ai https://example.com',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'LLM-friendly crawler designed to clean markup, extract structural markdown, and feed clean context to agent loops.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'deep_eye': {
    "name": 'Deep Eye',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Vision describer',
    "category": 'Vision describer',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/deep-eye',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/deep_eye && python3 serve.py --port {port}',
        "default_port": 8100,
    },
    "deps": [
        'ollama',
    ],
    "description": 'Local computer vision analysis engine designed to monitor webcams or video inputs offline and provide descriptive captions.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'docling': {
    "name": 'Docling',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Document Parser',
    "category": 'Document Parser',
    "installer": {
        "type": 'pipx',
        "pkg": 'docling',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'docling',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Advanced multi-format document parser, converting complex PDFs, docx, and sheets into highly clean chunked text.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'luxtts': {
    "name": 'LuxTTS',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Voice Synthesis',
    "category": 'Voice Synthesis',
    "installer": {
        "type": 'uv',
        "pkg": 'luxtts',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'luxtts serve --port {port}',
        "default_port": 8500,
    },
    "deps": [
    ],
    "description": 'High-fidelity, local text-to-speech synthesis daemon creating standard voice outputs for interactive interfaces.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'markitdown': {
    "name": 'MarkItDown',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Markdown Converter',
    "category": 'Markdown Converter',
    "installer": {
        "type": 'pipx',
        "pkg": 'markitdown',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'markitdown document.pdf',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Microsoft command-line tool designed to convert miscellaneous office documents and files to standard markdown in-place.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'mirofish': {
    "name": 'Mirofish',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'ETL Transformation',
    "category": 'ETL Transformation',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/mirofish',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'mirofish --help',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Data transformation and ETL framework designed to convert database rows into clean training or RAG arrays.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'opendataloader': {
    "name": 'OpenDataLoader',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Data Ingest',
    "category": 'Data Ingest',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/opendataloader',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -m opendataloader --help',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Universal data loading and pre-processing pipeline for automated file format normalization.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'opendataloader_pdf': {
    "name": 'OpenDataLoader PDF',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'PDF Processing',
    "category": 'PDF Processing',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/opendataloader-pdf',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'opendataloader-pdf extract file.pdf',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Specialized OCR and text extraction pipeline designed specifically to process high-resolution scanned layout PDF files.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'parakeet': {
    "name": 'Parakeet.cpp',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Speech Transcriber',
    "category": 'Speech Transcriber',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/parakeet.cpp',
        "post_install": 'make',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/parakeet && ./parakeet --port {port}',
        "default_port": 8300,
    },
    "deps": [
        'cuda',
    ],
    "description": 'High-speed C++ speech recognition client utilizing optimized Transformer architectures for direct hardware running.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'understand_anything': {
    "name": 'Understand Anything',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Document Comprehension',
    "category": 'Document Comprehension',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/understand-anything',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'understand-anything analyze file.pdf',
        "default_port": None,
    },
    "deps": [
        'ollama',
    ],
    "description": 'Document semantic summarization tool designed to pre-process large files and generate abstract files for agent caches.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'whisper': {
    "name": 'Whisper',
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Audio Extraction',
    "category": 'Audio Extraction',
    "installer": {
        "type": 'pipx',
        "pkg": 'openai-whisper',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'whisper',
        "default_port": None,
    },
    "deps": [
    ],
    "filesystem": {
        "install": 'tools/whisper',
        "cache": 'cache/whisper',
    },
    "description": 'Robust speech-to-text transcription engine running locally to ingest and index audio media tracks.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },

    # ── L10: Human Interface & System Operations ──────────────────────

    'ansible': {
    "name": 'Ansible',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Agentless Deployment',
    "category": 'Agentless Deployment',
    "installer": {
        "type": 'pacman',
        "pkg": 'ansible',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'ansible --version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Agentless configuration management and automation orchestrating systems files across SSH links.',
    "license": 'GPL-3.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'anythingllm': {
    "name": 'AnythingLLM',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Collaborative Chat',
    "category": 'Collaborative Chat',
    "installer": {
        "type": 'git_node',
        "pkg": 'https://github.com/Mintplex-Labs/anything-llm.git',
        "update_cmd": 'git pull --ff-only && yarn install',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/anythingllm && yarn dev',
        "default_port": 3001,
    },
    "deps": [
    ],
    "filesystem": {
        "install": 'tools/anythingllm',
        "config": 'configs/anythingllm',
        "data": 'data/anythingllm',
        "logs": 'logs/anythingllm',
    },
    "description": 'Workspace-based desktop chat platform with built-in RAG parsers and security locks.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'aws_cdk': {
    "name": 'AWS CDK',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Cloud Dev Kit',
    "category": 'Cloud Dev Kit',
    "installer": {
        "type": 'npm',
        "pkg": 'aws-cdk',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'cdk --version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Defines local target groups and infrastructure profiles using standard TypeScript templates.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'bicep': {
    "name": 'Bicep',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Local Declarative DSL',
    "category": 'Local Declarative DSL',
    "installer": {
        "type": 'npm',
        "pkg": '@azure/bicep',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'bicep --version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Declarative template engine designed to outline system deployments under standard configurations.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'calibre': {
    "name": 'Calibre',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Library Manager',
    "category": 'Library Manager',
    "installer": {
        "type": 'pacman',
        "pkg": 'calibre',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'calibre',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Comprehensive e-book management, database indexing, and PDF converter utility running offline.',
    "license": 'GPL-3.0',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'career_ops': {
    "name": 'Career Ops',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Gap Analyzer',
    "category": 'Gap Analyzer',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/career-ops',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'career-ops analyze',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Self-hosted utility designed to scan developer resumes and audit skill gaps offline.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'dashy': {
    "name": 'Dashy',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Cluster Homepage',
    "category": 'Cluster Homepage',
    "installer": {
        "type": 'npm',
        "pkg": 'dashy',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'dashy --port {port}',
        "default_port": 3000,
    },
    "deps": [
    ],
    "description": 'Highly customizable visual homepage displaying active link cards for all cluster daemons.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'dify': {
    "name": 'Dify',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Platform Workspace',
    "category": 'Platform Workspace',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/langgenius/dify.git',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/dify/api && poetry run flask run --host 0.0.0.0 --port={port}',
        "default_port": 5001,
    },
    "deps": [
        'postgresql',
        'redis',
        'python',
        'node',
    ],
    "filesystem": {
        "install": 'tools/dify',
        "config": 'configs/dify',
        "data": 'data/dify',
        "logs": 'logs/dify',
    },
    "description": 'Complex web-based platform workspace hosting multiple multi-agent triggers, web hooks, and visual prompts.',
    "license": 'Dify-OSL',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'flowise': {
    "name": 'Flowise',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Visual Agent Canvas',
    "category": 'Visual Agent Canvas',
    "installer": {
        "type": 'npm',
        "pkg": 'flowise',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'npx flowise start --port {port}',
        "default_port": 3000,
    },
    "deps": [
    ],
    "filesystem": {
        "install": 'tools/flowise',
        "data": 'data/flowise',
        "logs": 'logs/flowise',
    },
    "description": 'Drag-and-drop workspace UI to build customized LLM pipelines, multi-agent frameworks, and RAG flows.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'forge': {
    "name": 'Forge (A1111)',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Image WebUI',
    "category": 'Image WebUI',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/AUTOMATIC1111/stable-diffusion-webui-forge',
        "env_overrides": {
            'HF_HOME': '{base_dir}/cache/huggingface',
            'DIFFUSERS_CACHE': '{base_dir}/cache/huggingface',
        },
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/forge && python3 launch.py --port {port}',
        "default_port": 7860,
    },
    "deps": [
        'cuda',
    ],
    "filesystem": {
        "install": 'tools/forge',
        "config": 'configs/forge',
        "data": 'data/forge',
        "cache": 'cache/forge',
        "logs": 'logs/forge',
    },
    "description": 'Stable Diffusion graphical interface for direct image generation using physical CUDA acceleration cores.',
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'glances': {
    "name": 'Glances',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Telemetry Monitor',
    "category": 'Telemetry Monitor',
    "installer": {
        "type": 'pacman',
        "pkg": 'glances',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'glances -w --port {port}',
        "default_port": 61208,
    },
    "deps": [
    ],
    "description": 'Cross-platform system resources dashboard tracking CPU, memory, and network sockets natively.',
    "license": 'LGPL-3.0',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'grafana': {
    "name": 'Grafana',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Telemetry Visualizer',
    "category": 'Telemetry Visualizer',
    "installer": {
        "type": 'pacman',
        "pkg": 'grafana',
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'grafana-server',
        "default_port": 3000,
    },
    "deps": [
    ],
    "description": 'Multi-source metrics dashboarding suite to monitor compute health and VRAM throughput visually.',
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'grafana_alloy': {
    "name": 'Grafana Alloy',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Alloy Telemetry',
    "category": 'Alloy Telemetry',
    "installer": {
        "type": 'script',
        "pkg": 'grafana/alloy',
        "cmd": 'mkdir -p {tools_root}/grafana_alloy/bin && curl -fsSL -o {tools_root}/grafana_alloy/bin/alloy https://github.com/grafana/alloy/releases/latest/download/alloy-linux-amd64 && chmod +x {tools_root}/grafana_alloy/bin/alloy',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'alloy run --server.http.listen-port={port}',
        "default_port": 12345,
    },
    "deps": [
        'prometheus',
    ],
    "description": 'OpenTelemetry pipeline collector collecting and aggregating system metrics from the cluster daemon endpoints.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'hermes': {
    "name": 'Hermes',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Ecosystem Launcher',
    "category": 'Ecosystem Launcher',
    "installer": {
        "type": 'npm',
        "pkg": 'hermes-ai',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'hermes dashboard --port {port} --data-dir {workspaces_root}/hermes & hermes desktop --data-dir {workspaces_root}/hermes',
        "default_port": 17050,
    },
    "deps": [
        'ollama',
    ],
    "filesystem": {
        "install": 'tools/hermes',
        "data": 'workspaces/hermes',
        "logs": 'logs/hermes',
    },
    "description": 'Unified desktop assistant combining active chat with resource monitors in a single visual framework.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'hermes_dashboard_page': {
    "name": 'Hermes Dashboard',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'System Console',
    "category": 'System Console',
    "installer": {
        "type": 'npm',
        "pkg": 'hermes-dashboard',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'hermes dashboard --port {port}',
        "default_port": 17050,
    },
    "deps": [
        'ollama',
    ],
    "description": 'Web-based graphical telemetry manager tracking active tasks and cluster state variables.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'hermes_desktop': {
    "name": 'Hermes Desktop',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Desktop GUI',
    "category": 'Desktop GUI',
    "installer": {
        "type": 'npm',
        "pkg": 'hermes-desktop',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'hermes desktop',
        "default_port": None,
    },
    "deps": [
        'ollama',
    ],
    "description": 'Desktop agent application designed to capture text prompts and run silent tasks in the background.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'homelab': {
    "name": 'Homelab',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Metal Provisioner',
    "category": 'Metal Provisioner',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/khuedoan/homelab',
        "cmd": '',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'homelab',
        "default_port": None,
    },
    "deps": [
        'ansible',
    ],
    "description": 'Automates full homelab provisioning from raw drive format to k3s cluster setup in a single run.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'invokeai': {
    "name": 'InvokeAI',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Studio Canvas',
    "category": 'Studio Canvas',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/invoke-ai/InvokeAI',
        "env_overrides": {
            'HF_HOME': '{base_dir}/cache/huggingface',
            'DIFFUSERS_CACHE': '{base_dir}/cache/huggingface',
        },
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/invokeai && invokeai --host 0.0.0.0 --port {port}',
        "default_port": 9090,
    },
    "deps": [
        'cuda',
    ],
    "filesystem": {
        "install": 'tools/invokeai',
        "config": 'configs/invokeai',
        "data": 'data/invokeai',
        "cache": 'cache/invokeai',
        "logs": 'logs/invokeai',
    },
    "description": 'Professional visual editing canvas for offline text-to-image synthesis and mask-based rendering.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'joplin': {
    "name": 'Joplin',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Offline Journal',
    "category": 'Offline Journal',
    "installer": {
        "type": 'pacman',
        "pkg": 'joplin',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'joplin',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Privacy-first note-taking and task list application syncing natively via SQLite3 files.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'kanban': {
    "name": 'Kanban Board',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Sprints Manager',
    "category": 'Sprints Manager',
    "installer": {
        "type": 'npm',
        "pkg": 'kanban-board',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'kanban',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Local visual dashboard designed to map task timelines and track developer sprints natively.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'langflow': {
    "name": 'LangFlow',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'RAG Flow Canvas',
    "category": 'RAG Flow Canvas',
    "installer": {
        "type": 'uv',
        "pkg": 'langflow',
        "env_overrides": {
            'LANGFLOW_CONFIG_DIR': '{base_dir}/configs/langflow',
        },
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'langflow run --port {port}',
        "default_port": 7860,
    },
    "deps": [
    ],
    "filesystem": {
        "install": 'tools/langflow',
        "config": 'configs/langflow',
        "cache": 'cache/langflow',
        "logs": 'logs/langflow',
    },
    "description": 'Visual node editor for building modular pipelines, routing endpoints, and testing custom prompt streams.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'latitude': {
    "name": 'Latitude',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Output Evaluator',
    "category": 'Output Evaluator',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/latitude',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/latitude && python3 -m latitude serve --port {port}',
        "default_port": 9300,
    },
    "deps": [
        'ollama',
    ],
    "description": 'LLM output evaluation and benchmarking suite designed to trace model degradation across cluster swaps.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'librechat': {
    "name": 'LibreChat',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Enterprise Assistant',
    "category": 'Enterprise Assistant',
    "installer": {
        "type": 'git_node',
        "pkg": 'https://github.com/danny-avila/LibreChat.git',
        "update_cmd": 'git pull --ff-only && yarn install && yarn build',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/librechat && API_PLUGINS=false PORT={port} NODE_ENV=production yarn backend',
        "default_port": 3080,
    },
    "deps": [
        'ollama',
    ],
    "filesystem": {
        "install": 'tools/librechat',
        "config": 'configs/librechat',
        "data": 'data/librechat',
        "logs": 'logs/librechat',
    },
    "description": 'Default agent interface with native tool execution, system files parsing, and multi-user configurations.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'local_llm_launcher': {
    "name": 'Local LLM Launcher',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Model Manager GUI',
    "category": 'Model Manager GUI',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/local-llm-launcher-gui',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'cd {tools_root}/local_llm_launcher && python3 main.py',
        "default_port": None,
    },
    "deps": [
        'ollama',
    ],
    "description": 'Desktop GUI utility built to trigger local model down-loaders and boot default executors.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'logseq': {
    "name": 'Logseq',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Outliner Graph',
    "category": 'Outliner Graph',
    "installer": {
        "type": 'npm',
        "pkg": 'logseq',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'logseq',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Privacy-first knowledge graph outliner storing local markdown files with local git synchronization.',
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'mnemosyne': {
    "name": 'Mnemosyne',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Learning Cards',
    "category": 'Learning Cards',
    "installer": {
        "type": 'pipx',
        "pkg": 'mnemosyne',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'mnemosyne',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Spaced repetition flashcard software designed to integrate with agent memory caches for automated studies.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'obsidian': {
    "name": 'Obsidian',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Sovereign Graph Editor',
    "category": 'Sovereign Graph Editor',
    "installer": {
        "type": 'pacman',
        "pkg": 'obsidian',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'obsidian',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Local-first note-taking system and knowledge graph displaying hyperlinked markdown files visually.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'openjarvis': {
    "name": 'OpenJarvis',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Local Central Shell',
    "category": 'Local Central Shell',
    "installer": {
        "type": 'git_node',
        "pkg": 'https://github.com/openjarvis/openjarvis.git',
        "post_install": 'npm install && npm run build',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/openjarvis && npm start -- --port {port}',
        "default_port": 17070,
    },
    "deps": [
        'ollama',
        'qdrant',
    ],
    "filesystem": {
        "install": 'tools/openjarvis',
        "config": 'configs/openjarvis',
        "data": 'workspaces/openjarvis',
        "cache": 'cache/openjarvis',
        "logs": 'logs/openjarvis',
    },
    "description": 'Centralized workspace manager providing multi-modal operations, file indexing, and unified terminal control.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'opentofu': {
    "name": 'OpenTofu',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Open-Source IaC',
    "category": 'Open-Source IaC',
    "installer": {
        "type": 'custom',
        "pkg": 'https://opentofu.org/docs/intro/install/',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'tofu version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Open-source Terraform fork under the Linux Foundation designed to automate resource bindings.',
    "license": 'MPL-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'openwebui': {
    "name": 'Open WebUI',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Extensible Interface',
    "category": 'Extensible Interface',
    "installer": {
        "type": 'uv',
        "pkg": 'open-webui',
        "env_overrides": {
            'OPEN_WEBUI_CONFIG_DIR': '{base_dir}/configs/openwebui',
        },
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'WEBUI_DATA_DIR={workspaces_root}/openwebui open-webui serve --port {port}',
        "default_port": 8080,
    },
    "deps": [
        'ollama',
    ],
    "filesystem": {
        "install": 'tools/openwebui',
        "config": 'configs/openwebui',
        "data": 'workspaces/openwebui',
        "logs": 'logs/openwebui',
    },
    "description": 'Web-based graphical assistant interface that routes prompts and provides full visual model execution.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'opik': {
    "name": 'Opik',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'LLM Observability',
    "category": 'LLM Observability',
    "installer": {
        "type": 'uv',
        "pkg": 'opik',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'opik serve --port {port}',
        "default_port": 3000,
    },
    "deps": [
    ],
    "description": 'Open-source LLM observability, tracing, and verification dashboard tracking active agent loops and prompt metrics.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'paperlessngx': {
    "name": 'Paperless-ngx',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Document Archiver',
    "category": 'Document Archiver',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/paperless-ngx/paperless-ngx',
        "env_overrides": {
            'PAPERLESS_DATA_DIR': '{base_dir}/data/paperlessngx',
        },
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/paperlessngx && python3 manage.py runserver 0.0.0.0:{port}',
        "default_port": 8000,
    },
    "deps": [
        'postgresql',
        'redis',
    ],
    "filesystem": {
        "install": 'tools/paperlessngx',
        "config": 'configs/paperlessngx',
        "data": 'data/paperlessngx',
        "logs": 'logs/paperlessngx',
    },
    "description": 'Document archival system indexing incoming PDF scans via native local Tesseract OCR engine loops.',
    "license": 'GPL-3.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'pm_skills': {
    "name": 'PM Skills',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Sprint Planner',
    "category": 'Sprint Planner',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/pm-skills',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'pm-skills plan',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Local planning script providing automated project estimation templates for developer workspaces.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": True,
    }
    },
    'prometheus': {
    "name": 'Prometheus',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Metric Scraper',
    "category": 'Metric Scraper',
    "installer": {
        "type": 'pacman',
        "pkg": 'prometheus',
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'prometheus',
        "default_port": 9090,
    },
    "deps": [
    ],
    "description": 'Time-series database engine designed to scrape and store historical performance telemetry across the cluster.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'pulse_ai': {
    "name": 'Pulse AI',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Auto Recovery Daemon',
    "category": 'Auto Recovery Daemon',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/pulse-ai',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .',
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/pulse_ai && python3 -m pulse serve --port {port}',
        "default_port": 8900,
    },
    "deps": [
    ],
    "description": 'AI service health monitor that automatically restarts crashed native systemd services across `/mnt/AI`.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'pulumi': {
    "name": 'Pulumi',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Programmable IaC',
    "category": 'Programmable IaC',
    "installer": {
        "type": 'npm',
        "pkg": '@pulumi/pulumi',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'pulumi version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Developer IaC platform designed to define local resource groups using standard Python or Go scripts.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'puppet': {
    "name": 'Puppet',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'System Auditor',
    "category": 'System Auditor',
    "installer": {
        "type": 'pacman',
        "pkg": 'puppet',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'puppet --version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Declarative system state auditor checking host directories against master configurations natively.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'terraform': {
    "name": 'Terraform',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Infrastructure Provision',
    "category": 'Infrastructure Provision',
    "installer": {
        "type": 'pacman',
        "pkg": 'terraform',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'terraform version',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Declarative infrastructure as code provisioning engine that maps cluster layouts to configurations.',
    "license": 'BSL-1.1',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'terragrunt': {
    "name": 'Terragrunt',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'IaC DRY Wrapper',
    "category": 'IaC DRY Wrapper',
    "installer": {
        "type": 'custom',
        "pkg": 'https://terragrunt.gruntwork.io/docs/getting-started/install/',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'terragrunt --version',
        "default_port": None,
    },
    "deps": [
        'terraform',
    ],
    "description": 'Thin wrapper designed to maintain clean configuration layouts and enforce DRY setups across clusters.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
    'zotero': {
    "name": 'Zotero',
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Reference Manager',
    "category": 'Reference Manager',
    "installer": {
        "type": 'pacman',
        "pkg": 'zotero',
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'zotero',
        "default_port": None,
    },
    "deps": [
    ],
    "description": 'Academic citation and library management engine running natively to store reference papers.',
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False,
    }
    },
}
