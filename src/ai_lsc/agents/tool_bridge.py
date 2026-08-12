"""
AI-LSC — Registry-to-function-calling schema translator.

``ToolBridge`` reads the 115-tool registry and generates OpenAI-compatible
tool schemas that describe which actions an LLM can take.  It also enriches
schemas with context from the registry (descriptions, layers, ports).

Usage
-----
    bridge = ToolBridge(registry_mgr)
    schemas = bridge.generate_all_schemas()
    # Pass schemas to Ollama, LibreChat, or OpenWebUI
"""

from __future__ import annotations

from typing import Any

from ai_lsc.agents.schema import (
    CORE_SCHEMAS,
    SCHEMA_BY_NAME,
    _make_schema,
)
from ai_lsc.constants import DEFAULT_PORTS


class ToolBridge:
    """Translates the AI-LSC registry into function-calling tool schemas.

    Parameters
    ----------
    registry_data :
        The full registry dict from ``RegistryManager.get_all_tools()``.
    active_tools :
        Set of tool IDs currently active in the pipeline (from
        ``PipelineState.active_tools``).  Used to annotate which
        tools are available vs. just registered.
    """

    def __init__(
        self,
        registry_data: dict[str, dict[str, Any]],
        active_tools: set[str] | None = None,
    ) -> None:
        self.registry = registry_data
        self.active_tools = active_tools or set()

    # ── Schema generation ────────────────────────────────────────────

    def generate_all_schemas(self) -> list[dict[str, Any]]:
        """Return the complete list of tool schemas for function calling.

        This merges the 9 core action schemas with per-tool annotations
        for tools that have web interfaces or are Ollama models.
        """
        # H-08: drop the static list_available_tools schema before we
        # append the annotated version, otherwise the LLM receives two
        # definitions for the same tool name.
        schemas = [
            s for s in CORE_SCHEMAS
            if s.get("function", {}).get("name") != "list_available_tools"
        ]

        # Annotate list_tools with available tool IDs
        list_schema = SCHEMA_BY_NAME["list_available_tools"]
        tool_names = sorted(self.registry.keys())
        list_desc = (
            f"{list_schema['function']['description']} "
            f"Known tools: {', '.join(tool_names[:20])}"
            f"{'...' if len(tool_names) > 20 else ''}. "
            f"Active: {', '.join(sorted(self.active_tools)) or 'none'}."
        )
        schemas.append(_make_schema(
            name="list_available_tools",
            description=list_desc,
            properties=list_schema["function"]["parameters"]["properties"],
            required=list_schema["function"]["parameters"]["required"],
        ))

        return schemas

    def generate_tool_summary(self) -> str:
        """Return a human-readable summary of all registered tools.

        Designed to be injected as context into the LLM's system prompt
        so it knows what tools are available without needing a tool call.
        """
        lines = ["AI-LSC Managed Tools:", "=" * 40]
        for tool_id, meta in sorted(self.registry.items()):
            status = "ACTIVE" if tool_id in self.active_tools else "available"
            port = meta.get("launcher", {}).get("default_port")
            port_str = f" :{port}" if port else ""
            desc = meta.get("description", "No description")
            flags = meta.get("flags", {})
            flags_str = []
            if flags.get("has_web"):
                flags_str.append("web")
            if flags.get("is_ollama"):
                flags_str.append("ollama")
            if flags.get("has_cli"):
                flags_str.append("cli")
            flag_str = f" [{','.join(flags_str)}]" if flags_str else ""
            lines.append(
                f"  {tool_id}{port_str} — {desc} ({status}){flag_str}"
            )
        return "\n".join(lines)

    # ── Tool lookup helpers ───────────────────────────────────────────

    def get_tool_info(self, tool_id: str) -> dict[str, Any]:
        """Return registry metadata for a single tool, or empty dict."""
        return self.registry.get(tool_id, {})

    def get_tools_by_layer(self, layer: str) -> list[tuple[str, dict]]:
        """Return all tools in a given layer."""
        return [
            (tid, meta) for tid, meta in self.registry.items()
            if meta.get("layer") == layer
        ]

    def get_tools_by_flag(
        self, flag: str, value: bool = True
    ) -> list[tuple[str, dict]]:
        """Return tools matching a specific flag (e.g. 'has_web')."""
        return [
            (tid, meta) for tid, meta in self.registry.items()
            if meta.get("flags", {}).get(flag) == value
        ]

    def get_web_tools(self) -> list[tuple[str, dict]]:
        """Return all tools with web interfaces."""
        return self.get_tools_by_flag("has_web")

    def get_ollama_tools(self) -> list[tuple[str, dict]]:
        """Return all Ollama-related tools."""
        return self.get_tools_by_flag("is_ollama")

    def suggest_model_for_task(self, task_type: str) -> str:
        """Suggest an appropriate Ollama model tier for a task type.

        This mirrors the Layer 1 routing logic from the agentic
        architecture template.
        """
        routing: dict[str, str] = {
            "document": "70b",
            "chart": "70b",
            "web": "70b",
            "script": "32b",
            "analysis": "70b",
            "classification": "8b",
            "clarification": "14b",
        }
        return routing.get(task_type, "32b")
