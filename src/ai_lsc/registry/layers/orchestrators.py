"""Registry entries for the Orchestrators layer (L6).

Contains distributed compute, agent orchestration, workflow
engines, pipeline coordination, and multi-agent frameworks.
(LLM serving moved to Engines; routing/gateways to Routing;
coding agents to DevOps in the 11-layer taxonomy.)

This module is consumed by
:mod:`ai_lsc.registry.loader`.

Structural fields (layer, level) follow the 10-Layer Systems
Architecture Taxonomy; tools may be regrouped across files in a
future pass — the loader merges by tool, not by filename.
"""

TOOLS: dict[str, dict] = {
    'distcc': {
    "name": "DistCC",
    "level": 2,
    "layer": 'Development Runtime & Environment',
    "role": 'Distribution',
    "category": 'Distributed Compilation',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Scaling',
    "category": 'Distributed Compute',
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
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Coordination',
    "category": 'Cluster SSH',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Integration Library',
    "category": 'Integration Library',
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
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'RAG Flow Canvas',
    "category": 'RAG Flow Canvas',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Role-Playing Agent',
    "category": 'Role-Playing Agent',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Multi-Agent Framework',
    "category": 'Multi-Agent Framework',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Stateless Orchestration',
    "category": 'Stateless Orchestration',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Production Multi-Agent',
    "category": 'Production Multi-Agent',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/agno-agi/agno"
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Tool Integration',
    "category": 'Agent Toolkit',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Brain',
    "category": 'Reasoning Engine',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/NateBJones-Projects/OB1"
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Reasoning',
    "category": 'Agent Workflow',
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
    "filesystem": {
        "install": "tools/odysseus",
        "config": "configs/odysseus",
        "logs": "logs/odysseus",
    },
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
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Workflow Orchestrator',
    "category": 'Workflow',
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
    "filesystem": {
        "install": "tools/n8n",
        "data": "workspaces/n8n",
        "logs": "logs/n8n",
    },
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
    "level": 5,
    "layer": 'Intelligent API Routers & Proxies',
    "role": 'Curation Pipeline',
    "category": 'Curation Pipeline',
    "installer": {
        "type": "script",
        "cmd": "curl -L https://github.com/danielmiessler/fabric/releases/latest/download/fabric-linux-amd64 > {tools_root}/bin/fabric && chmod +x {tools_root}/bin/fabric",
        "pkg": "https://github.com/danielmiessler/fabric"
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Terminal Agent',
    "category": 'Terminal Agent',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Coordination Protocol',
    "category": 'Coordination Protocol',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/hivementality-ai/hivemind"
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Agent Daemon',
    "category": 'Agent Daemon',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Agent Shell',
    "category": 'Agent Shell',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/aporb/agentic-os"
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
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Context Integrity Core',
    "category": 'Context Integrity Core',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Reasoning',
    "category": 'Reasoning Engine',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/khodges42/glassMind"
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Process Manager',
    "category": 'Workflow Automation',
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
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Knowledge Graph Builder',
    "category": 'Claude Code Skill',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Resource Manager',
    "category": 'Infrastructure',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/headroomlabs-ai/headroom"
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
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'CI/CD Orchestration',
    "category": 'CI/CD Orchestration',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/lcajigasm/loop-engineering"
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Night Ops',
    "category": 'Workflow Automation',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/johndaskovsky/nightshift"
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
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Isolation',
    "category": 'Isolation',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/opensandbox-group/OpenSandbox"
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
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Code Refactoring',
    "category": 'Code Refactoring',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/DietrichGebert/ponytail"
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
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Prompt Tester',
    "category": 'Prompt Tester',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/llmhq-hub/promptops"
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Agent Discovery',
    "category": 'Multi-Agent',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/Panniantong/Agent-Reach"
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Algorithm',
    "category": 'AI Agent',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/aryaghan-mutum/algory"
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'OS Framework',
    "category": 'Agent OS',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/atlas-os/atlas"
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
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Gap Analyzer',
    "category": 'Gap Analyzer',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/santifer/career-ops"
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
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Isolation',
    "category": 'Isolation',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/NVIDIA/nvidia-container-toolkit"
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
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Sprint Planner',
    "category": 'Sprint Planner',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/product-on-purpose/pm-skills"
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
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Skill Auditor',
    "category": 'Skill Auditor',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/NVIDIA/skillspector"
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
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Requirement Builder',
    "category": 'Requirement Builder',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/github/spec-kit"
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Desktop Agent Core',
    "category": 'Desktop Agent Core',
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
    "layer": 'Multi-Agent Orchestration Runtimes',
    "role": 'Agent Framework',
    "category": 'Agent Framework',
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