"""Registry entries for the Observability layer (L7).

Contains metrics, dashboards, tracing, AI monitoring, and LLM evaluation tools.

This module is consumed by
:mod:`ai_lsc.registry.loader`.
"""

TOOLS: dict[str, dict] = {
    'btop': {
    "name": "Btop",
    "level": 7,
    "layer": "Observability",
    "role": "Dashboard",
    "category": "Metrics",
    "installer": {
        "type": "pacman",
        "pkg": "btop"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "x-terminal-emulator -e btop",
        "default_port": None
    },
    "deps": [],
    "description": "Resource monitor that shows usage and stats.",
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
    'glances': {
    "name": "Glances",
    "level": 7,
    "layer": "Observability",
    "role": "Dashboard",
    "category": "Metrics",
    "installer": {
        "type": "pacman",
        "pkg": "glances"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "glances -w --port {port}",
        "default_port": 61208
    },
    "deps": [],
    "description": "Cross-platform system monitoring tool.",
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
    'prometheus': {
    "name": "Prometheus",
    "level": 7,
    "layer": "Observability",
    "role": "Metrics Collector",
    "category": "Metrics",
    "installer": {
        "type": "pacman",
        "pkg": "prometheus"
    },
    "launcher": {
        "type": "systemd",
        "cmd": "prometheus",
        "default_port": 9090
    },
    "deps": [],
    "description": "Open-source monitoring and alerting toolkit.",
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
    'grafana': {
    "name": "Grafana",
    "level": 7,
    "layer": "Observability",
    "role": "Dashboard",
    "category": "Visualization",
    "installer": {
        "type": "pacman",
        "pkg": "grafana"
    },
    "launcher": {
        "type": "systemd",
        "cmd": "grafana-server",
        "default_port": 3000
    },
    "deps": [],
    "description": "Multi-source observability dashboards and visualization.",
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
    "name": "Grafana Alloy",
    "level": 7,
    "layer": "Observability",
    "role": "Collector",
    "category": "Telemetry",
    "installer": {
        "type": "script",
        "cmd": "curl -fsSL https://raw.githubusercontent.com/grafana/alloy/main/install.sh | sh"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "alloy run --server.http.listen-port={port}",
        "default_port": 12345
    },
    "deps": [
        "prometheus"
    ],
    "description": "OpenTelemetry collector with Prometheus integration.",
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
    'opik': {
    "name": "Opik",
    "level": 7,
    "layer": "Observability",
    "role": "LLM Tracing",
    "category": "AI Observability",
    "installer": {
        "type": "uv",
        "pkg": "opik"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "opik serve --port {port}",
        "default_port": 3000
    },
    "deps": [],
    "description": "Open-source LLM observability and tracing platform.",
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
    'pulse_ai': {
    "name": "Pulse AI",
    "level": 7,
    "layer": "Observability",
    "role": "Health Monitor",
    "category": "AI Monitoring",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/pulse-ai"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/pulse_ai && python3 -m pulse serve --port {port}",
        "default_port": 8900
    },
    "deps": [],
    "description": "AI service health monitoring and auto-recovery.",
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
    'latitude': {
    "name": "Latitude",
    "level": 7,
    "layer": "Observability",
    "role": "Evaluation",
    "category": "LLM Evaluation",
    "installer": {
        "type": "git",
        "pkg": "https://github.com/nicely-done/latitude"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/latitude && python3 -m latitude serve --port {port}",
        "default_port": 9300
    },
    "deps": [
        "ollama"
    ],
    "description": "LLM output evaluation and benchmarking platform.",
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
}