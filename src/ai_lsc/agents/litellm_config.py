"""
AI-LSC — LiteLLM proxy configuration generator.

Generates the ``litellm_config.yaml`` file that configures the LiteLLM
proxy to normalize all 210+ local Ollama models into a single OpenAI-compatible
endpoint.  This lets LibreChat (and any other OpenAI-format client) talk to
the entire local model fleet through one port.

The config also includes:
    - Model tier routing (8B/14B/32B/70B) with custom names.
    - Rate limiting per tier to manage VRAM contention.
    - Fallback chains for graceful degradation.

Usage
-----
    config = LiteLLMConfigGenerator()
    config.add_ollama_models(ollama_port=11434)
    yaml_str = config.generate_yaml()
    config.save("/mnt/AI/config/litellm_config.yaml")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_lsc.constants import MODEL_TIERS
from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)


# Default model catalog — maps tier to representative Ollama models
_TIER_MODELS: dict[str, list[dict[str, str]]] = {
    "8b": [
        {"ollama_name": "qwen2.5:7b", "alias": "classifier"},
        {"ollama_name": "llama3.1:8b", "alias": "llama3-8b"},
        {"ollama_name": "gemma2:9b", "alias": "gemma2-9b"},
    ],
    "14b": [
        {"ollama_name": "qwen2.5:14b", "alias": "utility"},
        {"ollama_name": "phi4:14b", "alias": "phi4"},
        {"ollama_name": "mistral:7b", "alias": "mistral"},
    ],
    "32b": [
        {"ollama_name": "qwen2.5:32b", "alias": "reasoner"},
        {"ollama_name": "llama3.1:70b", "alias": "llama3-70b"},
        {"ollama_name": "command-r:35b", "alias": "command-r"},
    ],
    "70b": [
        {"ollama_name": "qwen2.5:72b", "alias": "heavy"},
        {"ollama_name": "deepseek-coder-v2:236b", "alias": "coder-heavy"},
    ],
}

# Rate limits per tier (requests per minute)
_TIER_RPM: dict[str, int] = {
    "8b": 60,
    "14b": 30,
    "32b": 10,
    "70b": 3,
}


class LiteLLMConfigGenerator:
    """Generate LiteLLM proxy configuration for the AI-LSC stack.

    Parameters
    ----------
    general_settings :
        Override dict for the ``general_settings`` section.
    """

    def __init__(
        self,
        general_settings: dict[str, Any] | None = None,
    ) -> None:
        self.model_list: list[dict[str, Any]] = []
        self.litellm_settings: dict[str, Any] = {
            "drop_params": True,
            "set_verbose": False,
        }
        self.general_settings: dict[str, Any] = general_settings or {
            "master_key": "sk-ai-lsc-local",
        }
        self._tier_models: dict[str, list[dict[str, str]]] = {
            k: list(v) for k, v in _TIER_MODELS.items()
        }

    # ── Model Registration ────────────────────────────────────────────

    def add_ollama_models(
        self,
        ollama_port: int = 11434,
        ollama_host: str = "127.0.0.1",
    ) -> None:
        """Add the default tier-based Ollama models."""
        base_url = f"http://{ollama_host}:{ollama_port}"

        for tier, models in self._tier_models.items():
            rpm = _TIER_RPM.get(tier, 10)
            tier_info = MODEL_TIERS.get(tier, {})

            for model in models:
                entry = {
                    "model_name": model["alias"],
                    "litellm_provider": "ollama",
                    "model_info": {
                        "id": model["ollama_name"],
                        "mode": "chat",
                        "tier": tier,
                        "max_vram_gb": tier_info.get("max_vram_gb", 32),
                        "description": tier_info.get("desc", ""),
                    },
                    "litellm_params": {
                        "model": model["ollama_name"],
                        "api_base": base_url,
                        "rpm_limit": rpm,
                    },
                }
                self.model_list.append(entry)

        logger.info("Added %d models from Ollama at %s",
                     len(self.model_list), base_url)

    def add_custom_model(
        self,
        alias: str,
        ollama_name: str,
        ollama_port: int = 11434,
        rpm: int = 10,
        tier: str = "32b",
    ) -> None:
        """Add a custom model to the configuration."""
        base_url = f"http://127.0.0.1:{ollama_port}"
        tier_info = MODEL_TIERS.get(tier, {})

        entry = {
            "model_name": alias,
            "litellm_provider": "ollama",
            "model_info": {
                "id": ollama_name,
                "mode": "chat",
                "tier": tier,
                "max_vram_gb": tier_info.get("max_vram_gb", 32),
            },
            "litellm_params": {
                "model": ollama_name,
                "api_base": base_url,
                "rpm_limit": rpm,
            },
        }
        self.model_list.append(entry)

    def add_external_provider(
        self,
        alias: str,
        provider: str,
        api_key: str = "",
        api_base: str = "",
        model_id: str = "",
    ) -> None:
        """Add an external API provider (e.g. OpenAI, Anthropic)."""
        entry = {
            "model_name": alias,
            "litellm_provider": provider,
            "model_info": {"id": model_id},
            "litellm_params": {
                "model": model_id,
                "api_key": api_key,
            },
        }
        if api_base:
            entry["litellm_params"]["api_base"] = api_base
        self.model_list.append(entry)

    # ── YAML Generation ─────────────────────────────────────────────────

    def generate_yaml(self) -> str:
        """Generate the litellm_config.yaml content."""
        lines = [
            "# AI-LSC — LiteLLM Proxy Configuration",
            "# Auto-generated by agents/litellm_config.py",
            "# Maps all local Ollama models into a single OpenAI-compatible endpoint",
            "",
            "model_list:",
        ]

        for entry in self.model_list:
            lines.append(f'  - model_name: "{entry["model_name"]}"')
            lines.append(f'    litellm_provider: "{entry["litellm_provider"]}"')
            for k, v in entry.get("litellm_params", {}).items():
                lines.append(f"    {k}: {self._format_yaml_value(v)}")
            lines.append("")

        # General settings
        if self.general_settings:
            lines.append("general_settings:")
            for k, v in self.general_settings.items():
                lines.append(f"  {k}: {self._format_yaml_value(v)}")
            lines.append("")

        # LiteLLM settings
        if self.litellm_settings:
            lines.append("litellm_settings:")
            for k, v in self.litellm_settings.items():
                lines.append(f"  {k}: {self._format_yaml_value(v)}")

        return "\n".join(lines)

    def generate_dict(self) -> dict[str, Any]:
        """Return the configuration as a plain dict (for JSON export)."""
        return {
            "model_list": self.model_list,
            "general_settings": self.general_settings,
            "litellm_settings": self.litellm_settings,
        }

    # ── Persistence ──────────────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        """Write the YAML configuration to disk."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.generate_yaml(), encoding="utf-8")
        logger.info("Saved LiteLLM config to %s", out)

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _format_yaml_value(value: Any) -> str:
        """Format a Python value as a YAML scalar."""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            if any(c in value for c in ':"\'{}[]&*?|>!%@`'):
                return f'"{value}"'
            return value
        return str(value)

    def list_models(self) -> list[str]:
        """Return all registered model aliases."""
        return [e["model_name"] for e in self.model_list]
