"""Registry entries for the Orchestrators layer (L6).

Contains distributed compute, agent orchestration, workflow
engines, pipeline coordination, and multi-agent frameworks.
(LLM serving moved to Engines; routing/gateways to Routing;
coding agents to DevOps in the 11-layer taxonomy.)

This module is consumed by
:mod:`ai_lsc.registry.loader`.
"""

TOOLS: dict[str, dict] = {
    'distcc': {
    "name": "DistCC",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Distribution",
    "category": "Distributed Compilation",
    "installer": {
        "type": "pacman",
        "pkg": "distcc"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "distcc --version",
        "default_port": 3632
    },
    "deps": [],
    "description": "Distributed C/C++ compilation across multiple machines.",
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
    'ray': {
    "name": "Ray",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Scaling",
    "category": "Distributed Compute",
    "installer": {
        "type": "uv",
        "pkg": "ray"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "ray start --head --port {port}",
        "default_port": 8265
    },
    "deps": [],
    "description": "Unified framework for scaling AI and Python applications.",
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
    'pssh': {
    "name": "PSSH (Parallel SSH)",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Coordination",
    "category": "Cluster SSH",
    "installer": {
        "type": "pacman",
        "pkg": "pssh"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "pssh --version",
        "default_port": None
    },
    "deps": [],
    "description": "Parallel SSH tool for running commands on multiple hosts.",
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
    "name": "LangChain",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Orchestration",
    "category": "LLM Framework",
    "installer": {
        "type": "uv",
        "pkg": "langchain"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 -c \"import langchain; print(langchain.__version__)\"",
        "default_port": None
    },
    "deps": [],
    "description": "Framework for LLM-powered application development.",
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
    'langflow': {
    "name": "LangFlow",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Visual Builder",
    "category": "Workflow",
    "installer": {
        "type": "uv",
        "pkg": "langflow"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "langflow run --port {port}",
        "default_port": 7860
    },
    "deps": [],
    "description": "Visual framework for multi-agent and RAG workflows.",
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
    'crewai': {
    "name": "CrewAI",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Brain",
    "category": "Agent Workflow",
    "installer": {
        "type": "uv",
        "pkg": "crewai"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "crewai",
        "default_port": None
    },
    "deps": [],
    "description": "Framework for orchestrating role-playing autonomous AI agents.",
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
    'autogen': {
    "name": "AutoGen",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Brain",
    "category": "Agent Workflow",
    "installer": {
        "type": "uv",
        "pkg": "pyautogen"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "autogen",
        "default_port": None
    },
    "deps": [],
    "description": "Enable next-gen LLM applications with multiple conversable agents.",
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
    'openai_swarm': {
    "name": "OpenAI Swarm",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Multi-Agent",
    "category": "Agent Framework",
    "installer": {
        "type": "uv",
        "pkg": "swarm"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 -c \"import swarm; print('ok')\"",
        "default_port": None
    },
    "deps": [],
    "description": "OpenAI multi-agent orchestration framework.",
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
    "name": "Agno",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Agent Framework",
    "category": "AI Agent",
    "installer": {
        "type": "uv",
        "pkg": "agno"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 -c \"import agno; print(agno.__version__)\"",
        "default_port": None
    },
    "deps": [],
    "description": "Framework for building AI agents with tool calling and memory.",
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
    'nvidia_agent_skills': {
    "name": "NVIDIA Agent Skills",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Tool Integration",
    "category": "Agent Toolkit",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/NVIDIA/agent-skills"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "ls {tools_root}/nvidia_agent_skills",
        "default_port": None
    },
    "deps": [
        "cuda"
    ],
    "description": "NVIDIA-curated agent skill definitions and tools.",
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
    'openbrain': {
    "name": "OpenBrain",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Brain",
    "category": "Reasoning Engine",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/openbrain"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/openbrain && python3 -m openbrain serve --port {port}",
        "default_port": 7100
    },
    "deps": [
        "ollama"
    ],
    "description": "Open-source reasoning and cognitive engine.",
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
    "name": "Odysseus",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Reasoning",
    "category": "Agent Workflow",
    "installer": {
        "type": "uv",
        "pkg": "odysseus"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/odysseus/ && ./.venv/bin/uvicorn app:app --host 127.0.0.1 --port {port}",
        "default_port": 7000
    },
    "deps": [
        "ollama"
    ],
    "description": "Local reasoning and orchestration agent.",
    "license": 'MIT',
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
    'n8n': {
    "name": "n8n",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Workflow Orchestrator",
    "category": "Workflow Automation",
    "installer": {
        "type": "npm",
        "pkg": "n8n",
        "env_overrides": {
            "NODE_PATH": "{tools_root}/n8n/node_modules"
        }
    },
    "launcher": {
        "type": "tmux",
        "cmd": "npx n8n start --port {port} --data-dir {workspaces_root}/n8n",
        "default_port": 5678
    },
    "deps": [],
    "description": "Ops-oriented workflow automation for multi-step agent orchestration beyond single-turn tool calls.",
    "license": 'Sustainable-Use',
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
    "name": "Fabric",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Curation",
    "category": "AI Augmentation",
    "installer": {
        "type": "script",
        "cmd": "curl -L https://github.com/danielmiessler/fabric/releases/latest/download/fabric-linux-amd64 > {tools_root}/bin/fabric && chmod +x {tools_root}/bin/fabric"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "OPENAI_API_BASE=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local fabric",
        "default_port": None
    },
    "deps": [
        "litellm"
    ],
    "description": "Open-source framework for augmenting humans using AI. LLM calls forced to localhost via OPENAI_API_BASE=http://127.0.0.1:4000/v1 (LiteLLM proxy) — override via the service row port if you run a different local backend.",
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
    'synapscli': {
    "name": "SynapsCLI",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Agent",
    "category": "AI Agent",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/HaseebKhalid1507/SynapsCLI",
        "cmd": "cargo build --release"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "synapscli",
        "default_port": None
    },
    "deps": [],
    "description": "High-performance terminal-native AI agent runtime in Rust. Interactive LLM chat, parallel agent orchestration, and autonomous supervision.",
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
    'hivemind': {
    "name": "HiveMind",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Coordination",
    "category": "Multi-Agent",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/hivemind"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/hivemind && python3 -m hivemind serve --port {port}",
        "default_port": 8700
    },
    "deps": [
        "ollama"
    ],
    "description": "Distributed multi-agent coordination framework.",
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
    'hermes_agent': {
    "name": "Hermes Agent",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Agent",
    "category": "AI Agent",
    "installer": {
        "type": "npm",
        "pkg": "hermes-agent"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "hermes agent --port {port}",
        "default_port": 17051
    },
    "deps": [
        "ollama"
    ],
    "description": "Hermes autonomous agent runtime.",
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
    'agentic_os': {
    "name": "Agentic OS",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Hands",
    "category": "Agent OS",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/agentic-os"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/agentic_os && python3 main.py",
        "default_port": None
    },
    "deps": [
        "ollama"
    ],
    "description": "Autonomous agent operating system framework.",
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
    "name": "MCP Drift State Tracker",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Code Audit",
    "category": "MCP Server",
    "installer": {
        "type": "git_node",
        "pkg": "https://git.dcos.net/dcosnet/MCP-Drift-State-Tracker.git",
        "post_install": "npm install && npm run build",
        "update_cmd": "git pull --ff-only && npm install && npm run build"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/mcp_drift_state_tracker && node dist/index.js",
        "default_port": None
    },
    "deps": [],
    "description": "Industrial-grade MCP server that enforces code completeness, intercepts context erosion, and neutralizes LLM laziness across multi-language repository workspaces. Pure TypeScript with JSON-driven language profiles (20+ languages).",
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": True,
        "is_skills_collection": False
    }
},
    'glassmind': {
    "name": "GlassMind",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Reasoning",
    "category": "Reasoning Engine",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/glassmind"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/glassmind && python3 -m glassmind serve --port {port}",
        "default_port": 9400
    },
    "deps": [
        "ollama"
    ],
    "description": "Transparent reasoning and chain-of-thought engine.",
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
    "name": "Honcho",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Process Manager",
    "category": "Workflow Automation",
    "installer": {
        "type": "uv",
        "pkg": "honcho"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "honcho --version",
        "default_port": None
    },
    "deps": [],
    "description": "Python process manager for Procfile-based application orchestration.",
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
    "name": "Graphify",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Knowledge Graph Builder",
    "category": "Claude Code Skill",
    "installer": {
        "type": "uv",
        "pkg": "graphifyy"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "graphify --version",
        "default_port": None
    },
    "deps": [],
    "description": "Knowledge graph builder for code, docs, PDFs, and "
                  "images. Installs as a Claude Code skill (type "
                  "`/graphify .` in Claude Code) or runs standalone "
                  "via CLI. Builds interactive graph.html, Obsidian "
                  "vault, Wikipedia-style wiki, and persistent "
                  "graph.json from any folder. MCP stdio server mode "
                  "(`graphify --mcp`) lets other agents query the "
                  "graph. Uses Claude vision by default; can be "
                  "configured to use any OpenAI-compat endpoint "
                  "(MeshLLM, LiteLLM, Ollama) for extraction. PyPI "
                  "package is `graphifyy` (CLI is `graphify`).",
    "license": "MIT",
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": True,
        "is_skills_collection": False
    }
},
    'headroom': {
    "name": "Headroom",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Resource Manager",
    "category": "Infrastructure",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/headroom"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "headroom --version",
        "default_port": None
    },
    "deps": [],
    "description": "Resource management and capacity planning agent.",
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
    'loop_engineering': {
    "name": "Loop Engineering",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Engineering Loop",
    "category": "Workflow Automation",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/loop_engineering"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "loop_engineering --version",
        "default_port": None
    },
    "deps": [],
    "description": "Engineering workflow loop automation tool.",
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
    'nightshift': {
    "name": "Nightshift",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Night Ops",
    "category": "Workflow Automation",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/nightshift"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "nightshift --version",
        "default_port": None
    },
    "deps": [],
    "description": "Automated night-time operations and batch processing agent.",
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
    "name": "OpenSandbox",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Sandbox",
    "category": "Container Ops",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/opensandbox"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "opensandbox --version",
        "default_port": None
    },
    "deps": [],
    "description": "Sandboxed environment provisioning for agent execution.",
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
    'ponytail': {
    "name": "Ponytail",
    "level": 6,
    "layer": "Orchestrators",
    "role": "CI/CD",
    "category": "Workflow Automation",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/ponytail"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "ponytail --version",
        "default_port": None
    },
    "deps": [],
    "description": "CI/CD pipeline automation and management tool.",
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
    "name": "PromptOps",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Prompt Ops",
    "category": "AI Agent",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/promptops"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "promptops --version",
        "default_port": None
    },
    "deps": [],
    "description": "Prompt engineering and operations management agent.",
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
    'agent_reach': {
    "name": "Agent Reach",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Agent Discovery",
    "category": "Multi-Agent",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/agent_reach"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "agent_reach --version",
        "default_port": None
    },
    "deps": [],
    "description": "Multi-agent discovery and communication framework.",
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
    'algory': {
    "name": "Algory",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Algorithm",
    "category": "AI Agent",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/algory"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "algory --version",
        "default_port": None
    },
    "deps": [],
    "description": "Algorithm engine for AI agent task decomposition.",
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
    'atlas_os': {
    "name": "Atlas OS",
    "level": 6,
    "layer": "Orchestrators",
    "role": "OS Framework",
    "category": "Agent OS",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/atlas_os"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "atlas_os --version",
        "default_port": None
    },
    "deps": [],
    "description": "Agent operating system framework for orchestration.",
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
    'career_ops': {
    "name": "Career Ops",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Career Ops",
    "category": "Workflow Automation",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/career_ops"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "career_ops --version",
        "default_port": None
    },
    "deps": [],
    "description": "Workflow automation for career and professional operations.",
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
    'container_tool': {
    "name": "Container Tool",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Containerization",
    "category": "Container Ops",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/container_tool"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "container_tool --version",
        "default_port": None
    },
    "deps": [],
    "description": "Container orchestration and management toolkit.",
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
    'pm_skills': {
    "name": "PM Skills",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Project Management",
    "category": "Workflow Automation",
    "installer": {
        "type": "uv",
        "pkg": "pm-skills"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "pm_skills --version",
        "default_port": None
    },
    "deps": [],
    "description": "AI-powered project management skills toolkit.",
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
    "name": "Skillspector",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Skill Inspector",
    "category": "AI Agent",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/skillspector"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "skillspector --version",
        "default_port": None
    },
    "deps": [],
    "description": "AI agent skill inspection and analysis toolkit.",
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
    "name": "Spec Kit",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Specification",
    "category": "AI Agent",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/spec_kit"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "spec_kit --version",
        "default_port": None
    },
    "deps": [],
    "description": "Specification generation and management toolkit.",
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
    "name": "Wayland AI",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Agent Orchestrator",
    "category": "AI Agent",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/ferroxlabs/wayland",
        "post_install": "npx @ferroxlabs/wayland-core"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "wayland",
        "default_port": None
    },
    "deps": [],
    "description": "Local-first desktop AI agent that unifies Claude Code, Codex, Gemini, Qwen, and 12+ coding assistants under a single Rust-powered orchestration engine. MCP-native, sandboxed tool execution.",
    "license": "Proprietary",
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
    'letta': {
    "name": "Letta",
    "level": 6,
    "layer": "Orchestrators",
    "role": "Agent Framework",
    "category": "Agent Framework",
    "installer": {
        "type": "uv",
        "pkg": "letta"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "letta server --port {port}",
        "default_port": 8283
    },
    "deps": [],
    "description": "Stateful agent framework (MemGPT) with persistent memory, "
                  "self-editing agents, and a REST API server for agent "
                  "management.",
    "license": "Apache-2.0",
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

}