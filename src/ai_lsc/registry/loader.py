"""Registry loader -- discovers and merges per-layer registry modules.

On startup the loader scans ``ai_lsc.registry.layers`` for every
``.py`` file that exports a ``TOOLS`` dict, and merges them into a
single unified registry dict.

This replaces the monolithic ``DEFAULT_REGISTRY`` dict with a
zero-merge-conflict modular approach: each layer lives in its own
file and is independently editable.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import Any

logger = logging.getLogger(__name__)

# ── Hard blacklist: IDs that must NEVER appear in the registry ──
_BLACKLISTED_IDS = frozenset({
    "wayland",
    "wayland_compositor",
})


def _evict_blacklisted(registry: dict[str, dict[str, Any]]) -> None:
    """Remove blacklisted tool IDs from the merged registry."""
    evicted = [tid for tid in registry if tid in _BLACKLISTED_IDS]
    for tid in evicted:
        del registry[tid]
        logger.warning("Registry blacklist evicted: %s", tid)


def load_merged_registry() -> dict[str, dict[str, Any]]:
    """Discover and merge all layer TOOLS dicts into one registry dict.

    Each layer module should export ``TOOLS: dict[str, dict]`` where
    keys are tool IDs and values are the full metadata dicts.

    Returns the merged ``{tool_id: metadata}`` dictionary, with later
    files overriding earlier ones on key collision (which should never
    happen if layers are well-separated).
    """
    merged: dict[str, dict[str, Any]] = {}

    # Import the layers package
    try:
        layers_pkg = importlib.import_module("ai_lsc.registry.layers")
    except ImportError:
        return merged

    for importer, modname, ispkg in pkgutil.iter_modules(
        layers_pkg.__path__, prefix=layers_pkg.__name__ + "."
    ):
        if ispkg:
            continue
        try:
            mod = importlib.import_module(modname)
        except ImportError:
            continue

        tools = getattr(mod, "TOOLS", None)

        if isinstance(tools, dict):
            # Dict format: {tool_id: metadata, ...}
            _merge_tools_dict(merged, tools)
        elif isinstance(tools, list):
            # Legacy list format: [{...}, ...]
            _merge_tools_list(merged, tools)

    _evict_blacklisted(merged)
    return merged


def _merge_tools_dict(
    target: dict[str, dict[str, Any]],
    tools: dict[str, dict[str, Any]],
) -> None:
    """Merge a ``TOOLS`` dict into the target registry dict."""
    for tool_id, entry in tools.items():
        if not isinstance(entry, dict):
            continue
        # Inject tool_id into entry if missing
        if "tool_id" not in entry:
            entry = {**entry, "tool_id": tool_id}
        target[tool_id] = entry


def _merge_tools_list(
    target: dict[str, dict[str, Any]],
    tools: list[dict[str, Any]],
) -> None:
    """Merge a legacy ``TOOLS`` list into the target registry dict."""
    for entry in tools:
        if not isinstance(entry, dict):
            continue
        tool_id = entry.get("tool_id")
        if tool_id is None:
            name = entry.get("name", "")
            tool_id = name.lower().replace(" ", "_").replace("/", "_")
        entry["tool_id"] = tool_id
        target[tool_id] = entry

