"""Registry entries for the User Interfaces layer (L8).

Contains frontends, dashboards, chat UIs, image generation interfaces,
sensory interfaces (vision, speech, voice), and knowledge graph tools.

This module is consumed by
:mod:`ai_lsc.registry.loader`.
"""

TOOLS: dict[str, dict] = {
    'openwebui': {
    "name": "Open WebUI",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "Chat Frontend",
    "installer": {
        "type": "uv",
        "pkg": "open-webui"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "open-webui serve --port {port} --data-dir {workspaces_root}/openwebui",
        "default_port": 8080
    },
    "deps": [
        "ollama"
    ],
    "description": "Extensible frontend for LLMs.",
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
    'anythingllm': {
    "name": "AnythingLLM",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "Chat",
    "installer": {
        "type": "git_node",
        "pkg": "https://github.com/Mintplex-Labs/anything-llm.git"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/anythingllm && yarn dev",
        "default_port": 3001
    },
    "deps": [],
    "description": "Full-stack application for conversational AI.",
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
    'librechat': {
    "name": "LibreChat",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "Chat Agent Platform",
    "installer": {
        "type": "git_node",
        "pkg": "https://github.com/danny-avila/LibreChat.git",
        "update_cmd": "git pull --ff-only && yarn install && yarn build"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/librechat && API_PLUGINS=false PORT={port} NODE_ENV=production yarn backend",
        "default_port": 3080
    },
    "deps": [
        "ollama"
    ],
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
        "install": "tools/librechat",
        "config": "configs/librechat",
        "data": "data/librechat",
        "logs": "logs/librechat"
    }
},
    'flowise': {
    "name": "Flowise",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "Workflow",
    "installer": {
        "type": "npm",
        "pkg": "flowise"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "npx flowise start --port {port}",
        "default_port": 3000
    },
    "deps": [],
    "description": "Drag & drop UI to build customized LLM flows.",
    "license": 'Apache-2.0',
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
    'invokeai': {
    "name": "InvokeAI",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "Image Generation",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/invoke-ai/InvokeAI"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/invokeai && invokeai --host 0.0.0.0 --port {port}",
        "default_port": 9090
    },
    "deps": [
        "cuda"
    ],
    "description": "Professional AI image generation workspace.",
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
    'forge': {
    "name": "Forge (A1111)",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "Image Generation",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/AUTOMATIC1111/stable-diffusion-webui-forge"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/forge && python3 launch.py --port {port}",
        "default_port": 7860
    },
    "deps": [
        "cuda"
    ],
    "description": "Stable Diffusion WebUI Forge (optimized fork).",
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
    'dashy': {
    "name": "Dashy",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "Homepage",
    "installer": {
        "type": "npm",
        "pkg": "dashy"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "dashy --port {port}",
        "default_port": 3000
    },
    "deps": [],
    "description": "Highly customizable dashboard and homepage.",
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
    'obsidian': {
    "name": "Obsidian",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "Knowledge Graph Notes",
    "installer": {
        "type": "pacman",
        "pkg": "obsidian"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "obsidian",
        "default_port": None
    },
    "deps": [],
    "description": "Knowledge graph note-taking and markdown editor.",
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
    'hermes': {
    "name": "Hermes",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "Ecosystem Dashboard",
    "installer": {
        "type": "npm",
        "pkg": "hermes-ai"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "hermes dashboard --port {port} --data-dir {workspaces_root}/hermes & hermes desktop --data-dir {workspaces_root}/hermes",
        "default_port": 17050
    },
    "deps": [
        "ollama"
    ],
    "description": "Unified desktop and dashboard environment for the AI ecosystem.",
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
    'hermes_desktop': {
    "name": "Hermes Desktop",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "Desktop Agent",
    "installer": {
        "type": "npm",
        "pkg": "hermes-desktop"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "hermes desktop",
        "default_port": None
    },
    "deps": [
        "ollama"
    ],
    "description": "Hermes desktop agent environment.",
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
    'hermes_dashboard_page': {
    "name": "Hermes Dashboard",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "Dashboard",
    "installer": {
        "type": "npm",
        "pkg": "hermes-dashboard"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "hermes dashboard --port {port}",
        "default_port": 17050
    },
    "deps": [
        "ollama"
    ],
    "description": "Hermes ecosystem monitoring dashboard.",
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
    'local_llm_launcher': {
    "name": "Local LLM Launcher",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Face",
    "category": "LLM GUI",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/local-llm-launcher-gui"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "cd {tools_root}/local_llm_launcher && python3 main.py",
        "default_port": None
    },
    "deps": [
        "ollama"
    ],
    "description": "GUI launcher and manager for local LLMs.",
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
    "name": "OpenJarvis",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Central Intelligence",
    "category": "AI Assistant Platform",
    "installer": {
        "type": "git_node",
        "pkg": "https://github.com/openjarvis/openjarvis.git",
        "post_install": "npm install && npm run build"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/openjarvis && npm start -- --port {port}",
        "default_port": 17070
    },
    "deps": [
        "ollama",
        "qdrant"
    ],
    "description": "Central AI assistant platform with multi-modal I/O, memory integration, agentic task execution, and unified dashboard. The brain of the intelligent stack.",
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
        "install": "tools/openjarvis",
        "config": "configs/openjarvis",
        "data": "workspaces/openjarvis",
        "cache": "cache/openjarvis",
        "logs": "logs/openjarvis"
    }
},
    'deep_eye': {
    "name": "Deep Eye",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Vision",
    "category": "Computer Vision",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/deep-eye"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/deep_eye && python3 serve.py --port {port}",
        "default_port": 8100
    },
    "deps": [
        "ollama"
    ],
    "description": "Local computer vision analysis and description engine.",
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
    'parakeet': {
    "name": "Parakeet.cpp",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Senses",
    "category": "Speech Recognition",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/parakeet.cpp"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/parakeet && ./parakeet --port {port}",
        "default_port": 8300
    },
    "deps": [
        "cuda"
    ],
    "description": "C++ speech recognition with transformer architecture.",
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
    'luxtts': {
    "name": "LuxTTS",
    "level": 8,
    "layer": "User Interfaces",
    "role": "Voice",
    "category": "Text-to-Speech",
    "installer": {
        "type": "uv",
        "pkg": "luxtts"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "luxtts serve --port {port}",
        "default_port": 8500
    },
    "deps": [],
    "description": "High-quality local text-to-speech synthesis.",
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
}