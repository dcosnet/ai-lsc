"""
AI-LSC — LibreChat configuration generator.

Generates the ``librechat.yaml`` configuration file that wires LibreChat
to the local AI-LSC stack: Ollama inference engine, LiteLLM proxy for
multi-model routing, and the agent tool-use schemas from the agents bridge.

This makes LibreChat the turnkey agent frontend for the agentic stack
— just start it and all 210+ models plus tool-calling are available
through the web UI.

Usage
-----
    config = LibreChatConfigGenerator()
    config.set_ollama_endpoint(ollama_port=11434)
    config.set_litellm_endpoint(litellm_port=4000)
    config.set_tool_schemas(tool_schemas)
    config.save("/mnt/AI/tools/librechat/librechat.yaml")
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)


def _env_api_key(env_var: str, default: str = "") -> str:
    """Read an API key from the process environment.

    Returns *default* (empty string by default) when the variable is unset.
    Never logs the value.
    """
    return os.environ.get(env_var, default)


class LibreChatConfigGenerator:
    """Generate LibreChat configuration for AI-LSC integration.

    Parameters
    ----------
    config_dir :
        Directory where LibreChat is installed (contains docker-compose.yml
        or the yarn project root).
    """

    def __init__(self, config_dir: str | Path | None = None) -> None:
        self.config_dir = Path(config_dir) if config_dir else None
        self._endpoints: dict[str, dict[str, Any]] = {}
        self._tool_schemas: list[dict[str, Any]] = []
        self._assistants: list[dict[str, Any]] = []
        self._preset_customizations: list[dict[str, Any]] = []

    # ── Endpoint Configuration ─────────────────────────────────────────

    def set_ollama_endpoint(
        self,
        ollama_port: int = 11434,
        ollama_host: str = "127.0.0.1",
    ) -> None:
        """Configure the direct Ollama endpoint for native tool calling."""
        self._endpoints["ollama"] = {
            "type": "ollama",
            "name": "AI-LSC Ollama (Native Tool Calling)",
            "url": f"http://{ollama_host}:{ollama_port}",
            "models": {
                "default": ["qwen2.5:32b", "qwen2.5:72b"],
                "fetch": True,  # auto-discover models from /api/tags
            },
        }

    def set_litellm_endpoint(
        self,
        litellm_port: int = 4000,
        litellm_host: str = "127.0.0.1",
        api_key: str | None = None,
    ) -> None:
        """Configure the LiteLLM proxy endpoint for multi-model routing.

        ``api_key`` defaults to the ``AI_LSC_LITELLM_KEY`` environment
        variable.  If neither is set, an empty string is written and the
        caller is expected to supply the key out-of-band.
        """
        resolved_key = api_key or _env_api_key("AI_LSC_LITELLM_KEY")
        self._endpoints["litellm"] = {
            "type": "openai",
            "name": "AI-LSC LiteLLM Proxy (All Models)",
            "url": f"http://{litellm_host}:{litellm_port}/v1",
            "apiKey": resolved_key,
            "models": {
                "default": [
                    "classifier", "utility", "reasoner", "heavy",
                    "llama3-8b", "gemma2-9b", "phi4", "mistral",
                    "command-r", "coder-heavy",
                ],
                "fetch": True,
            },
        }

    def set_openwebui_endpoint(
        self,
        port: int = 8080,
        host: str = "127.0.0.1",
        api_key: str | None = None,
    ) -> None:
        """Configure OpenWebUI as an OpenAI-compatible endpoint."""
        resolved_key = api_key or _env_api_key("AI_LSC_OPENWEBUI_KEY")
        self._endpoints["openwebui"] = {
            "type": "openai",
            "name": "Open WebUI",
            "url": f"http://{host}:{port}/api",
            "apiKey": resolved_key,
            "models": {"default": ["*"], "fetch": True},
        }

    # ── Tool Schema Integration ────────────────────────────────────────

    def set_tool_schemas(
        self,
        schemas: list[dict[str, Any]],
    ) -> None:
        """Set the AI-LSC tool schemas for LibreChat's tool-use system.

        These are registered as server-side tools that any assistant
        can invoke through the OpenAI function-calling protocol.
        """
        self._tool_schemas = schemas

    # ── Assistant Presets ───────────────────────────────────────────────

    def add_assistant_preset(
        self,
        name: str,
        model: str = "reasoner",
        system_prompt: str = "",
        tools_enabled: bool = True,
    ) -> None:
        """Add a pre-configured assistant definition.

        Parameters
        ----------
        name :
            Assistant display name.
        model :
            Default model identifier (matches LiteLLM alias or Ollama model).
        system_prompt :
            Initial system prompt.
        tools_enabled :
            Whether to enable AI-LSC tool calling.
        """
        assistant: dict[str, Any] = {
            "name": name,
            "model": model,
            "system_prompt": system_prompt,
        }
        if tools_enabled and self._tool_schemas:
            assistant["tools"] = self._tool_schemas
        self._assistants.append(assistant)

    def add_default_assistants(self) -> None:
        """Add the standard AI-LSC assistant presets."""
        self.add_assistant_preset(
            name="Stack Operator",
            model="reasoner",
            system_prompt=(
                "You are the AI-LSC Stack Operator. You can start, stop, "
                "and manage the entire AI tool stack. Use tools to control "
                "services, pull models, and configure the pipeline. "
                "Always check service status before starting or stopping."
            ),
        )
        self.add_assistant_preset(
            name="RAG Analyst",
            model="reasoner",
            system_prompt=(
                "You are the AI-LSC RAG Analyst. You search knowledge "
                "bases, analyze documents using vector similarity, and "
                "synthesize information from multiple sources. Use the "
                "inject_skill tool to load the rag-analyst skill."
            ),
        )
        self.add_assistant_preset(
            name="Code Reviewer",
            model="heavy",
            system_prompt=(
                "You are the AI-LSC Code Reviewer. You review code for "
                "bugs, style issues, security vulnerabilities, and "
                "architectural problems. Use the inject_skill tool to "
                "load the code-reviewer skill for deep analysis."
            ),
        )

    # ── YAML Generation ─────────────────────────────────────────────────

    def generate_yaml(self) -> str:
        """Generate the librechat.yaml configuration content."""
        lines = [
            "# AI-LSC — LibreChat Configuration",
            "# Auto-generated by agents/librechat_config.py",
            "# Connects LibreChat to the local AI-LSC tool stack",
            "",
        ]

        # Endpoints
        if self._endpoints:
            lines.append("endpoints:")
            for name, config in self._endpoints.items():
                lines.append(f'  - name: "{config.get("name", name)}"')
                lines.append(f'    type: "{config.get("type", "openai")}"')
                lines.append(f'    url: "{config.get("url", "")}"')
                if "apiKey" in config:
                    lines.append(f'    apiKey: "{config["apiKey"]}"')
                lines.append("")

        # Tool schemas (written as JSON in a comment block for copy-paste)
        if self._tool_schemas:
            lines.append("# AI-LSC Tool Schemas (register via LibreChat admin UI):")
            lines.append("# tools:")
            lines.append(f"#   schemas: {json.dumps(self._tool_schemas, indent=4)}")
            lines.append("")

        # Assistant presets
        if self._assistants:
            lines.append("# AI-LSC Assistant Presets:")
            for assistant in self._assistants:
                lines.append(f"# - name: \"{assistant['name']}\"")
                lines.append(f"#   model: \"{assistant['model']}\"")
                lines.append(f"#   system_prompt: \"{assistant.get('system_prompt', '')}\"")
                lines.append("")

        return "\n".join(lines)

    def generate_env_file(self) -> str:
        """Generate the .env file for LibreChat configuration."""
        env_lines = [
            "# AI-LSC — LibreChat Environment",
            "# Auto-generated by agents/librechat_config.py",
            "",
            "# Database (use MariaDB from AI-LSC stack)",
            "DB_HOST=127.0.0.1",
            "DB_PORT=3306",
            "DB_NAME=librechat",
            "DB_USER=librechat",
            "DB_PASS=librechat",
            "",
            "# Redis (use Redis from AI-LSC stack)",
            "REDIS_HOST=127.0.0.1",
            "REDIS_PORT=6379",
            "",
            # Application settings
            "PORT=3080",
            "HOST=127.0.0.1",
            "NODE_ENV=production",
            "API_PLUGINS=false",
            "",
            # AI-LSC integration
            "ALLOWED_ENDPOINTS=ollama,openai,custom",
            "",
        ]

        # Add endpoint-specific env vars
        if "ollama" in self._endpoints:
            ollama_ep = self._endpoints["ollama"]
            env_lines.append(f"# Ollama endpoint")
            env_lines.append(f"OLLAMA_BASE_URL={ollama_ep.get('url', 'http://127.0.0.1:11434')}")
            env_lines.append("")

        if "litellm" in self._endpoints:
            litellm = self._endpoints["litellm"]
            env_lines.append(f"# LiteLLM proxy endpoint")
            env_lines.append(f"OPENAI_REVERSE_PROXY={litellm.get('url', 'http://127.0.0.1:4000/v1')}")
            env_lines.append(f"OPENAI_API_KEY={litellm.get('apiKey', _env_api_key('AI_LSC_LITELLM_KEY'))}")
            env_lines.append("")

        return "\n".join(env_lines)

    # ── Persistence ──────────────────────────────────────────────────

    def save(
        self,
        config_dir: str | Path | None = None,
    ) -> dict[str, str]:
        """Write configuration files to disk.

        Returns a dict mapping filename → absolute path.
        """
        out_dir = Path(config_dir) if config_dir else self.config_dir
        if not out_dir:
            return {}

        out_dir.mkdir(parents=True, exist_ok=True)
        written: dict[str, str] = {}

        # librechat.yaml
        yaml_path = out_dir / "librechat.yaml"
        yaml_path.write_text(self.generate_yaml(), encoding="utf-8")
        written["librechat.yaml"] = str(yaml_path)

        # .env
        env_path = out_dir / ".env"
        env_path.write_text(self.generate_env_file(), encoding="utf-8")
        written[".env"] = str(env_path)

        # tool_schemas.json (for import via admin UI)
        if self._tool_schemas:
            schemas_path = out_dir / "ai_lsc_tool_schemas.json"
            schemas_path.write_text(
                json.dumps(self._tool_schemas, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            written["ai_lsc_tool_schemas.json"] = str(schemas_path)

        logger.info("Saved LibreChat config files to %s", out_dir)
        return written
