"""Registry entries for the GPU Runtimes layer (L3).

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
    'cuda': {
    "name": "CUDA Toolkit",
    "level": 3,
    "layer": "GPU Runtimes",
    "role": "Acceleration",
    "category": "GPU",
    "installer": {
        "type": "pacman",
        "pkg": "cuda"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "nvcc --version",
        "default_port": None
    },
    "deps": [],
    "description": "NVIDIA CUDA parallel computing platform.",
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
    'apex': {
    "name": "NVIDIA Apex",
    "level": 3,
    "layer": "GPU Runtimes",
    "role": "Optimization",
    "category": "Mixed Precision",
    "installer": {
        "type": "uv",
        "pkg": "apex"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 -c \"import apex; print(apex.__version__)\"",
        "default_port": None
    },
    "deps": [
        "cuda"
    ],
    "description": "NVIDIA mixed precision and distributed training.",
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
}