"""Registry entries for the Host Platform layer (L1).

Each entry follows the standard registry schema:

- ``name``: human-readable tool name
- ``level``: 11-layer taxonomy level (1-11)
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
    'tmux': {
    "name": "Tmux",
    "level": 1,
    "layer": "Host Platform",
    "role": "Multiplexer",
    "category": "Terminal",
    "installer": {
        "type": "pacman",
        "pkg": "tmux"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "tmux -V",
        "default_port": None
    },
    "deps": [],
    "description": "Terminal multiplexer for persistent sessions.",
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
    'git': {
    "name": "Git",
    "level": 1,
    "layer": "Host Platform",
    "role": "Version Control",
    "category": "VCS",
    "installer": {
        "type": "pacman",
        "pkg": "git"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "git --version",
        "default_port": None
    },
    "deps": [],
    "description": "Distributed version control system.",
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
    'podman': {
    "name": "Podman",
    "level": 1,
    "layer": "Host Platform",
    "role": "Container Runtime",
    "category": "Containers",
    "installer": {
        "type": "pacman",
        "pkg": "podman"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "podman --version",
        "default_port": None
    },
    "deps": [],
    "description": "Daemonless container engine for OCI containers.",
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
    'docker': {
    "name": "Docker",
    "level": 1,
    "layer": "Host Platform",
    "role": "Container Runtime",
    "category": "Containers",
    "installer": {
        "type": "pacman",
        "pkg": "docker"
    },
    "launcher": {
        "type": "systemd",
        "cmd": "docker",
        "default_port": None
    },
    "deps": [],
    "description": "Container platform for building and running containers.",
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
    'postgresql': {
    "name": "PostgreSQL",
    "level": 1,
    "layer": "Host Platform",
    "role": "Foundation",
    "category": "Database",
    "installer": {
        "type": "pacman",
        "pkg": "postgresql"
    },
    "launcher": {
        "type": "systemd",
        "cmd": "postgresql",
        "default_port": 5432
    },
    "deps": [],
    "description": "Relational database used by many frameworks.",
    "license": 'PostgreSQL',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'mariadb': {
    "name": "MariaDB",
    "level": 1,
    "layer": "Host Platform",
    "role": "Foundation",
    "category": "Database",
    "installer": {
        "type": "pacman",
        "pkg": "mariadb"
    },
    "launcher": {
        "type": "systemd",
        "cmd": "mariadb",
        "default_port": 3306
    },
    "deps": [],
    "description": "Open source relational database.",
    "license": 'GPL-2.0',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'redis': {
    "name": "Redis",
    "level": 1,
    "layer": "Host Platform",
    "role": "Foundation",
    "category": "Cache",
    "installer": {
        "type": "pacman",
        "pkg": "redis"
    },
    "launcher": {
        "type": "systemd",
        "cmd": "redis",
        "default_port": 6379
    },
    "deps": [],
    "description": "In-memory cache and message broker.",
    "license": 'RSALv2',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'sqlite3': {
    "name": "SQLite3",
    "level": 1,
    "layer": "Host Platform",
    "role": "Foundation",
    "category": "Database",
    "installer": {
        "type": "pacman",
        "pkg": "sqlite"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "sqlite3",
        "default_port": None
    },
    "deps": [],
    "description": "C-language library implementing a SQL database engine.",
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
    'duckdb': {
    "name": "DuckDB",
    "level": 1,
    "layer": "Host Platform",
    "role": "Foundation",
    "category": "Analytical Database",
    "installer": {
        "type": "uv",
        "pkg": "duckdb"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 -c \"import duckdb; print(duckdb.__version__)\"",
        "default_port": None
    },
    "deps": [],
    "description": "In-process analytical database with SQL support.",
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
    'lxc': {
    "name": "LXC",
    "level": 1,
    "layer": "Host Platform",
    "role": "Container Runtime",
    "category": "Containers",
    "installer": {
        "type": "pacman",
        "pkg": "lxc"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "lxc --version",
        "default_port": None
    },
    "deps": [],
    "description": "Linux container system-level virtualization.",
    "license": 'LGPL-2.1',
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
    'firecracker': {
    "name": "Firecracker",
    "level": 1,
    "layer": "Host Platform",
    "role": "MicroVM",
    "category": "Virtualization",
    "installer": {
        "type": "script",
        "cmd": "mkdir -p {tools_root}/bin {tools_root}/firecracker && FC_VER=$(curl -sIL https://github.com/firecracker-microvm/firecracker/releases/latest | grep -i '^location:' | tail -1 | sed 's|.*/tag/||' | tr -d '\r') && curl -fsSL 'https://github.com/firecracker-microvm/firecracker/releases/download/$FC_VER/firecracker-$FC_VER-x86_64.tgz' | tar xz -C {tools_root}/firecracker --strip-components=1 && ln -sf {tools_root}/firecracker/firecracker-$FC_VER-x86_64 {tools_root}/bin/firecracker && ln -sf {tools_root}/firecracker/jailer-$FC_VER-x86_64 {tools_root}/bin/jailer"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "{tools_root}/bin/firecracker --version",
        "default_port": None
    },
    "deps": [],
    "description": "Lightweight virtualization for serverless workloads.",
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
    'qemu': {
    "name": "QEMU",
    "level": 1,
    "layer": "Host Platform",
    "role": "Emulation",
    "category": "Virtualization",
    "installer": {
        "type": "pacman",
        "pkg": "qemu-base"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "qemu-system-x86_64 --version",
        "default_port": None
    },
    "deps": [],
    "description": "Full system emulation and virtualization.",
    "license": 'GPL-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'libvirt': {
    "name": "libvirt",
    "level": 1,
    "layer": "Host Platform",
    "role": "VM Management",
    "category": "Virtualization",
    "installer": {
        "type": "pacman",
        "pkg": "libvirt"
    },
    "launcher": {
        "type": "systemd",
        "cmd": "libvirtd",
        "default_port": None
    },
    "deps": [],
    "description": "Virtualization API and management daemon.",
    "license": 'LGPL-2.1',
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
    'cloudflared': {
    "name": "Cloudflared",
    "level": 1,
    "layer": "Host Platform",
    "role": "Tunnel",
    "category": "Networking",
    "installer": {
        "type": "script",
        "cmd": "mkdir -p {tools_root}/bin && curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o {tools_root}/bin/cloudflared && chmod +x {tools_root}/bin/cloudflared"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "{tools_root}/bin/cloudflared tunnel --url http://localhost:{port}",
        "default_port": 8080
    },
    "deps": [],
    "description": "Cloudflare tunnel for exposing local services.",
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
    'nginx': {
    "name": "Nginx",
    "level": 1,
    "layer": "Host Platform",
    "role": "Reverse Proxy",
    "category": "Networking",
    "installer": {
        "type": "pacman",
        "pkg": "nginx"
    },
    "launcher": {
        "type": "systemd",
        "cmd": "nginx",
        "default_port": 80
    },
    "deps": [],
    "description": "HTTP and reverse proxy server.",
    "license": 'BSD-2-Clause',
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
    'certbot': {
    "name": "Certbot",
    "level": 1,
    "layer": "Host Platform",
    "role": "TLS",
    "category": "Networking",
    "installer": {
        "type": "pacman",
        "pkg": "certbot"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "certbot --version",
        "default_port": None
    },
    "deps": [],
    "description": "Automated TLS certificate management (Let's Encrypt).",
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
}