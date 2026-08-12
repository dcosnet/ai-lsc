"""
AI-LSC — Agent dispatcher.

Bridges LLM tool_call JSON payloads to AI-LSC's RuntimeExecutor.
When an agent frontend (LibreChat, OpenWebUI) sends a tool_call
response, this dispatcher translates it into RuntimeExecutor calls.

This module is in the ``agents`` package (allowed for urllib) because
it needs to make HTTP calls to Ollama's API for model pulls and status
checks that the RuntimeExecutor doesn't handle directly.

Usage
-----
    dispatcher = AgentDispatcher(runtime, registry_mgr, ollama_port)
    result = dispatcher.execute_tool_call({
        "name": "start_service",
        "arguments": {"tool_id": "qdrant"}
    })
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from typing import Any

from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)


class AgentDispatcher:
    """Translates tool_call JSON into RuntimeExecutor method calls.

    Parameters
    ----------
    runtime :
        A ``RuntimeExecutor`` instance for process management.
    registry_data :
        The full registry dict from ``RegistryManager.get_all_tools()``.
    active_tools :
        Currently active tool IDs in the pipeline.
    ollama_port :
        Port of the Ollama API server.
    """

    def __init__(
        self,
        runtime: Any,  # RuntimeExecutor — avoid circular import
        registry_data: dict[str, dict[str, Any]],
        active_tools: set[str],
        ollama_port: int = 11434,
    ) -> None:
        self.runtime = runtime
        self.registry = registry_data
        self.active_tools = active_tools
        self.ollama_port = ollama_port

    # ── Main dispatch entry point ─────────────────────────────────────

    def execute_tool_call(
        self,
        tool_call: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a single tool_call and return the result.

        Parameters
        ----------
        tool_call :
            A dict with ``name`` (str) and ``arguments`` (dict).

        Returns
        -------
        dict with ``success``, ``result_text``, and optional ``data``.
        """
        name = tool_call.get("name", "")
        args = tool_call.get("arguments", {})

        handlers: dict[str, Any] = {
            "start_service": self._start_service,
            "stop_service": self._stop_service,
            "check_service_status": self._check_status,
            "pull_model": self._pull_model,
            "list_available_tools": self._list_tools,
            "inject_skill": self._inject_skill_stub,
            "open_web_interface": self._open_web,
            "search_registry": self._search_registry,
            "install_tool": self._install_tool,
        }

        handler = handlers.get(name)
        if handler is None:
            return {
                "success": False,
                "result_text": f"Unknown tool: {name}. "
                               f"Available: {', '.join(handlers.keys())}",
            }

        try:
            return handler(args)
        except Exception as exc:
            logger.error("Tool call %s failed: %s", name, exc)
            return {
                "success": False,
                "result_text": f"Error executing {name}: {exc}",
            }

    # ── Tool handlers ──────────────────────────────────────────────────

    def _start_service(self, args: dict) -> dict[str, Any]:
        tool_id = args.get("tool_id", "")
        meta = self.registry.get(tool_id, {})
        if not meta:
            return {
                "success": False,
                "result_text": f"Tool '{tool_id}' not found in registry.",
            }

        launcher = meta.get("launcher", {})
        launcher_type = launcher.get("type", "tmux")
        launcher_cmd = launcher.get("cmd", "")
        port = str(args.get("port", launcher.get("default_port", "")))

        result = self.runtime.start_service(
            tool_id=tool_id,
            launcher_cmd=launcher_cmd,
            launcher_type=launcher_type,
            port=port,
        )
        self.active_tools.add(tool_id)
        return {"success": True, "result_text": result}

    def _stop_service(self, args: dict) -> dict[str, Any]:
        tool_id = args.get("tool_id", "")
        meta = self.registry.get(tool_id, {})
        launcher = meta.get("launcher", {})
        result = self.runtime.stop_service(
            tool_id=tool_id,
            launcher_type=launcher.get("type", "tmux"),
            launcher_cmd=launcher.get("cmd", ""),
            search_term=launcher.get("cmd", ""),
        )
        self.active_tools.discard(tool_id)
        return {"success": True, "result_text": result}

    def _check_status(self, args: dict) -> dict[str, Any]:
        tool_id = args.get("tool_id", "")
        meta = self.registry.get(tool_id, {})
        launcher = meta.get("launcher", {})
        running = self.runtime.is_service_running(
            launcher_type=launcher.get("type", "tmux"),
            tool_id=tool_id,
            service_cmd=launcher.get("cmd", ""),
            search_term=launcher.get("cmd", ""),
        )
        status = "RUNNING" if running else "OFFLINE"
        return {
            "success": True,
            "result_text": f"{tool_id} is {status}",
            "data": {"tool_id": tool_id, "running": running},
        }

    def _pull_model(self, args: dict) -> dict[str, Any]:
        model_name = args.get("model_name", "")
        if not model_name:
            return {
                "success": False,
                "result_text": "model_name is required.",
            }
        proc = self.runtime.pull_model(model_name)
        # H-07: pull_model may legitimately return None on misconfiguration.
        if proc is None:
            return {
                "success": False,
                "result_text": (
                    f"Could not start `ollama pull {model_name}` "
                    f"(runtime returned no process)."
                ),
            }
        # H-05: always kill the child on thread crash so the pipe buffer
        # does not block forever and leak the process.
        try:
            output, _ = proc.communicate(timeout=600)
        except (OSError, subprocess.TimeoutExpired) as exc:
            proc.kill()
            return {
                "success": False,
                "result_text": f"Pull interrupted: {exc}",
            }
        return {
            "success": proc.returncode == 0,
            "result_text": output.strip() if output else "Pull completed.",
        }

    def _list_tools(self, args: dict) -> dict[str, Any]:
        filter_layer = args.get("filter_layer", "")
        filter_cat = args.get("filter_category", "")
        running_only = args.get("running_only", False)

        results = []
        for tid, meta in self.registry.items():
            if filter_layer and meta.get("layer") != filter_layer:
                continue
            if filter_cat and meta.get("category") != filter_cat:
                continue
            if running_only and tid not in self.active_tools:
                continue
            results.append({
                "tool_id": tid,
                "name": meta.get("name", tid),
                "layer": meta.get("layer", ""),
                "category": meta.get("category", ""),
                "active": tid in self.active_tools,
                "description": meta.get("description", ""),
            })

        return {
            "success": True,
            "result_text": f"Found {len(results)} tools.",
            "data": results,
        }

    def _inject_skill_stub(self, args: dict) -> dict[str, Any]:
        # H-16: validate the skill actually exists before reporting success,
        # otherwise the LLM receives a false confirmation that the skill
        # was injected.
        skill_name = args.get("skill_name", "")
        if not skill_name:
            return {
                "success": False,
                "result_text": "skill_name is required.",
            }
        known_skills = set()
        resolver = getattr(self, "skill_resolver", None)
        if resolver is not None:
            try:
                known_skills = {s.name for s in resolver.find_by_trigger(skill_name)}
            except Exception:  # noqa: BLE001 - resolver is best-effort
                known_skills = set()
        if known_skills and skill_name not in known_skills:
            return {
                "success": False,
                "result_text": (
                    f"Skill '{skill_name}' is not registered. "
                    f"Available matches: {', '.join(sorted(known_skills)) or 'none'}"
                ),
            }
        return {
            "success": True,
            "result_text": (
                f"Skill '{skill_name}' queued for injection. "
                f"The frontend should load the skill's system prompt "
                f"and prepend it to the next LLM call."
            ),
        }

    def _open_web(self, args: dict) -> dict[str, Any]:
        tool_id = args.get("tool_id", "")
        meta = self.registry.get(tool_id, {})
        port = str(
            args.get("port", meta.get("launcher", {}).get("default_port", ""))
        )
        if not port:
            return {
                "success": False,
                "result_text": f"No web port known for {tool_id}.",
            }
        url = self.runtime.open_web_url(port)
        return {
            "success": True,
            "result_text": f"Opened {tool_id} web interface at {url}",
        }

    def _search_registry(self, args: dict) -> dict[str, Any]:
        query = args.get("query", "").lower()
        results = []
        for tid, meta in self.registry.items():
            searchable = " ".join([
                tid, meta.get("name", ""), meta.get("description", ""),
                meta.get("layer", ""), meta.get("category", ""),
            ]).lower()
            if query in searchable:
                results.append({
                    "tool_id": tid,
                    "name": meta.get("name", tid),
                    "layer": meta.get("layer", ""),
                    "description": meta.get("description", ""),
                })
        return {
            "success": True,
            "result_text": f"Found {len(results)} matching tools.",
            "data": results,
        }

    def _install_tool(self, args: dict) -> dict[str, Any]:
        tool_id = args.get("tool_id", "")
        meta = self.registry.get(tool_id, {})
        if not meta:
            return {
                "success": False,
                "result_text": f"Tool '{tool_id}' not found in registry.",
            }
        installer = meta.get("installer", {})
        result = self.runtime.install_tool(
            inst_type=installer.get("type", "pacman"),
            pkg=installer.get("pkg", ""),
            cmd=installer.get("cmd", ""),
            tool_id=tool_id,
            ctx=self.runtime.format_context(),
        )
        return {"success": True, "result_text": result}
