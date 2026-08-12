"""Registry entries for the Development Environment layer (L2).

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
    'python': {
    "name": "Python Environment",
    "level": 2,
    "layer": "Development Environment",
    "role": "Build System",
    "category": "Runtime",
    "installer": {
        "type": "pacman",
        "pkg": "python-pip"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 --version",
        "default_port": None
    },
    "deps": [],
    "description": "Python core interpreter and virtual environments.",
    "license": 'Python',
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
    'cupy': {
    "name": "CuPy",
    "level": 2,
    "layer": "Development Environment",
    "role": "GPU Acceleration",
    "category": "GPU Computing",
    "installer": {
        "type": "uv",
        "pkg": "cupy-cuda12x"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 -c \"import cupy; print(cupy.__version__)\"",
        "default_port": None
    },
    "deps": [
        "cuda"
    ],
    "description": "NumPy-compatible GPU array computing library.",
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
    'fd': {
    "name": "fd",
    "level": 2,
    "layer": "Development Environment",
    "role": "Search",
    "category": "Find Tool",
    "installer": {
        "type": "pacman",
        "pkg": "fd"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "fd --version",
        "default_port": None
    },
    "deps": [],
    "description": "Fast find command alternative.",
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
    'ripgrep': {
    "name": "ripgrep (rg)",
    "level": 2,
    "layer": "Development Environment",
    "role": "Search",
    "category": "Search Tool",
    "installer": {
        "type": "pacman",
        "pkg": "ripgrep"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "rg --version",
        "default_port": None
    },
    "deps": [],
    "description": "Fast recursive search tool (grep replacement).",
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
    "name": "tree-sitter",
    "level": 2,
    "layer": "Development Environment",
    "role": "Parsing",
    "category": "Parser",
    "installer": {
        "type": "uv",
        "pkg": "tree-sitter"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "tree-sitter --version",
        "default_port": None
    },
    "deps": [],
    "description": "Incremental parsing system for source code.",
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
    'sst': {
    "name": "SST (Serverless Stack)",
    "level": 2,
    "layer": "Development Environment",
    "role": "Full-Stack Framework",
    "category": "Serverless Framework",
    "installer": {
        "type": "npm",
        "pkg": "sst"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "sst --version",
        "default_port": None
    },
    "deps": [],
    "description": "Framework for building full-stack apps on your own infrastructure (AWS, Cloudflare, etc).",
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
    'unsloth': {
    "name": "Unsloth",
    "level": 2,
    "layer": "Development Environment",
    "role": "Training",
    "category": "Model Training",
    "installer": {
        "type": "uv",
        "pkg": "unsloth"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 -c \"import unsloth; print('ok')\"",
        "default_port": None
    },
    "deps": [
        "cuda"
    ],
    "description": "2x faster LLM fine-tuning with 80% less memory.",
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
    'php': {
        "name": "PHP",
        "level": 2,
        "layer": "Development Environment",
        "role": "Language",
        "category": "Runtime",
        "installer": {
            "type": "pacman",
            "pkg": "php"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "php --version",
            "default_port": None
        },
        "deps": [],
        "description": "Server-side scripting language.",
        "license": "PHP-3.01",
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
    'ruby': {
        "name": "Ruby",
        "level": 2,
        "layer": "Development Environment",
        "role": "Language",
        "category": "Runtime",
        "installer": {
            "type": "pacman",
            "pkg": "ruby"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "ruby --version",
            "default_port": None
        },
        "deps": [],
        "description": "Dynamic programming language.",
        "license": "Ruby",
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
    'perl': {
        "name": "Perl",
        "level": 2,
        "layer": "Development Environment",
        "role": "Language",
        "category": "Runtime",
        "installer": {
            "type": "pacman",
            "pkg": "perl"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "perl -v",
            "default_port": None
        },
        "deps": [],
        "description": "High-level scripting language.",
        "license": "GPL-1.0",
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
    'julia': {
        "name": "Julia",
        "level": 2,
        "layer": "Development Environment",
        "role": "Language",
        "category": "Runtime",
        "installer": {
            "type": "pacman",
            "pkg": "julia"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "julia --version",
            "default_port": None
        },
        "deps": [],
        "description": "High-performance numerical computing language.",
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
    'nodejs': {
        "name": "Node.js",
        "level": 2,
        "layer": "Development Environment",
        "role": "Language",
        "category": "Runtime",
        "installer": {
            "type": "pacman",
            "pkg": "nodejs"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "node --version",
            "default_port": None
        },
        "deps": [],
        "description": "JavaScript runtime built on V8.",
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
    'go': {
        "name": "Go",
        "level": 2,
        "layer": "Development Environment",
        "role": "Language",
        "category": "Runtime",
        "installer": {
            "type": "pacman",
            "pkg": "go"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "go version",
            "default_port": None
        },
        "deps": [],
        "description": "Compiled systems programming language.",
        "license": "BSD-3-Clause",
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
    'rust': {
        "name": "Rust",
        "level": 2,
        "layer": "Development Environment",
        "role": "Language",
        "category": "Runtime",
        "installer": {
            "type": "pacman",
            "pkg": "rust"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "rustc --version",
            "default_port": None
        },
        "deps": [],
        "description": "Systems language focused on safety and performance.",
        "license": "MIT/Apache-2.0",
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
    'java_jdk': {
        "name": "Java JDK",
        "level": 2,
        "layer": "Development Environment",
        "role": "Language",
        "category": "Runtime",
        "installer": {
            "type": "pacman",
            "pkg": "jdk-openjdk"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "java --version",
            "default_port": None
        },
        "deps": [],
        "description": "Java development kit.",
        "license": "GPL-2.0",
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
    'zsh': {
        "name": "Zsh",
        "level": 2,
        "layer": "Development Environment",
        "role": "Shell",
        "category": "Shell",
        "installer": {
            "type": "pacman",
            "pkg": "zsh"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "zsh --version",
            "default_port": None
        },
        "deps": [],
        "description": "Extended Bourne shell with enhancements.",
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
    'mksh': {
        "name": "mksh",
        "level": 2,
        "layer": "Development Environment",
        "role": "Shell",
        "category": "Shell",
        "installer": {
            "type": "pacman",
            "pkg": "mksh"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "mksh -c 'echo ok'",
            "default_port": None
        },
        "deps": [],
        "description": "MirBSD Korn shell.",
        "license": "MirOS",
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
    'bash': {
        "name": "Bash",
        "level": 2,
        "layer": "Development Environment",
        "role": "Shell",
        "category": "Shell",
        "installer": {
            "type": "pacman",
            "pkg": "bash"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "bash --version",
            "default_port": None
        },
        "deps": [],
        "description": "GNU Bourne Again Shell.",
        "license": "GPL-3.0",
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
    'fish': {
        "name": "Fish",
        "level": 2,
        "layer": "Development Environment",
        "role": "Shell",
        "category": "Shell",
        "installer": {
            "type": "pacman",
            "pkg": "fish"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "fish --version",
            "default_port": None
        },
        "deps": [],
        "description": "User-friendly shell with auto-suggestions.",
        "license": "GPL-2.0",
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
    'fakeroot': {
        "name": "Fakeroot",
        "level": 2,
        "layer": "Development Environment",
        "role": "Build Tool",
        "category": "Build",
        "installer": {
            "type": "pacman",
            "pkg": "fakeroot"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "fakeroot --version",
            "default_port": None
        },
        "deps": [],
        "description": "Run commands pretending to have root privileges for package building.",
        "license": "GPL-3.0",
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
    'make': {
        "name": "GNU Make",
        "level": 2,
        "layer": "Development Environment",
        "role": "Build System",
        "category": "Build",
        "installer": {
            "type": "pacman",
            "pkg": "make"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "make --version",
            "default_port": None
        },
        "deps": [],
        "description": "Build automation tool.",
        "license": "GPL-3.0",
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
    'cmake': {
        "name": "CMake",
        "level": 2,
        "layer": "Development Environment",
        "role": "Build System",
        "category": "Build",
        "installer": {
            "type": "pacman",
            "pkg": "cmake"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "cmake --version",
            "default_port": None
        },
        "deps": [],
        "description": "Cross-platform build system generator.",
        "license": "BSD-3-Clause",
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
    'gcc': {
        "name": "GCC",
        "level": 2,
        "layer": "Development Environment",
        "role": "Compiler",
        "category": "Build",
        "installer": {
            "type": "pacman",
            "pkg": "gcc"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "gcc --version",
            "default_port": None
        },
        "deps": [],
        "description": "GNU Compiler Collection.",
        "license": "GPL-3.0",
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
    'bison': {
        "name": "Bison",
        "level": 2,
        "layer": "Development Environment",
        "role": "Parser Generator",
        "category": "Build",
        "installer": {
            "type": "pacman",
            "pkg": "bison"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "bison --version",
            "default_port": None
        },
        "deps": [],
        "description": "GNU parser generator.",
        "license": "GPL-3.0",
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
    'pkg_config': {
        "name": "pkg-config",
        "level": 2,
        "layer": "Development Environment",
        "role": "Build Tool",
        "category": "Build",
        "installer": {
            "type": "pacman",
            "pkg": "pkg-config"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "pkg-config --version",
            "default_port": None
        },
        "deps": [],
        "description": "Helper tool for retrieving library compile/link flags.",
        "license": "GPL-2.0",
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
    'valgrind': {
        "name": "Valgrind",
        "level": 2,
        "layer": "Development Environment",
        "role": "Profiling",
        "category": "Debugging",
        "installer": {
            "type": "pacman",
            "pkg": "valgrind"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "valgrind --version",
            "default_port": None
        },
        "deps": [],
        "description": "Instrumentation framework for debugging and profiling.",
        "license": "GPL-2.0",
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
    'gdb': {
        "name": "GDB",
        "level": 2,
        "layer": "Development Environment",
        "role": "Debugger",
        "category": "Debugging",
        "installer": {
            "type": "pacman",
            "pkg": "gdb"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "gdb --version",
            "default_port": None
        },
        "deps": [],
        "description": "GNU Debugger.",
        "license": "GPL-3.0",
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
    'strace': {
        "name": "strace",
        "level": 2,
        "layer": "Development Environment",
        "role": "Tracing",
        "category": "Debugging",
        "installer": {
            "type": "pacman",
            "pkg": "strace"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "strace -V",
            "default_port": None
        },
        "deps": [],
        "description": "System call tracer for debugging.",
        "license": "LGPL-2.1",
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
    'ltrace': {
        "name": "ltrace",
        "level": 2,
        "layer": "Development Environment",
        "role": "Tracing",
        "category": "Debugging",
        "installer": {
            "type": "pacman",
            "pkg": "ltrace"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "ltrace --version",
            "default_port": None
        },
        "deps": [],
        "description": "Library call tracer.",
        "license": "GPL-2.0",
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
    'patchelf': {
        "name": "PatchELF",
        "level": 2,
        "layer": "Development Environment",
        "role": "Binary Tool",
        "category": "Build",
        "installer": {
            "type": "pacman",
            "pkg": "patchelf"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "patchelf --version",
            "default_port": None
        },
        "deps": [],
        "description": "Tool for modifying ELF binaries.",
        "license": "GPL-3.0",
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
    'upx': {
        "name": "UPX",
        "level": 2,
        "layer": "Development Environment",
        "role": "Packer",
        "category": "Build",
        "installer": {
            "type": "pacman",
            "pkg": "upx"
        },
        "launcher": {
            "type": "desktop",
            "cmd": "upx --version",
            "default_port": None
        },
        "deps": [],
        "description": "Ultimate Packer for eXecutables.",
        "license": "GPL-2.0",
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