"""Registry entries for the DevOps layer (L10).

Contains Infrastructure as Code tools, configuration management, OCI
runtime packaging, provisioning tools, and AI coding agents
(aider, claude_code, codex, openhands, opencode, gemini_cli,
qwen_code, goose, zcoder).

This module is consumed by
:mod:`ai_lsc.registry.loader`.

Structural fields (layer, level) follow the 10-Layer Systems
Architecture Taxonomy; tools may be regrouped across files in a
future pass — the loader merges by tool, not by filename.
"""

TOOLS: dict[str, dict] = {
    'terraform': {
    "name": "Terraform",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Infrastructure Provision',
    "category": 'Infrastructure Provision',
    "installer": {
        "type": "pacman",
        "pkg": "terraform"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "terraform version",
        "default_port": None
    },
    "deps": [],
    "description": "Infrastructure as Code provisioning tool.",
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
    'ansible': {
    "name": "Ansible",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Agentless Deployment',
    "category": 'Agentless Deployment',
    "installer": {
        "type": "pacman",
        "pkg": "ansible"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "ansible --version",
        "default_port": None
    },
    "deps": [],
    "description": "Agentless IT automation and configuration management.",
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
    'puppet': {
    "name": "Puppet",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'System Auditor',
    "category": 'System Auditor',
    "installer": {
        "type": "pacman",
        "pkg": "puppet"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "puppet --version",
        "default_port": None
    },
    "deps": [],
    "description": "Declarative configuration management tool.",
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
    'pulumi': {
    "name": "Pulumi",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Programmable IaC',
    "category": 'Programmable IaC',
    "installer": {
        "type": "npm",
        "pkg": "@pulumi/pulumi"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "pulumi version",
        "default_port": None
    },
    "deps": [],
    "description": "IaC platform using real programming languages (Python, TypeScript, Go).",
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
    'bicep': {
    "name": "Bicep",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Local Declarative DSL',
    "category": 'Local Declarative DSL',
    "installer": {
        "type": "npm",
        "pkg": "@azure/bicep"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "bicep --version",
        "default_port": None
    },
    "deps": [],
    "description": "Azure domain-specific language for declarative infrastructure.",
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
    'opentofu': {
    "name": "OpenTofu",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Open-Source IaC',
    "category": 'Open-Source IaC',
    "installer": {
        "type": "custom",
        "pkg": "https://github.com/opentofu/opentofu"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "tofu version",
        "default_port": None
    },
    "deps": [],
    "description": "Open-source Terraform fork maintained by the Linux Foundation.",
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
    'aws_cdk': {
    "name": "AWS CDK",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Cloud Dev Kit',
    "category": 'Cloud Dev Kit',
    "installer": {
        "type": "npm",
        "pkg": "aws-cdk"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "cdk --version",
        "default_port": None
    },
    "deps": [],
    "description": "Cloud Development Kit — define AWS CloudFormation in code.",
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
    'crossplane': {
    "name": "Crossplane",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Infrastructure as Code',
    "category": 'IaC Control Plane',
    "installer": {
        "type": "custom",
        "pkg": "https://github.com/crossplane/crossplane"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "crossplane --help",
        "default_port": None
    },
    "deps": [
        "kubectl"
    ],
    "description": "Kubernetes-native cloud infrastructure control plane.",
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
    'terragrunt': {
    "name": "Terragrunt",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'IaC DRY Wrapper',
    "category": 'IaC DRY Wrapper',
    "installer": {
        "type": "custom",
        "pkg": "https://github.com/gruntwork-io/terragrunt"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "terragrunt --version",
        "default_port": None
    },
    "deps": [
        "terraform"
    ],
    "description": "Thin wrapper for Terraform providing DRY config and remote state.",
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
    "name": "Stack Container Packager",
    "level": 1,
    "layer": 'Host Platform & Infrastructure',
    "role": 'Runtime Packaging',
    "category": 'Runtime Packaging',
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
    "description": "Compiles validated pipeline matrices into Podman/Docker specs.",
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
    'homelab': {
    "name": "Homelab",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Metal Provisioner',
    "category": 'Metal Provisioner',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/khuedoan/homelab",
        "cmd": ""
    },
    "launcher": {
        "type": "desktop",
        "cmd": "homelab",
        "default_port": None
    },
    "deps": [],
    "description": "Fully automated homelab provisioning from empty disk to running services in one command. IaC/GitOps: Packer + Terraform + Ansible + k3s + ArgoCD.",
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
    'aider': {
    "name": "Aider",
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'CLI Pair Programmer',
    "category": 'CLI Pair Programmer',
    "installer": {
        "type": "uv",
        "pkg": "aider-chat"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "aider --version",
        "default_port": None
    },
    "deps": [],
    "description": "AI pair programming assistant that works in your terminal.",
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

    'claude_code': {
    "name": "Claude Code",
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Terminal Coding Agent',
    "category": 'Terminal Coding Agent',
    "installer": {
        "type": "npm",
        "pkg": "@anthropic-ai/claude-code"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "claude --version",
        "default_port": None
    },
    "deps": [],
    "description": "Anthropic's CLI-based AI coding agent powered by Claude.",
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

    'codex': {
    "name": "Codex",
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Codex Developer',
    "category": 'Codex Developer',
    "installer": {
        "type": "npm",
        "pkg": "@openai/codex"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "codex --version",
        "default_port": None
    },
    "deps": [],
    "description": "OpenAI's CLI-based AI coding agent powered by GPT.",
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

    'openhands': {
    "name": "OpenHands",
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Sovereign Software Agent',
    "category": 'Sovereign Software Agent',
    "installer": {
        "type": "git_node",
        "pkg": "https://github.com/All-Hands-AI/OpenHands.git"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "openhands serve --port {port}",
        "default_port": 3000
    },
    "deps": [],
    "description": "Open-source AI coding agent platform with web UI for autonomous software engineering.",
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

    'opencode': {
    "name": "OpenCode",
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Coding Agent',
    "category": 'AI Coding Agent',
    "installer": {
        "type": "npm",
        "pkg": "opencode-ai"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "opencode --version",
        "default_port": None
    },
    "deps": [],
    "description": "Open-source terminal AI coding agent from the SST team. "
                  "Native TUI, LSP integration, shareable sessions, and "
                  "75+ model providers including local Ollama.",
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

    'gemini_cli': {
    "name": "Gemini CLI",
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Coding Agent',
    "category": 'AI Coding Agent',
    "installer": {
        "type": "npm",
        "pkg": "@google/gemini-cli"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "gemini --version",
        "default_port": None
    },
    "deps": [],
    "description": "Google's open-source terminal AI agent. Supports "
                  "OpenAI-compatible local endpoints via OPENAI_BASE_URL, "
                  "MCP servers, and multi-turn agentic workflows.",
    "license": "Apache-2.0",
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

    'qwen_code': {
    "name": "Qwen Code",
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Coding Agent',
    "category": 'AI Coding Agent',
    "installer": {
        "type": "npm",
        "pkg": "@qwen-code/qwen-code"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "qwen --version",
        "default_port": None
    },
    "deps": [],
    "description": "Qwen's terminal-based agentic coding tool (Gemini CLI "
                  "fork) optimized for Qwen models, with subagents, MCP "
                  "support, and OpenAI-compatible local endpoints.",
    "license": "Apache-2.0",
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

    'goose': {
    "name": "codename goose",
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Coding Agent',
    "category": 'AI Coding Agent',
    "installer": {
        "type": "custom",
        "pkg": "https://github.com/block/goose"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "goose --version",
        "default_port": None
    },
    "deps": [],
    "description": "Block's open-source extensible AI agent. Runs MCP "
                  "extensions for coding, research, and automation; supports "
                  "local LLM backends including Ollama.",
    "license": "Apache-2.0",
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

# ---- zcoder -----------------------------------------------------------------
    'zcoder': {
    "name": "ZCoder",
    "level": 7,
    "layer": 'Agentic Software Engineering & Sandboxes',
    "role": 'Coding Agent',
    "category": 'AI Coding Agent',
    "installer": {
        "type": "npm",
        "pkg": "zcoder-cli"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "zcoder --version",
        "default_port": None
    },
    "deps": [
        "ollama"
    ],
    "description": "Zhipu AI Z-Coder CLI coding agent. Speaks OpenAI-compat "
                  "— point OPENAI_API_BASE at MeshLLM (localhost:9337/v1), "
                  "LiteLLM (localhost:4000/v1), or Ollama direct "
                  "(localhost:11434/v1). If the upstream package name "
                  "differs in your region, override installer.pkg in "
                  "your local registry.",
    "license": "Apache-2.0",
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