"""
AI-LSC — Tool schema definitions for OpenAI-compatible function calling.

Defines the JSON schema fragments that describe each tool action the LLM
can invoke.  These schemas are consumed by:
    - ``ToolBridge.generate_schemas()``  → full schema list
    - ``ollama_tools.register_with_ollama()``  → POST /api/tools
    - LibreChat / OpenWebUI tool-definition imports

Every schema follows the OpenAI function-calling format::

    {
        "type": "function",
        "function": {
            "name": "<action_name>",
            "description": "<human-readable description>",
            "parameters": {
                "type": "object",
                "properties": { ... },
                "required": [ ... ]
            }
        }
    }
"""

from __future__ import annotations

from typing import Any


# ── Common parameter fragments ─────────────────────────────────────────

_TOOL_ID_PARAM: dict[str, Any] = {
    "type": "string",
    "description": "Tool identifier from the AI-LSC registry "
                  "(e.g. 'ollama', 'qdrant', 'redis').",
}

_PORT_PARAM: dict[str, Any] = {
    "type": "integer",
    "description": "Override the default port (optional).",
}

_MODEL_NAME_PARAM: dict[str, Any] = {
    "type": "string",
    "description": "Model name for Ollama pull "
                  "(e.g. 'qwen2.5:72b', 'llama3:8b').",
}

_SKILL_NAME_PARAM: dict[str, Any] = {
    "type": "string",
    "description": "Skill identifier to inject into the conversation "
                  "(e.g. 'rag-analyst', 'code-reviewer').",
}

_QUERY_PARAM: dict[str, Any] = {
    "type": "string",
    "description": "Search query or description of what to find.",
}

_TARGET_URL_PARAM: dict[str, Any] = {
    "type": "string",
    "description": "URL to open in the browser.",
}


# ── Schema factory ─────────────────────────────────────────────────────

def _make_schema(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str] | None = None,
) -> dict[str, Any]:
    """Build an OpenAI function-calling tool schema."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }


# ── Pre-built schemas for core actions ─────────────────────────────────

SCHEMA_START_SERVICE = _make_schema(
    name="start_service",
    description="Start an AI-LSC managed service by its tool ID. "
                "The service must be installed first.",
    properties={
        "tool_id": _TOOL_ID_PARAM,
        "port": _PORT_PARAM,
    },
    required=["tool_id"],
)

SCHEMA_STOP_SERVICE = _make_schema(
    name="stop_service",
    description="Stop a running AI-LSC managed service.",
    properties={"tool_id": _TOOL_ID_PARAM},
    required=["tool_id"],
)

SCHEMA_CHECK_STATUS = _make_schema(
    name="check_service_status",
    description="Check whether an AI-LSC service is currently running "
                "and return its status.",
    properties={"tool_id": _TOOL_ID_PARAM},
    required=["tool_id"],
)

SCHEMA_PULL_MODEL = _make_schema(
    name="pull_model",
    description="Pull/download an Ollama model from the registry. "
                "Requires Ollama to be running.",
    properties={"model_name": _MODEL_NAME_PARAM},
    required=["model_name"],
)

SCHEMA_LIST_TOOLS = _make_schema(
    name="list_available_tools",
    description="List all tools in the AI-LSC registry, optionally "
                "filtered by layer, category, or status.",
    properties={
        "filter_layer": {
            "type": "string",
            "description": "Optional layer name filter "
                          "(e.g. 'Inference Engines', 'Data & Knowledge Pipelines').",
        },
        "filter_category": {
            "type": "string",
            "description": "Optional category filter "
                          "(e.g. 'Database', 'Cache', 'Vector Store').",
        },
        "running_only": {
            "type": "boolean",
            "description": "If true, only return currently running tools.",
        },
    },
)

SCHEMA_INJECT_SKILL = _make_schema(
    name="inject_skill",
    description="Inject a skill's system prompt into the current "
                "conversation context. The skill must be registered in "
                "the skills directory.",
    properties={
        "skill_name": _SKILL_NAME_PARAM,
        "params": {
            "type": "object",
            "description": "Optional key-value parameters for the skill.",
        },
    },
    required=["skill_name"],
)

SCHEMA_OPEN_WEB = _make_schema(
    name="open_web_interface",
    description="Open a tool's web interface in the browser.",
    properties={
        "tool_id": _TOOL_ID_PARAM,
        "port": _PORT_PARAM,
    },
    required=["tool_id"],
)

SCHEMA_SEARCH_REGISTRY = _make_schema(
    name="search_registry",
    description="Search the tool registry by keyword. Returns matching "
                "tools with their IDs, descriptions, layers, and status.",
    properties={"query": _QUERY_PARAM},
    required=["query"],
)

SCHEMA_INSTALL_TOOL = _make_schema(
    name="install_tool",
    description="Install a tool from the AI-LSC registry if not "
                "already present on the system.",
    properties={
        "tool_id": _TOOL_ID_PARAM,
    },
    required=["tool_id"],
)


# ── Convenience lookups ───────────────────────────────────────────────

CORE_SCHEMAS: list[dict[str, Any]] = [
    SCHEMA_START_SERVICE,
    SCHEMA_STOP_SERVICE,
    SCHEMA_CHECK_STATUS,
    SCHEMA_PULL_MODEL,
    SCHEMA_LIST_TOOLS,
    SCHEMA_INJECT_SKILL,
    SCHEMA_OPEN_WEB,
    SCHEMA_SEARCH_REGISTRY,
    SCHEMA_INSTALL_TOOL,
]

SCHEMA_BY_NAME: dict[str, dict[str, Any]] = {
    s["function"]["name"]: s for s in CORE_SCHEMAS
}
