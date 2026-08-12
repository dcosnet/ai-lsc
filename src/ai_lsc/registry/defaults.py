"""
AI-LSC — Default registry data (~1 200 lines of pure data).

This is the *authoritative source of truth* for every tool known to the
ecosystem.  On first run ``RegistryManager`` writes this dict to
``ecosystem.json``; on subsequent runs it merges in any new keys so that
the on-disk registry auto-evolves across releases without user action.

Convention
----------
Every entry has the same top-level shape::

    {
        "name":       <Human-readable display name>,
        "level":      <1–13 taxonomy level (int)>,
        "layer":      <Layer name matching NAV_LAYER_ORDER>,
        "role":       <Functional role within the layer>,
        "category":   <UI grouping category>,
        "installer":  {"type": <pacman|uv|npm|git|git_node|script>,
                        "pkg": <package name or URL>,
                        "cmd": <only for "script" type>},
        "launcher":   {"type": <systemd|tmux|desktop>,
                        "cmd": <shell command with {placeholders}>,
                        "default_port": <int | None>},
        "deps":       [<tool_ids this tool depends on>],
        "description": <One-line human description>,
        "flags":      {<ToolFlags boolean fields>},
    }

Launcher command placeholders
-----------------------------
``{port}``, ``{tools_root}``, ``{models_root}``,
``{workspaces_root}``, ``{base_dir}`` are resolved at launch time by
the ``ServiceRow`` dispatcher.

Layer map
---------
L1  Host Platform              — containers, databases, caches
L2  Development Environment    — runtimes, search, parsing, frameworks
L3  GPU Runtimes               — CUDA, optimisation, fine-tuning
L4  Engines                    — local LLM servers
L5  Orchestrators              — serving, agents, routing, pipelines, workflow
L6  Security                   — auth, secrets, scanning, policy
L7  Observability              — metrics, dashboards, tracing, evaluation
L8  User Interfaces            — chat frontends, image gen, vision, speech
L9  DevOps                     — IaC, config management, coding agents, automation
L10 Knowledge Management       — vector stores, search, graphs, documents, memory

Flags
-----
``has_cli`` / ``has_gui`` / ``has_web`` describe the active surface(s) a
user can interact with once the tool is running.

``is_passive`` marks tools that are *consumed* (libraries, model packs,
CLIs without a daemon) rather than launched as long-running services.
``is_mcp`` marks MCP (Model Context Protocol) API tools.
``is_skills_collection`` marks bundled skill / capability definitions.
"""

# NOTE: This dict is intentionally kept as a *literal* so that it can be
#       round-tripped through JSON without loss.  Do NOT add non-serialisable
#       objects (Path, Enum, etc.) here.

