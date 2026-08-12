"""Registry entries for the DevOps layer (L9).

Contains Infrastructure as Code tools, configuration management, OCI
runtime packaging, and provisioning tools.

This module is consumed by
:mod:`ai_lsc.registry.loader`.
"""

TOOLS: dict[str, dict] = {
    'terraform': {
    "name": "Terraform",
    "level": 9,
    "layer": "DevOps",
    "role": "Infrastructure as Code",
    "category": "IaC",
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
    "level": 9,
    "layer": "DevOps",
    "role": "Configuration Management",
    "category": "Config Management",
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
    "level": 9,
    "layer": "DevOps",
    "role": "Configuration Management",
    "category": "Config Management",
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
    "level": 9,
    "layer": "DevOps",
    "role": "Infrastructure as Code",
    "category": "IaC",
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
    "level": 9,
    "layer": "DevOps",
    "role": "Infrastructure as Code",
    "category": "IaC",
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
    "level": 9,
    "layer": "DevOps",
    "role": "Infrastructure as Code",
    "category": "IaC",
    "installer": {
        "type": "custom",
        "pkg": "https://opentofu.org/docs/intro/install/"
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
    "level": 9,
    "layer": "DevOps",
    "role": "Infrastructure as Code",
    "category": "IaC",
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
    "level": 9,
    "layer": "DevOps",
    "role": "Infrastructure as Code",
    "category": "IaC Control Plane",
    "installer": {
        "type": "custom",
        "pkg": "https://docs.crossplane.io/v2/getting-started/install/"
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
    "level": 9,
    "layer": "DevOps",
    "role": "Infrastructure as Code",
    "category": "IaC Wrapper",
    "installer": {
        "type": "custom",
        "pkg": "https://terragrunt.gruntwork.io/docs/getting-started/install/"
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
    "level": 9,
    "layer": "DevOps",
    "role": "Runtime Packaging",
    "category": "OCI Export",
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
    "level": 9,
    "layer": "DevOps",
    "role": "Provisioning",
    "category": "Provisioning",
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
}