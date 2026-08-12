"""Registry entries for the Engines layer (L4).

Each entry follows the standard registry schema:

- ``name``: human-readable tool name
- ``level``: 10-layer taxonomy level (1-10)
- ``layer``: this layer name
- ``role``: role within the layer
- ``category``: functional category
- ``installer``: installation method
- ``launcher``: process launcher specification
- ``deps``: list of required tool IDs
- ``description``: short description
- ``flags``: optional boolean flags

This module is consumed by
:mod:`ai_lsc.registry.loader`.
"""

TOOLS: dict[str, dict] = {
    'ollama': {
    "name": "Ollama",
    "level": 4,
    "layer": "Engines",
    "role": "Engine",
    "category": "LLM Runtime",
    "installer": {
        "type": "script",
        "cmd": "curl -fsSL https://ollama.com/install.sh | sh"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "OLLAMA_HOST=0.0.0.0:{port} OLLAMA_MODELS={models_root}/ollama ollama serve",
        "default_port": 11434
    },
    "deps": [],
    "description": "Local LLM runner and model manager.",
    "license": 'MIT',
    "flags": {
        "is_ollama": True,
        "has_cli": False,
        "has_gui": False,
        "has_web": True,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'llamacpp': {
    "name": "llama.cpp",
    "level": 4,
    "layer": "Engines",
    "role": "Engine",
    "category": "LLM Runtime",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/ggerganov/llama.cpp"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/llamacpp && make && ./server --port {port}",
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
    'koboldcpp': {
    "name": "KoboldCPP",
    "level": 4,
    "layer": "Engines",
    "role": "Engine",
    "category": "LLM Runtime",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/LostRuins/koboldcpp"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/koboldcpp && make && ./koboldcpp --port {port}",
        "default_port": 5001
    },
    "deps": [],
    "description": "GGUF-based LLM inference with CUDA/Vulkan.",
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
    'llamafile': {
    "name": "Llamafile",
    "level": 4,
    "layer": "Engines",
    "role": "Engine",
    "category": "Single-File LLM",
    "installer": {
        "type": "script",
        "cmd": "curl -LO https://github.com/Mozilla-Ocho/llamafile/releases/latest/download/llamafile && chmod +x llamafile"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "{tools_root}/bin/llamafile",
        "default_port": None
    },
    "deps": [],
    "description": "Distribute and run LLMs in a single file.",
    "license": 'Apache-2.0',
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
    'turbollm': {
    "name": "TurboLLM",
    "level": 4,
    "layer": "Engines",
    "role": "Engine",
    "category": "LLM Runtime",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/turbollm"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/turbollm && python3 -m turbollm serve --port {port}",
        "default_port": 8000
    },
    "deps": [
        "cuda"
    ],
    "description": "Fast LLM serving with tensor parallelism.",
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
    'airllm': {
    "name": "AirLLM",
    "level": 4,
    "layer": "Engines",
    "role": "Engine",
    "category": "Efficient LLM",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/liguodongiot/llm-airforce"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/airllm && python3 -m airllm serve --port {port}",
        "default_port": 8001
    },
    "deps": [
        "cuda"
    ],
    "description": "Memory-efficient 70B LLM inference on 4GB GPUs.",
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
    'locally_uncensored': {
    "name": "Locally-Uncensored",
    "level": 4,
    "layer": "Engines",
    "role": "Engine",
    "category": "Uncensored Models",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/locally-uncensored"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "ollama list",
        "default_port": None
    },
    "deps": [
        "ollama"
    ],
    "description": "Curated uncensored model collection and tooling.",
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
    'heretic': {
    "name": "Heretic",
    "level": 4,
    "layer": "Engines",
    "role": "Abliteration",
    "category": "Model Surgery",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/p-e-w/heretic",
        "post_install": "pip install -e ."
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 -c \"import heretic; print('ok')\"",
        "default_port": None
    },
    "deps": [
        "cuda"
    ],
    "description": "Fully automatic censorship/safety-alignment removal for transformer-based LLMs via optimized abliteration. Modifies model weights directly.",
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
}