DEFAULT_REGISTRY: dict = {

    # ── L1: Host Platform ──────────────────────────────────────
    'duckdb': {
    "name": 'DuckDB',
    "level": 1,
    "layer": 'Host Platform',
    "role": 'Foundation',
    "category": 'Analytical Database',
    "installer": {
        "type": 'uv',
        "pkg": 'duckdb'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import duckdb; print(duckdb.__version__)"',
        "default_port": None
    },
    "deps": [],
    "description": 'In-process analytical database with SQL support.',
    "license": 'MIT',
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
    'mariadb': {
    "name": 'MariaDB',
    "level": 1,
    "layer": 'Host Platform',
    "role": 'Foundation',
    "category": 'Database',
    "installer": {
        "type": 'pacman',
        "pkg": 'mariadb'
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'mariadb',
        "default_port": 3306
    },
    "deps": [],
    "description": 'Open source relational database.',
    "license": 'GPL-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": '',
        "config": 'configs/mariadb',
        "data": 'data/mariadb',
        "logs": 'logs/mariadb'
    }
    },
    'postgresql': {
    "name": 'PostgreSQL',
    "level": 1,
    "layer": 'Host Platform',
    "role": 'Foundation',
    "category": 'Database',
    "installer": {
        "type": 'pacman',
        "pkg": 'postgresql'
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'postgresql',
        "default_port": 5432
    },
    "deps": [],
    "description": 'Relational database used by many frameworks.',
    "license": 'PostgreSQL',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": '',
        "config": 'configs/postgresql',
        "data": 'data/postgresql',
        "logs": 'logs/postgresql'
    }
    },
    'redis': {
    "name": 'Redis',
    "level": 1,
    "layer": 'Host Platform',
    "role": 'Foundation',
    "category": 'Cache',
    "installer": {
        "type": 'pacman',
        "pkg": 'redis'
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'redis',
        "default_port": 6379
    },
    "deps": [],
    "description": 'In-memory cache and message broker.',
    "license": 'RSALv2',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": '',
        "config": 'configs/redis',
        "data": 'data/redis',
        "logs": 'logs/redis'
    }
    },
    'sqlite3': {
    "name": 'SQLite3',
    "level": 1,
    "layer": 'Host Platform',
    "role": 'Foundation',
    "category": 'Database',
    "installer": {
        "type": 'pacman',
        "pkg": 'sqlite'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'sqlite3',
        "default_port": None
    },
    "deps": [],
    "description": 'C-language library implementing a SQL database engine.',
    "license": 'MIT',
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

    # ── L2: Development Environment ────────────────────────────
    'cupy': {
    "name": 'CuPy',
    "level": 2,
    "layer": 'Development Environment',
    "role": 'GPU Acceleration',
    "category": 'GPU Computing',
    "installer": {
        "type": 'uv',
        "pkg": 'cupy-cuda12x'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import cupy; print(cupy.__version__)"',
        "default_port": None
    },
    "deps": ['cuda'],
    "description": 'NumPy-compatible GPU array computing library.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'fd': {
    "name": 'fd',
    "level": 2,
    "layer": 'Development Environment',
    "role": 'Search',
    "category": 'Find Tool',
    "installer": {
        "type": 'pacman',
        "pkg": 'fd'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'fd --version',
        "default_port": None
    },
    "deps": [],
    "description": 'Fast find command alternative.',
    "license": 'MIT',
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
    'python': {
    "name": 'Python Environment',
    "level": 2,
    "layer": 'Development Environment',
    "role": 'Build System',
    "category": 'Runtime',
    "installer": {
        "type": 'pacman',
        "pkg": 'python-pip'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 --version',
        "default_port": None
    },
    "deps": [],
    "description": 'Python core interpreter and virtual environments.',
    "license": 'Python',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'ripgrep': {
    "name": 'ripgrep (rg)',
    "level": 2,
    "layer": 'Development Environment',
    "role": 'Search',
    "category": 'Search Tool',
    "installer": {
        "type": 'pacman',
        "pkg": 'ripgrep'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'rg --version',
        "default_port": None
    },
    "deps": [],
    "description": 'Fast recursive search tool (grep replacement).',
    "license": 'MIT',
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
    'tree_sitter': {
    "name": 'tree-sitter',
    "level": 2,
    "layer": 'Development Environment',
    "role": 'Parsing',
    "category": 'Parser',
    "installer": {
        "type": 'uv',
        "pkg": 'tree-sitter'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'tree-sitter --version',
        "default_port": None
    },
    "deps": [],
    "description": 'Incremental parsing system for source code.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },

    # ── L3: GPU Runtime ────────────────────────────────────────
    'apex': {
    "name": 'NVIDIA Apex',
    "level": 3,
    "layer": 'GPU Runtimes',
    "role": 'Optimization',
    "category": 'Mixed Precision',
    "installer": {
        "type": 'pip',
        "pkg": 'apex'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import apex; print(apex.__version__)"',
        "default_port": None
    },
    "deps": ['cuda'],
    "description": 'NVIDIA mixed precision and distributed training.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'cuda': {
    "name": 'CUDA Toolkit',
    "level": 3,
    "layer": 'GPU Runtimes',
    "role": 'Acceleration',
    "category": 'GPU',
    "installer": {
        "type": 'pacman',
        "pkg": 'cuda'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'nvcc --version',
        "default_port": None
    },
    "deps": [],
    "description": 'NVIDIA CUDA parallel computing platform.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'heretic': {
    "name": 'Heretic',
    "level": 4,
    "layer": 'Engines',
    "role": 'Abliteration',
    "category": 'Model Surgery',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/p-e-w/heretic',
        "post_install": 'pip install -e .'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import heretic; print(\'ok\')"',
        "default_port": None
    },
    "deps": ['cuda'],
    "description": 'Fully automatic censorship/safety-alignment removal for transformer-based LLMs via optimized abliteration. Modifies model weights directly.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'unsloth': {
    "name": 'Unsloth',
    "level": 2,
    "layer": 'Development Environment',
    "role": 'Optimization',
    "category": 'LLM Fine-tuning',
    "installer": {
        "type": 'uv',
        "pkg": 'unsloth'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import unsloth; print(\'ok\')"',
        "default_port": None
    },
    "deps": ['cuda'],
    "description": '2x faster LLM fine-tuning with 80% less memory.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },

    # ── L4: Inference Engines ──────────────────────────────────
    'airllm': {
    "name": 'AirLLM',
    "level": 4,
    "layer": 'Engines',
    "role": 'Engine',
    "category": 'Efficient LLM',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/liguodongiot/llm-airforce',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/airllm && python3 -m airllm serve --port {port}',
        "default_port": 8001
    },
    "deps": ['cuda'],
    "description": 'Memory-efficient 70B LLM inference on 4GB GPUs.',
    "license": 'Proprietary',
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
    'koboldcpp': {
    "name": 'KoboldCPP',
    "level": 4,
    "layer": 'Engines',
    "role": 'Engine',
    "category": 'LLM Runtime',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/LostRuins/koboldcpp',
        "post_install": 'make',
        "update_cmd": 'git pull --ff-only && make clean && make'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/koboldcpp && make && ./koboldcpp --port {port}',
        "default_port": 5001
    },
    "deps": [],
    "description": 'GGUF-based LLM inference with CUDA/Vulkan.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'llamacpp': {
    "name": 'llama.cpp',
    "level": 4,
    "layer": 'Engines',
    "role": 'Engine',
    "category": 'LLM Runtime',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/ggerganov/llama.cpp',
        "post_install": 'make',
        "update_cmd": 'git pull --ff-only && make clean && make'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/llamacpp && make && ./server --port {port}',
        "default_port": 8080
    },
    "deps": [],
    "description": "Port of Facebook's LLaMA model in C/C++.",
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
    'llamafile': {
    "name": 'Llamafile',
    "level": 4,
    "layer": 'Engines',
    "role": 'Engine',
    "category": 'Single-File LLM',
    "installer": {
        "type": 'script',
        "pkg": 'llamafile',
        "cmd": 'mkdir -p {tools_root}/llamafile && curl -L -o {tools_root}/bin/llamafile https://github.com/Mozilla-Ocho/llamafile/releases/latest/download/llamafile && chmod +x {tools_root}/bin/llamafile'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": '{tools_root}/bin/llamafile',
        "default_port": None
    },
    "deps": [],
    "description": 'Distribute and run LLMs in a single file.',
    "license": 'Apache-2.0',
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
    'locally_uncensored': {
    "name": 'Locally-Uncensored',
    "level": 4,
    "layer": 'Engines',
    "role": 'Collection',
    "category": 'Model Collection',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/locally-uncensored'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'ollama list',
        "default_port": None
    },
    "deps": ['ollama'],
    "description": 'Curated uncensored model collection and tooling.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": True
    }
    },
    'ollama': {
    "name": 'Ollama',
    "level": 4,
    "layer": 'Engines',
    "role": 'Engine',
    "category": 'LLM Runtime',
    "installer": {
        "type": 'script',
        "pkg": 'ollama',
        "cmd": 'curl -fsSL https://ollama.com/install.sh | sh'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'OLLAMA_HOST=0.0.0.0:{port} OLLAMA_MODELS={models_root}/ollama ollama serve',
        "default_port": 11434
    },
    "deps": [],
    "description": 'Local LLM runner and model manager.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": True,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/ollama',
        "logs": 'logs/ollama',
        "models": 'models/ollama'
    }
    },
    'turbollm': {
    "name": 'TurboLLM',
    "level": 4,
    "layer": 'Engines',
    "role": 'Engine',
    "category": 'LLM Runtime',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/turbollm',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/turbollm && python3 -m turbollm serve --port {port}',
        "default_port": 8000
    },
    "deps": ['cuda'],
    "description": 'Fast LLM serving with tensor parallelism.',
    "license": 'Proprietary',
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

    # ── L5: Distributed Runtime ────────────────────────────────
    'vllm': {
    "name": 'vLLM',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Scaling',
    "category": 'LLM Serving',
    "installer": {
        "type": 'uv',
        "pkg": 'vllm',
        "env_overrides": {
            'HF_HOME': '{base_dir}/cache/huggingface',
            'TRANSFORMERS_CACHE': '{base_dir}/cache/huggingface'
        }
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'python -m vllm.entrypoints.openai.api_server --port {port}',
        "default_port": 8000
    },
    "deps": ['cuda'],
    "description": 'High-throughput and memory-efficient LLM serving.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/vllm',
        "config": 'configs/vllm',
        "cache": 'cache/vllm',
        "logs": 'logs/vllm'
    }
    },

    # ── L6: AI Endpoints ───────────────────────────────────────
    '9router_proxy': {
    "name": '9Router Proxy',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'API Gateway',
    "category": 'LLM Router',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/9router',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/9router && python3 main.py --port {port}',
        "default_port": 4001
    },
    "deps": ['ollama'],
    "description": 'Intelligent LLM request router and load balancer.',
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
    'deep_eye': {
    "name": 'Deep Eye',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Vision',
    "category": 'Computer Vision',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/deep-eye',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/deep_eye && python3 serve.py --port {port}',
        "default_port": 8100
    },
    "deps": ['ollama'],
    "description": 'Local computer vision analysis and description engine.',
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
    'litellm': {
    "name": 'LiteLLM Proxy',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'API Gateway',
    "category": 'Proxy',
    "installer": {
        "type": 'uv',
        "pkg": 'litellm',
        "env_overrides": {
            'LITELLM_CONFIG_DIR': '{base_dir}/configs/litellm'
        }
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'litellm --port {port}',
        "default_port": 4000
    },
    "deps": [],
    "description": 'Call 100+ LLMs using the OpenAI format.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/litellm',
        "config": 'configs/litellm',
        "logs": 'logs/litellm'
    }
    },
    'luxtts': {
    "name": 'LuxTTS',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Voice',
    "category": 'Text-to-Speech',
    "installer": {
        "type": 'uv',
        "pkg": 'luxtts'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'luxtts serve --port {port}',
        "default_port": 8500
    },
    "deps": [],
    "description": 'High-quality local text-to-speech synthesis.',
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

    # ── L7: Data & Knowledge Pipelines ─────────────────────────
    'airweave': {
    "name": 'Airweave',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Integration',
    "category": 'Data Sync',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/airweave',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/airweave && python3 -m airweave serve --port {port}',
        "default_port": 8600
    },
    "deps": [],
    "description": 'Real-time data synchronization and integration layer.',
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
    'chromadb': {
    "name": 'ChromaDB',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Memory / Senses',
    "category": 'Vector Store',
    "installer": {
        "type": 'uv',
        "pkg": 'chromadb'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'chroma run --path {models_root}/chroma --port {port}',
        "default_port": 8000
    },
    "deps": [],
    "description": 'AI-native open-source vector database.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/chromadb',
        "data": 'models/chroma',
        "logs": 'logs/chromadb'
    }
    },
    'crawl4ai': {
    "name": 'Crawl4AI',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Data Harvesting',
    "category": 'Web Crawler',
    "installer": {
        "type": 'pipx',
        "pkg": 'crawl4ai'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'crawl4ai https://example.com',
        "default_port": None
    },
    "deps": [],
    "description": 'LLM-friendly web crawler and data extractor.',
    "license": 'Proprietary',
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
    'docling': {
    "name": 'Docling',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Memory / Senses',
    "category": 'File Parsing',
    "installer": {
        "type": 'pipx',
        "pkg": 'docling'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'docling',
        "default_port": None
    },
    "deps": [],
    "description": 'Advanced document parsing and chunking.',
    "license": 'MIT',
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
    'elasticsearch': {
    "name": 'Elasticsearch',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Memory / Senses',
    "category": 'Search Engine',
    "installer": {
        "type": 'pacman',
        "pkg": 'elasticsearch'
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'elasticsearch',
        "default_port": 9200
    },
    "deps": [],
    "description": 'Distributed search and analytics engine.',
    "license": 'Apache-2.0',
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
    'fabric': {
    "name": 'Fabric',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Curation',
    "category": 'Content Pipeline',
    "installer": {
        "type": 'script',
        "pkg": 'fabric',
        "cmd": 'curl -L https://github.com/danielmiessler/fabric/releases/latest/download/fabric-linux-amd64 > {tools_root}/bin/fabric && chmod +x {tools_root}/bin/fabric'
    },
    "launcher": {
        "type": 'tmux',
        # Fabric reads OPENAI_API_BASE / OPENAI_API_KEY for its default
        # OpenAI-compatible client.  Force to localhost LiteLLM proxy.
        "cmd": 'OPENAI_API_BASE=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local fabric',
        "default_port": None
    },
    "deps": ['litellm'],
    "description": 'Open-source framework for augmenting humans using AI. LLM calls forced to localhost via OPENAI_API_BASE=http://127.0.0.1:4000/v1 (LiteLLM proxy) — override via the service row port if you run a different local backend.',
    "license": 'MIT',
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
    'graphrag': {
    "name": 'GraphRAG',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Knowledge Synthesis',
    "category": 'Graph RAG',
    "installer": {
        "type": 'uv',
        "pkg": 'graphrag'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -m graphrag init',
        "default_port": None
    },
    "deps": [],
    "description": 'Microsoft GraphRAG for knowledge graph construction.',
    "license": 'MIT',
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
    'lancedb': {
    "name": 'LanceDB',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Memory / Senses',
    "category": 'Vector Store',
    "installer": {
        "type": 'uv',
        "pkg": 'lancedb'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'python3 -m lancedb serve --port {port}',
        "default_port": 8484
    },
    "deps": [],
    "description": 'Serverless vector database for AI applications.',
    "license": 'Proprietary',
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
    'markitdown': {
    "name": 'MarkItDown',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'File Parsing',
    "category": 'Document Converter',
    "installer": {
        "type": 'pipx',
        "pkg": 'markitdown'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'markitdown document.pdf',
        "default_port": None
    },
    "deps": [],
    "description": 'Microsoft tool to convert files to Markdown.',
    "license": 'MIT',
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
    'meilisearch': {
    "name": 'Meilisearch',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Memory / Senses',
    "category": 'Search Engine',
    "installer": {
        "type": 'script',
        "pkg": 'meilisearch',
        "cmd": "curl -L https://install.meilisearch.com | sed 's|/usr/local/bin|{tools_root}/meilisearch/bin|g' | PREFIX={tools_root}/meilisearch sh"
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'meilisearch --port {port}',
        "default_port": 7700
    },
    "deps": [],
    "description": 'Fast, relevant, and typo-tolerant search engine.',
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
    'mirofish': {
    "name": 'Mirofish',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Transform',
    "category": 'Data Pipeline',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/mirofish'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'mirofish --help',
        "default_port": None
    },
    "deps": [],
    "description": 'Data transformation and ETL pipeline framework.',
    "license": 'Proprietary',
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
    'neo4j': {
    "name": 'Neo4j',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Memory / Senses',
    "category": 'Graph Database',
    "installer": {
        "type": 'pacman',
        "pkg": 'neo4j'
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'neo4j',
        "default_port": 7474
    },
    "deps": [],
    "description": 'Native graph database and knowledge graph engine.',
    "license": 'Proprietary',
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
    'opendataloader': {
    "name": 'OpenDataLoader',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Ingestion',
    "category": 'Data Pipeline',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/opendataloader',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -m opendataloader --help',
        "default_port": None
    },
    "deps": [],
    "description": 'Universal data loading and preprocessing pipeline.',
    "license": 'MIT',
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
    'opendataloader_pdf': {
    "name": 'OpenDataLoader PDF',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Extraction',
    "category": 'PDF Pipeline',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/opendataloader-pdf'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'opendataloader-pdf extract file.pdf',
        "default_port": None
    },
    "deps": [],
    "description": 'Specialized PDF extraction and data loading pipeline.',
    "license": 'MIT',
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
    'parakeet': {
    "name": 'Parakeet.cpp',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Senses',
    "category": 'Speech Recognition',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/parakeet.cpp',
        "post_install": 'make'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/parakeet && ./parakeet --port {port}',
        "default_port": 8300
    },
    "deps": ['cuda'],
    "description": 'C++ speech recognition with transformer architecture.',
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
    'qdrant': {
    "name": 'Qdrant',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Memory / Senses',
    "category": 'Vector Store',
    "installer": {
        "type": 'script',
        "cmd": 'curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-musl.tar.gz | tar xz -C {tools_root}/qdrant && chmod +x {tools_root}/qdrant/qdrant'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": './qdrant --storage-path {models_root}/qdrant --host 127.0.0.1 --port {port}',
        "default_port": 6333
    },
    "deps": [],
    "description": 'High-performance vector database with mmap storage, payload filtering, and multi-vector support.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/qdrant',
        "data": 'data/qdrant',
        "logs": 'logs/qdrant'
    }
    },
    'turbovec': {
    "name": 'TurboVec',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Embedding',
    "category": 'Vector Engine',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/turbovec',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/turbovec && python3 serve.py --port {port}',
        "default_port": 8101
    },
    "deps": ['cuda'],
    "description": 'High-speed embedding generation and vector engine.',
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
    'understand_anything': {
    "name": 'Understand Anything',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Comprehension',
    "category": 'Document Understanding',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/understand-anything'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'understand-anything analyze file.pdf',
        "default_port": None
    },
    "deps": ['ollama'],
    "description": 'Universal document understanding and summarization.',
    "license": 'MIT',
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
    'whisper': {
    "name": 'Whisper',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Memory / Senses',
    "category": 'Audio Parsing',
    "installer": {
        "type": 'pipx',
        "pkg": 'openai-whisper'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'whisper',
        "default_port": None
    },
    "deps": [],
    "description": 'Robust Speech Recognition via Large-Scale Weak Supervision.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/whisper',
        "cache": 'cache/whisper'
    }
    },

    # ── L8: Automation & Execution ─────────────────────────────
    'agent_reach': {
    "name": 'Agent Reach',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Discovery',
    "category": 'Agent Network',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/agent-reach'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'agent-reach discover',
        "default_port": None
    },
    "deps": [],
    "description": 'Multi-agent service discovery and capability mapping.',
    "license": 'Proprietary',
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
    'agentic_os': {
    "name": 'Agentic OS',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Hands',
    "category": 'Agent OS',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/agentic-os',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/agentic_os && python3 main.py',
        "default_port": None
    },
    "deps": ['ollama'],
    "description": 'Autonomous agent operating system framework.',
    "license": 'MIT',
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
    'agno': {
    "name": 'Agno',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Multi-Agent',
    "category": 'Agent Framework',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/agno-agi/agno',
        "cmd": 'pip install -e .'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'agno',
        "default_port": None
    },
    "deps": [],
    "description": 'Python framework for building multi-agent platforms with memory, knowledge, tools, and reasoning. Production deployment via AgentOS with tracing, scheduling, and RBAC. Originally Phidata.',
    "license": 'MPL-2.0',
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
    'aider': {
    "name": 'Aider',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Hands',
    "category": 'Development',
    "installer": {
        "type": 'pipx',
        "pkg": 'aider-chat'
    },
    "launcher": {
        "type": 'tmux',
        # Force localhost-only endpoint: route OpenAI-compatible API
        # calls to the local LiteLLM proxy (default port 4000) instead
        # of api.openai.com.  Aider reads OPENAI_API_BASE for the
        # endpoint and OPENAI_API_KEY for auth.
        "cmd": 'OPENAI_API_BASE=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local aider --model {model_arg}',
        "default_port": None
    },
    "deps": ['ollama', 'litellm'],
    "description": 'AI pair programming in your terminal. Forced to localhost via OPENAI_API_BASE=http://127.0.0.1:4000/v1 (LiteLLM proxy) — override via the service row port if you run a different local backend.',
    "license": 'Apache-2.0',
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
    'algory': {
    "name": 'Algory',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Hands',
    "category": 'Algorithm Toolkit',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/algory'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'algory --help',
        "default_port": None
    },
    "deps": [],
    "description": 'Algorithm design and benchmarking toolkit.',
    "license": 'MIT',
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
    'atlas_os': {
    "name": 'Atlas OS',
    "level": 9,
    "layer": 'DevOps',
    "role": 'OS Integration',
    "category": 'AI Operating System',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/atlas-os'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'atlas --version',
        "default_port": None
    },
    "deps": ['ollama'],
    "description": 'AI-native operating system integration layer.',
    "license": 'Proprietary',
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
    'claude_code': {
    "name": 'Claude Code',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Hands',
    "category": 'Development',
    "installer": {
        "type": 'npm',
        "pkg": '@anthropic-ai/claude-code'
    },
    "launcher": {
        "type": 'tmux',
        # Force localhost-only endpoint: route Anthropic API calls to
        # the local LiteLLM proxy (default port 4000) instead of
        # api.anthropic.com.  User can override the port via the
        # service row if they run a different local proxy.
        "cmd": 'ANTHROPIC_BASE_URL=http://127.0.0.1:4000 ANTHROPIC_API_KEY=sk-ai-lsc-local claude',
        "default_port": None
    },
    "deps": ['litellm'],
    "description": "Anthropic's terminal assistant. Forced to localhost via ANTHROPIC_BASE_URL=http://127.0.0.1:4000 (LiteLLM proxy) — override via the service row port if you run a different local backend.",
    "license": 'Anthropic-ToS',
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
    'codex': {
    "name": 'Codex CLI',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Hands',
    "category": 'AI Coding Agent',
    "installer": {
        "type": 'npm',
        "pkg": '@openai/codex'
    },
    "launcher": {
        "type": 'tmux',
        # Force localhost-only endpoint: route OpenAI API calls to the
        # local LiteLLM proxy (default port 4000) instead of
        # api.openai.com.  Codex CLI reads OPENAI_BASE_URL +
        # OPENAI_API_KEY env vars.  User can override the port via the
        # service row if they run a different local proxy.
        "cmd": 'OPENAI_BASE_URL=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local codex',
        "default_port": None
    },
    "deps": ['litellm'],
    "description": 'OpenAI\'s open-source Codex CLI for terminal-based AI coding. Forced to localhost via OPENAI_BASE_URL=http://127.0.0.1:4000/v1 (LiteLLM proxy) — override via the service row port if you run a different local backend.',
    "license": 'Apache-2.0',
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
    'eagle_eye': {
    "name": 'Eagle-Eye',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Inspector',
    "category": 'Code Analysis',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/eagle-eye'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'eagle-eye scan .',
        "default_port": None
    },
    "deps": [],
    "description": 'Automated code inspection and quality gate.',
    "license": 'MIT',
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
    'graphify': {
    "name": 'Graphify',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Graph Builder',
    "category": 'Knowledge Graph',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/graphify'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'graphify build .',
        "default_port": None
    },
    "deps": [],
    "description": 'Codebase knowledge graph construction tool.',
    "license": 'Proprietary',
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
    'headroom': {
    "name": 'Headroom',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Context',
    "category": 'Context Manager',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/headroom'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'headroom scan',
        "default_port": None
    },
    "deps": [],
    "description": 'Codebase context extraction and management.',
    "license": 'Proprietary',
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
    'hermes_agent': {
    "name": 'Hermes Agent',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Agent',
    "category": 'AI Agent',
    "installer": {
        "type": 'npm',
        "pkg": 'hermes-agent'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'hermes agent --port {port}',
        "default_port": 17051
    },
    "deps": ['ollama'],
    "description": 'Hermes autonomous agent runtime.',
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
    'hivemind': {
    "name": 'HiveMind',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Coordination',
    "category": 'Multi-Agent',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/hivemind',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/hivemind && python3 -m hivemind serve --port {port}',
        "default_port": 8700
    },
    "deps": ['ollama'],
    "description": 'Distributed multi-agent coordination framework.',
    "license": 'Proprietary',
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
    'honcho': {
    "name": 'Honcho',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Process Manager',
    "category": 'Procfile Runner',
    "installer": {
        "type": 'pipx',
        "pkg": 'honcho'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'honcho start',
        "default_port": None
    },
    "deps": [],
    "description": 'Python Procfile manager for multi-process apps.',
    "license": 'Proprietary',
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
    'langchain': {
    "name": 'LangChain',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Framework',
    "category": 'LLM Framework',
    "installer": {
        "type": 'uv',
        "pkg": 'langchain'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import langchain; print(langchain.__version__)"',
        "default_port": None
    },
    "deps": [],
    "description": 'Framework for LLM-powered application development.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'loop_engineering': {
    "name": 'Loop Engineering',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Hands',
    "category": 'Dev Automation',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/loop-engineering'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'loop-engineering --help',
        "default_port": None
    },
    "deps": [],
    "description": 'Development loop automation and CI/CD orchestration.',
    "license": 'MIT',
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
    'mcp_drift_state_tracker': {
    "name": 'MCP Drift State Tracker',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Code Audit',
    "category": 'MCP Server',
    "installer": {
        "type": 'git_node',
        "pkg": 'https://git.dcos.net/dcosnet/MCP-Drift-State-Tracker.git',
        "post_install": 'npm install && npm run build',
        "update_cmd": 'git pull --ff-only && npm install && npm run build'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/mcp_drift_state_tracker && node dist/index.js',
        "default_port": None
    },
    "deps": [],
    "description": 'Industrial-grade MCP server that enforces code completeness, intercepts context erosion, and neutralizes LLM laziness across multi-language repository workspaces. Pure TypeScript with JSON-driven language profiles (20+ languages).',
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": True,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/mcp_drift_state_tracker',
        "config": 'configs/mcp_drift_state_tracker',
        "logs": 'logs/mcp_drift_state_tracker'
    }
    },
    'n8n': {
    "name": 'n8n',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Workflow Orchestrator',
    "category": 'Workflow Automation',
    "installer": {
        "type": 'npm',
        "pkg": 'n8n',
        "env_overrides": {
            'NODE_PATH': '{tools_root}/n8n/node_modules'
        }
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'npx n8n start --port {port} --data-dir {workspaces_root}/n8n',
        "default_port": 5678
    },
    "deps": [],
    "description": 'Ops-oriented workflow automation for multi-step agent orchestration beyond single-turn tool calls.',
    "license": 'Sustainable-Use',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/n8n',
        "data": 'workspaces/n8n',
        "logs": 'logs/n8n'
    }
    },
    'nightshift': {
    "name": 'NightShift',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Scheduler',
    "category": 'Task Runner',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/nightshift',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/nightshift && python3 -m nightshift serve --port {port}',
        "default_port": 8800
    },
    "deps": [],
    "description": 'Scheduled task execution and background job runner.',
    "license": 'Proprietary',
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
    'nvidia_agent_skills': {
    "name": 'NVIDIA Agent Skills',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Skills Collection',
    "category": 'Skills Bundle',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/NVIDIA/agent-skills'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'ls {tools_root}/nvidia_agent_skills',
        "default_port": None
    },
    "deps": ['cuda'],
    "description": 'NVIDIA-curated agent skill definitions and tools.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": True
    }
    },
    'openhands': {
    "name": 'OpenHands',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Autonomous Coder',
    "category": 'AI Coding Agent',
    "installer": {
        "type": 'git_node',
        "pkg": 'https://github.com/All-Hands-AI/OpenHands.git',
        "update_cmd": 'git pull --ff-only && pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        # OpenHands binds its own web UI to localhost:{port}.  Its LLM
        # calls go through LLM_CONFIG which we force to the local
        # LiteLLM proxy (default port 4000) via OPENAI_API_BASE +
        # OPENAI_API_KEY env vars.  OpenHands reads these on startup.
        "cmd": 'cd {tools_root}/openhands && OPENAI_API_BASE=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local python -m openhands.server --port {port}',
        "default_port": 3000
    },
    "deps": ['ollama', 'litellm'],
    "description": 'Autonomous AI software engineer. Plans, writes, debugs, and executes code in sandboxed environments with full terminal access, file management, and web browsing. LLM calls forced to localhost via OPENAI_API_BASE=http://127.0.0.1:4000/v1 (LiteLLM proxy).',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/openhands',
        "config": 'workspaces/openhands/config',
        "cache": 'cache/openhands',
        "logs": 'logs/openhands'
    }
    },
    'ponytail': {
    "name": 'Ponytail',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Code Gen',
    "category": 'Code Generation',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/ponytail'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'ponytail generate',
        "default_port": None
    },
    "deps": ['ollama'],
    "description": 'AI-powered code generation and refactoring tool.',
    "license": 'Proprietary',
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
    'promptops': {
    "name": 'PromptOps.it',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Prompt Management',
    "category": 'Prompt Tooling',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/promptops'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'promptops --help',
        "default_port": None
    },
    "deps": [],
    "description": 'Prompt versioning, testing, and operations toolkit.',
    "license": 'Proprietary',
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
    'skillspector': {
    "name": 'Skillspector',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Analysis',
    "category": 'Skill Inspection',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/skillspector'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'skillspector inspect',
        "default_port": None
    },
    "deps": [],
    "description": 'Ollama skill definition inspector and validator.',
    "license": 'Proprietary',
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
    'spec_kit': {
    "name": 'Spec Kit',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Documentation',
    "category": 'Spec Writer',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/spec-kit'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'spec-kit init',
        "default_port": None
    },
    "deps": [],
    "description": 'Automated specification and requirement document generator.',
    "license": 'Proprietary',
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
    'synapscli': {
    "name": 'SynapsCLI',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Agent Runtime',
    "category": 'AI Agent',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/HaseebKhalid1507/SynapsCLI',
        "cmd": 'cargo build --release'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'synapscli',
        "default_port": None
    },
    "deps": [],
    "description": 'High-performance terminal-native AI agent runtime in Rust. Interactive LLM chat, parallel agent orchestration, and autonomous supervision.',
    "license": 'Proprietary',
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
    'wayland_ai': {
    "name": 'Wayland AI',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Agent Orchestrator',
    "category": 'AI Agent',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/ferroxlabs/wayland',
        "cmd": 'npx @ferroxlabs/wayland-core'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'wayland',
        "default_port": None
    },
    "deps": [],
    "description": 'Local-first desktop AI agent that unifies Claude Code, Codex, Gemini, Qwen, and 12+ coding assistants under a single Rust-powered orchestration engine. MCP-native, sandboxed tool execution.',
    "license": 'Proprietary',
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

    # ── L9: Observability ──────────────────────────────────────
    'glances': {
    "name": 'Glances',
    "level": 7,
    "layer": 'Observability',
    "role": 'Dashboard',
    "category": 'Metrics',
    "installer": {
        "type": 'pacman',
        "pkg": 'glances'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'glances -w --port {port}',
        "default_port": 61208
    },
    "deps": [],
    "description": 'Cross-platform system monitoring tool.',
    "license": 'LGPL-3.0',
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
    'grafana': {
    "name": 'Grafana',
    "level": 7,
    "layer": 'Observability',
    "role": 'Dashboard',
    "category": 'Visualization',
    "installer": {
        "type": 'pacman',
        "pkg": 'grafana'
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'grafana-server',
        "default_port": 3000
    },
    "deps": [],
    "description": 'Multi-source observability dashboards and visualization.',
    "license": 'AGPL-3.0',
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
    'grafana_alloy': {
    "name": 'Grafana Alloy',
    "level": 7,
    "layer": 'Observability',
    "role": 'Collector',
    "category": 'Telemetry',
    "installer": {
        "type": 'script',
        "pkg": 'grafana/alloy',
        "cmd": 'mkdir -p {tools_root}/grafana_alloy/bin && curl -fsSL -o {tools_root}/grafana_alloy/bin/alloy https://github.com/grafana/alloy/releases/latest/download/alloy-linux-amd64 && chmod +x {tools_root}/grafana_alloy/bin/alloy'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'alloy run --server.http.listen-port={port}',
        "default_port": 12345
    },
    "deps": ['prometheus'],
    "description": 'OpenTelemetry collector with Prometheus integration.',
    "license": 'Apache-2.0',
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
    'hermes_dashboard_page': {
    "name": 'Hermes Dashboard',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Dashboard',
    "category": 'Ecosystem Dashboard',
    "installer": {
        "type": 'npm',
        "pkg": 'hermes-dashboard'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'hermes dashboard --port {port}',
        "default_port": 17050
    },
    "deps": ['ollama'],
    "description": 'Hermes ecosystem monitoring dashboard.',
    "license": 'Proprietary',
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
    'latitude': {
    "name": 'Latitude',
    "level": 7,
    "layer": 'Observability',
    "role": 'Evaluation',
    "category": 'LLM Evaluation',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/latitude',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/latitude && python3 -m latitude serve --port {port}',
        "default_port": 9300
    },
    "deps": ['ollama'],
    "description": 'LLM output evaluation and benchmarking platform.',
    "license": 'Proprietary',
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
    'opik': {
    "name": 'Opik',
    "level": 7,
    "layer": 'Observability',
    "role": 'LLM Tracing',
    "category": 'AI Observability',
    "installer": {
        "type": 'uv',
        "pkg": 'opik'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'opik serve --port {port}',
        "default_port": 3000
    },
    "deps": [],
    "description": 'Open-source LLM observability and tracing platform.',
    "license": 'Proprietary',
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
    'prometheus': {
    "name": 'Prometheus',
    "level": 7,
    "layer": 'Observability',
    "role": 'Metrics Collector',
    "category": 'Metrics',
    "installer": {
        "type": 'pacman',
        "pkg": 'prometheus'
    },
    "launcher": {
        "type": 'systemd',
        "cmd": 'prometheus',
        "default_port": 9090
    },
    "deps": [],
    "description": 'Open-source monitoring and alerting toolkit.',
    "license": 'Apache-2.0',
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
    'pulse_ai': {
    "name": 'Pulse AI',
    "level": 7,
    "layer": 'Observability',
    "role": 'Health Monitor',
    "category": 'AI Monitoring',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/pulse-ai',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/pulse_ai && python3 -m pulse serve --port {port}',
        "default_port": 8900
    },
    "deps": [],
    "description": 'AI service health monitoring and auto-recovery.',
    "license": 'Proprietary',
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

    # ── L10: Intelligent Routing ───────────────────────────────
    'autogen': {
    "name": 'AutoGen',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Brain',
    "category": 'Agent Workflow',
    "installer": {
        "type": 'pipx',
        "pkg": 'pyautogen'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'autogen',
        "default_port": None
    },
    "deps": [],
    "description": 'Enable next-gen LLM applications with multiple conversable agents.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'crewai': {
    "name": 'CrewAI',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Brain',
    "category": 'Agent Workflow',
    "installer": {
        "type": 'pipx',
        "pkg": 'crewai'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'crewai',
        "default_port": None
    },
    "deps": [],
    "description": 'Framework for orchestrating role-playing autonomous AI agents.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'everos_memory': {
    "name": 'EverOS Memory',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Memory',
    "category": 'Persistent Memory',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/everos-memory',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/everos_memory && python3 -m everos serve --port {port}',
        "default_port": 9200
    },
    "deps": [],
    "description": 'Persistent long-term memory system for AI agents.',
    "license": 'Proprietary',
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
    'glassmind': {
    "name": 'GlassMind',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Reasoning',
    "category": 'Reasoning Engine',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/glassmind',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/glassmind && python3 -m glassmind serve --port {port}',
        "default_port": 9400
    },
    "deps": ['ollama'],
    "description": 'Transparent reasoning and chain-of-thought engine.',
    "license": 'Proprietary',
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
    'mnemo_cortex': {
    "name": 'Mnemo Cortex',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Memory',
    "category": 'Cortex Memory',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/mnemo-cortex',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/mnemo_cortex && python3 -m mnemo_cortex serve --port {port}',
        "default_port": 7200
    },
    "deps": ['ollama'],
    "description": 'Hierarchical cortex memory for AI agents.',
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
    'odysseus': {
    "name": 'Odysseus',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Reasoning',
    "category": 'Reasoning Engine',
    "installer": {
        "type": 'pip',
        "pkg": 'odysseus'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/odysseus/ && ./.venv/bin/uvicorn app:app --host 127.0.0.1 --port {port}',
        "default_port": 7000
    },
    "deps": ['ollama'],
    "description": 'Local reasoning and orchestration agent.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/odysseus',
        "config": 'configs/odysseus',
        "logs": 'logs/odysseus'
    }
    },
    'openai_swarm': {
    "name": 'OpenAI Swarm',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Multi-Agent',
    "category": 'Agent Framework',
    "installer": {
        "type": 'uv',
        "pkg": 'swarm'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'python3 -c "import swarm; print(\'ok\')"',
        "default_port": None
    },
    "deps": [],
    "description": 'OpenAI multi-agent orchestration framework.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'openbrain': {
    "name": 'OpenBrain',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Brain',
    "category": 'Reasoning Engine',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/openbrain',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/openbrain && python3 -m openbrain serve --port {port}',
        "default_port": 7100
    },
    "deps": ['ollama'],
    "description": 'Open-source reasoning and cognitive engine.',
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

    # ── L11: User Interfaces ───────────────────────────────────
    'anythingllm': {
    "name": 'AnythingLLM',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Face',
    "category": 'Chat',
    "installer": {
        "type": 'git_node',
        "pkg": 'https://github.com/Mintplex-Labs/anything-llm.git',
        "update_cmd": 'git pull --ff-only && yarn install'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/anythingllm && yarn dev',
        "default_port": 3001
    },
    "deps": [],
    "description": 'Full-stack application for conversational AI.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/anythingllm',
        "config": 'configs/anythingllm',
        "data": 'data/anythingllm',
        "logs": 'logs/anythingllm'
    }
    },
    'dashy': {
    "name": 'Dashy',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Dashboard',
    "category": 'Homepage',
    "installer": {
        "type": 'npm',
        "pkg": 'dashy'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'dashy --port {port}',
        "default_port": 3000
    },
    "deps": [],
    "description": 'Highly customizable dashboard and homepage.',
    "license": 'Proprietary',
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
    'dify': {
    "name": 'Dify',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Pipeline Orchestrator',
    "category": 'Pipeline',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/langgenius/dify.git'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/dify/api && poetry run flask run --host 0.0.0.0 --port={port}',
        "default_port": 5001
    },
    "deps": ['postgresql', 'redis', 'python', 'node'],
    "description": 'LLM application development platform (native install). Requires Poetry, Node.js 18+, FFmpeg. Backend (Flask) + Celery worker + Next.js frontend run as separate services.',
    "license": 'Dify-OSL',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/dify',
        "config": 'configs/dify',
        "data": 'data/dify',
        "logs": 'logs/dify'
    }
    },
    'flowise': {
    "name": 'Flowise',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Face',
    "category": 'Workflow',
    "installer": {
        "type": 'npm',
        "pkg": 'flowise'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'npx flowise start --port {port}',
        "default_port": 3000
    },
    "deps": [],
    "description": 'Drag & drop UI to build customized LLM flows.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/flowise',
        "data": 'data/flowise',
        "logs": 'logs/flowise'
    }
    },
    'forge': {
    "name": 'Forge (A1111)',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Face',
    "category": 'Image Generation',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/AUTOMATIC1111/stable-diffusion-webui-forge',
        "env_overrides": {
            'HF_HOME': '{base_dir}/cache/huggingface',
            'DIFFUSERS_CACHE': '{base_dir}/cache/huggingface'
        }
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/forge && python3 launch.py --port {port}',
        "default_port": 7860
    },
    "deps": ['cuda'],
    "description": 'Stable Diffusion WebUI Forge (optimized fork).',
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/forge',
        "config": 'configs/forge',
        "data": 'data/forge',
        "cache": 'cache/forge',
        "logs": 'logs/forge'
    }
    },
    'hermes': {
    "name": 'Hermes',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Agent',
    "category": 'AI Agent',
    "installer": {
        "type": 'npm',
        "pkg": 'hermes-ai'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'hermes dashboard --port {port} --data-dir {workspaces_root}/hermes & hermes desktop --data-dir {workspaces_root}/hermes',
        "default_port": 17050
    },
    "deps": ['ollama'],
    "description": 'Unified desktop and dashboard environment for the AI ecosystem.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/hermes',
        "data": 'workspaces/hermes',
        "logs": 'logs/hermes'
    }
    },
    'hermes_desktop': {
    "name": 'Hermes Desktop',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Face',
    "category": 'Desktop Agent',
    "installer": {
        "type": 'npm',
        "pkg": 'hermes-desktop'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'hermes desktop',
        "default_port": None
    },
    "deps": ['ollama'],
    "description": 'Hermes desktop agent environment.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'invokeai': {
    "name": 'InvokeAI',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Face',
    "category": 'Image Generation',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/invoke-ai/InvokeAI',
        "env_overrides": {
            'HF_HOME': '{base_dir}/cache/huggingface',
            'DIFFUSERS_CACHE': '{base_dir}/cache/huggingface'
        }
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/invokeai && invokeai --host 0.0.0.0 --port {port}',
        "default_port": 9090
    },
    "deps": ['cuda'],
    "description": 'Professional AI image generation workspace.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/invokeai',
        "config": 'configs/invokeai',
        "data": 'data/invokeai',
        "cache": 'cache/invokeai',
        "logs": 'logs/invokeai'
    }
    },
    'langflow': {
    "name": 'LangFlow',
    "level": 5,
    "layer": 'Orchestrators',
    "role": 'Visual Builder',
    "category": 'Workflow Builder',
    "installer": {
        "type": 'uv',
        "pkg": 'langflow',
        "env_overrides": {
            'LANGFLOW_CONFIG_DIR': '{base_dir}/configs/langflow'
        }
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'langflow run --port {port}',
        "default_port": 7860
    },
    "deps": [],
    "description": 'Visual framework for multi-agent and RAG workflows.',
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/langflow',
        "config": 'configs/langflow',
        "cache": 'cache/langflow',
        "logs": 'logs/langflow'
    }
    },
    'librechat': {
    "name": 'LibreChat',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Agent Frontend',
    "category": 'Chat Agent Platform',
    "installer": {
        "type": 'git_node',
        "pkg": 'https://github.com/danny-avila/LibreChat.git',
        "update_cmd": 'git pull --ff-only && yarn install && yarn build'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/librechat && API_PLUGINS=false PORT={port} NODE_ENV=production yarn backend',
        "default_port": 3080
    },
    "deps": ['ollama'],
    "description": "Multi-provider chat agent platform with native OpenAI tool-calling, the default agent frontend for AI-LSC's agentic orchestration.",
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/librechat',
        "config": 'configs/librechat',
        "data": 'data/librechat',
        "logs": 'logs/librechat'
    }
    },
    'local_llm_launcher': {
    "name": 'Local LLM Launcher',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Face',
    "category": 'Desktop Launcher',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/local-llm-launcher-gui'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'cd {tools_root}/local_llm_launcher && python3 main.py',
        "default_port": None
    },
    "deps": ['ollama'],
    "description": 'GUI launcher and manager for local LLMs.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'openjarvis': {
    "name": 'OpenJarvis',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Central Intelligence',
    "category": 'AI Assistant Platform',
    "installer": {
        "type": 'git_node',
        "pkg": 'https://github.com/openjarvis/openjarvis.git',
        "post_install": 'npm install && npm run build'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/openjarvis && npm start -- --port {port}',
        "default_port": 17070
    },
    "deps": ['ollama', 'qdrant'],
    "description": 'Central AI assistant platform with multi-modal I/O, memory integration, agentic task execution, and unified dashboard. The brain of the intelligent stack.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/openjarvis',
        "config": 'configs/openjarvis',
        "data": 'workspaces/openjarvis',
        "cache": 'cache/openjarvis',
        "logs": 'logs/openjarvis'
    }
    },
    'openwebui': {
    "name": 'Open WebUI',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Face',
    "category": 'Chat Frontend',
    "installer": {
        "type": 'uv',
        "pkg": 'open-webui',
        "env_overrides": {
            'OPEN_WEBUI_CONFIG_DIR': '{base_dir}/configs/openwebui'
        }
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'open-webui serve --port {port} --data-dir {workspaces_root}/openwebui',
        "default_port": 8080
    },
    "deps": ['ollama'],
    "description": 'Extensible frontend for LLMs.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/openwebui',
        "config": 'configs/openwebui',
        "data": 'workspaces/openwebui',
        "logs": 'logs/openwebui'
    }
    },

    # ── L12: DevOps ────────────────────────────────────────────
    'ansible': {
    "name": 'Ansible',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Configuration Management',
    "category": 'Config Management',
    "installer": {
        "type": 'pacman',
        "pkg": 'ansible'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'ansible --version',
        "default_port": None
    },
    "deps": [],
    "description": 'Agentless IT automation and configuration management.',
    "license": 'GPL-3.0',
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
    'aws_cdk': {
    "name": 'AWS CDK',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Infrastructure as Code',
    "category": 'IaC',
    "installer": {
        "type": 'npm',
        "pkg": 'aws-cdk'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'cdk --version',
        "default_port": None
    },
    "deps": [],
    "description": 'Cloud Development Kit — define AWS CloudFormation in code.',
    "license": 'Apache-2.0',
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
    'bicep': {
    "name": 'Bicep',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Infrastructure as Code',
    "category": 'IaC',
    "installer": {
        "type": 'npm',
        "pkg": '@azure/bicep'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'bicep --version',
        "default_port": None
    },
    "deps": [],
    "description": 'Azure domain-specific language for declarative infrastructure.',
    "license": 'MIT',
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
    'container_tool': {
    "name": 'Container Toolkit',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Isolation',
    "category": 'Sandbox',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/container'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'container --help',
        "default_port": None
    },
    "deps": [],
    "description": 'Lightweight container sandbox for code execution.',
    "license": 'Proprietary',
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
    'crossplane': {
    "name": 'Crossplane',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Infrastructure as Code',
    "category": 'IaC Control Plane',
    "installer": {
        "type": 'custom',
        "pkg": 'https://docs.crossplane.io/v2/getting-started/install/'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'crossplane --help',
        "default_port": None
    },
    "deps": ['kubectl'],
    "description": 'Kubernetes-native cloud infrastructure control plane.',
    "license": 'Apache-2.0',
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
    'homelab': {
    "name": 'Homelab',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Infrastructure as Code',
    "category": 'Provisioning',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/khuedoan/homelab',
        "cmd": ''
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'homelab',
        "default_port": None
    },
    "deps": ['ansible'],
    "description": 'Fully automated homelab provisioning from empty disk to running services in one command. IaC/GitOps: Packer + Terraform + Ansible + k3s + ArgoCD.',
    "license": 'Proprietary',
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
    'opensandbox': {
    "name": 'OpenSandbox',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Isolation',
    "category": 'Sandbox',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/opensandbox',
        "post_install": 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 2>/dev/null || .venv/bin/pip install -e .'
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/opensandbox && python3 serve.py --port {port}',
        "default_port": 9100
    },
    "deps": [],
    "description": 'Secure sandboxed execution environment for AI agents.',
    "license": 'Proprietary',
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
    'opentofu': {
    "name": 'OpenTofu',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Infrastructure as Code',
    "category": 'IaC',
    "installer": {
        "type": 'custom',
        "pkg": 'https://opentofu.org/docs/intro/install/'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'tofu version',
        "default_port": None
    },
    "deps": [],
    "description": 'Open-source Terraform fork maintained by the Linux Foundation.',
    "license": 'MPL-2.0',
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
    'pulumi': {
    "name": 'Pulumi',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Infrastructure as Code',
    "category": 'IaC',
    "installer": {
        "type": 'npm',
        "pkg": '@pulumi/pulumi'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'pulumi version',
        "default_port": None
    },
    "deps": [],
    "description": 'IaC platform using real programming languages (Python, TypeScript, Go).',
    "license": 'Apache-2.0',
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
    'puppet': {
    "name": 'Puppet',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Configuration Management',
    "category": 'Config Management',
    "installer": {
        "type": 'pacman',
        "pkg": 'puppet'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'puppet --version',
        "default_port": None
    },
    "deps": [],
    "description": 'Declarative configuration management tool.',
    "license": 'Proprietary',
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
    'sst': {
    "name": 'SST (Serverless Stack)',
    "level": 2,
    "layer": 'Development Environment',
    "role": 'Infrastructure as Code',
    "category": 'Serverless Framework',
    "installer": {
        "type": 'npm',
        "pkg": 'sst'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'sst --version',
        "default_port": None
    },
    "deps": [],
    "description": 'Framework for building full-stack apps on your own infrastructure.',
    "license": 'MIT',
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
    'stack_exporter': {
    "name": 'Stack Container Packager',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Runtime Packaging',
    "category": 'OCI Export',
    "installer": {
        "type": 'pacman',
        "pkg": 'podman'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'podman --version',
        "default_port": None
    },
    "deps": [],
    "description": 'Compiles validated pipeline matrices into Podman/Docker specs.',
    "license": 'MIT',
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
    'terraform': {
    "name": 'Terraform',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Infrastructure as Code',
    "category": 'IaC',
    "installer": {
        "type": 'pacman',
        "pkg": 'terraform'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'terraform version',
        "default_port": None
    },
    "deps": [],
    "description": 'Infrastructure as Code provisioning tool.',
    "license": 'BSL-1.1',
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
    'terragrunt': {
    "name": 'Terragrunt',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Infrastructure as Code',
    "category": 'IaC Wrapper',
    "installer": {
        "type": 'custom',
        "pkg": 'https://terragrunt.gruntwork.io/docs/getting-started/install/'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'terragrunt --version',
        "default_port": None
    },
    "deps": ['terraform'],
    "description": 'Thin wrapper for Terraform providing DRY config and remote state.',
    "license": 'MIT',
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

    # ── L13: Knowledge Management ──────────────────────────────
    'calibre': {
    "name": 'Calibre',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Library Manager',
    "category": 'Ebook Library',
    "installer": {
        "type": 'pacman',
        "pkg": 'calibre'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'calibre',
        "default_port": None
    },
    "deps": [],
    "description": 'E-book library management and converter.',
    "license": 'GPL-3.0',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'career_ops': {
    "name": 'Career Ops',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Assessment',
    "category": 'Skill Analysis',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/career-ops'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'career-ops analyze',
        "default_port": None
    },
    "deps": [],
    "description": 'Career skill assessment and gap analysis tool.',
    "license": 'Proprietary',
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
    'joplin': {
    "name": 'Joplin',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Note Taking',
    "category": 'Notes',
    "installer": {
        "type": 'pacman',
        "pkg": 'joplin'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'joplin',
        "default_port": None
    },
    "deps": [],
    "description": 'Open-source note taking and to-do application.',
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'kanban': {
    "name": 'Kanban Board',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Planning',
    "category": 'Project Management',
    "installer": {
        "type": 'npm',
        "pkg": 'kanban-board'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'kanban',
        "default_port": None
    },
    "deps": [],
    "description": 'Local kanban board for task and sprint management.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'logseq': {
    "name": 'Logseq',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Knowledge Graph',
    "category": 'Outliner',
    "installer": {
        "type": 'npm',
        "pkg": 'logseq'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'logseq',
        "default_port": None
    },
    "deps": [],
    "description": 'Privacy-first knowledge graph outliner.',
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'mnemosyne': {
    "name": 'Mnemosyne',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Learning',
    "category": 'Spaced Repetition',
    "installer": {
        "type": 'pipx',
        "pkg": 'mnemosyne'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'mnemosyne',
        "default_port": None
    },
    "deps": [],
    "description": 'Spaced repetition flashcard program with AI integration.',
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'obsidian': {
    "name": 'Obsidian',
    "level": 8,
    "layer": 'User Interfaces',
    "role": 'Knowledge Graph',
    "category": 'Notes',
    "installer": {
        "type": 'pacman',
        "pkg": 'obsidian'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'obsidian',
        "default_port": None
    },
    "deps": [],
    "description": 'Knowledge graph note-taking and markdown editor.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
    'paperlessngx': {
    "name": 'Paperless-ngx',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Document Archive',
    "category": 'Document Management',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/paperless-ngx/paperless-ngx',
        "env_overrides": {
            'PAPERLESS_DATA_DIR': '{base_dir}/data/paperlessngx'
        }
    },
    "launcher": {
        "type": 'tmux',
        "cmd": 'cd {tools_root}/paperlessngx && python3 manage.py runserver 0.0.0.0:{port}',
        "default_port": 8000
    },
    "deps": ['postgresql', 'redis'],
    "description": 'Document management system with OCR.',
    "license": 'GPL-3.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": 'tools/paperlessngx',
        "config": 'configs/paperlessngx',
        "data": 'data/paperlessngx',
        "logs": 'logs/paperlessngx'
    }
    },
    'pm_skills': {
    "name": 'PM Skills',
    "level": 9,
    "layer": 'DevOps',
    "role": 'Skills Collection',
    "category": 'Project Management',
    "installer": {
        "type": 'git',
        "pkg": 'https://github.com/nicely-done/pm-skills'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'pm-skills plan',
        "default_port": None
    },
    "deps": [],
    "description": 'AI-assisted project management and planning skills.',
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": True
    }
    },
    'zotero': {
    "name": 'Zotero',
    "level": 10,
    "layer": 'Knowledge Management',
    "role": 'Reference Manager',
    "category": 'Academic References',
    "installer": {
        "type": 'pacman',
        "pkg": 'zotero'
    },
    "launcher": {
        "type": 'desktop',
        "cmd": 'zotero',
        "default_port": None
    },
    "deps": [],
    "description": 'Free reference management for researchers.',
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
    },
}
