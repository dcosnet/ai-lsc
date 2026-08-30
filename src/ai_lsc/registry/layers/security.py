"""Registry entries for the Security layer (L7).

Contains identity management, secrets management, container scanning,
intrusion prevention, antivirus, and policy enforcement tools for
the local AI infrastructure.

This module is consumed by
:mod:`ai_lsc.registry.loader`.

Structural fields (layer, level) follow the 10-Layer Systems
Architecture Taxonomy; tools may be regrouped across files in a
future pass — the loader merges by tool, not by filename.
"""

TOOLS: dict[str, dict] = {
    'keycloak': {
    "name": "Keycloak",
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Identity',
    "category": 'Auth',
    "installer": {
        "type": "custom",
        "pkg": "https://github.com/keycloak/keycloak"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "kc start-dev --http-port={port}",
        "default_port": 8081
    },
    "deps": ["java"],
    "description": "Open-source identity and access management for modern applications.",
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
    'vault': {
    "name": "HashiCorp Vault",
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Secrets',
    "category": 'Secrets Management',
    "installer": {
        "type": "pacman",
        "pkg": "vault"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "vault server -dev -dev-listen-address=127.0.0.1:{port}",
        "default_port": 8200
    },
    "deps": [],
    "description": "Secrets management and data protection for AI API keys and credentials.",
    "license": 'BSL-1.1',
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
    'trivy': {
    "name": "Trivy",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Scanner',
    "category": 'Container Security',
    "installer": {
        "type": "pacman",
        "pkg": "trivy"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "trivy --version",
        "default_port": None
    },
    "deps": [],
    "description": "Scanner for vulnerabilities in container images, filesystems, and git repositories.",
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
    'fail2ban': {
    "name": "Fail2Ban",
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'IDS',
    "category": 'Intrusion Prevention',
    "installer": {
        "type": "pacman",
        "pkg": "fail2ban"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "fail2ban-client status",
        "default_port": None
    },
    "deps": [],
    "description": "Intrusion prevention framework that protects AI service endpoints from brute-force attacks.",
    "license": 'GPL-2.0',
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
    'clamav': {
    "name": "ClamAV",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Scanner',
    "category": 'Antivirus',
    "installer": {
        "type": "pacman",
        "pkg": "clamav"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "freshclam && clamscan --version",
        "default_port": None
    },
    "deps": [],
    "description": "Open-source antivirus engine for scanning uploaded documents and datasets.",
    "license": 'GPL-2.0',
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
    'opa': {
    "name": "Open Policy Agent",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Policy',
    "category": 'Policy Engine',
    "installer": {
        "type": "pacman",
        "pkg": "opa"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "opa run --server --addr=0.0.0.0:{port}",
        "default_port": 8181
    },
    "deps": [],
    "description": "General-purpose policy engine for unified authorization and access control across AI services.",
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
}