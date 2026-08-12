"""
AI-LSC — Ollama tool schema registration.

.. deprecated::
    Ollama does **not** expose a persistent ``POST /api/tools`` endpoint
    for server-side tool registration (H-18).  Tools are passed inline
    in each ``/api/chat`` request via the ``tools`` field, which
    ``AgentLoop._call_ollama`` already does.  This module is retained
    for backwards compatibility but every registration call is a no-op
    that logs a warning.

Ollama tool-use flow (current)
------------------------------
1. Build tool schemas (this module's ``register_all`` is now a no-op).
2. Include schemas in the ``tools`` field of each ``POST /api/chat`` call.
3. Model returns ``tool_call`` objects in its response.
4. Client executes the tool call and sends the result back.
5. Model continues the conversation with tool results.

Usage
-----
    registrar = OllamaToolRegistrar(ollama_port=11434)
    # No longer registers server-side; callers should pass schemas inline.
    registrar.register_all(tool_schemas)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)


class OllamaToolRegistrar:
    """Register and manage tool schemas with a running Ollama instance.

    Parameters
    ----------
    ollama_port :
        Port of the Ollama API server.
    timeout :
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        ollama_port: int = 11434,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = f"http://127.0.0.1:{ollama_port}"
        self.timeout = timeout
        self._registered: set[str] = set()
        # H-18: Ollama's /api/tools endpoint does not exist; gate all
        # registration attempts behind a single warning so callers can
        # still call register_all() without breaking, but no network
        # roundtrip is attempted.
        self._registration_supported = False

    # ── Registration ──────────────────────────────────────────────────

    def register_all(
        self,
        schemas: list[dict[str, Any]],
    ) -> dict[str, bool]:
        """Register a list of tool schemas with Ollama.

        Returns a dict mapping tool name → success bool.  Always returns
        ``{name: False}`` for every schema in the current Ollama API;
        callers should pass the schemas inline to ``/api/chat`` instead.
        """
        if not self._registration_supported:
            logger.warning(
                "OllamaToolRegistrar.register_all(): Ollama has no "
                "persistent /api/tools endpoint. Pass tool schemas inline "
                "in each /api/chat request via the `tools` field instead."
            )
            return {
                s.get("function", {}).get("name", "unknown"): False
                for s in schemas
            }
        results: dict[str, bool] = {}
        for schema in schemas:
            func = schema.get("function", {})
            name = func.get("name", "unknown")
            try:
                self._register_single(schema)
                self._registered.add(name)
                results[name] = True
                logger.info("Registered tool: %s", name)
            except (urllib.error.URLError, OSError, RuntimeError) as exc:
                results[name] = False
                logger.warning("Failed to register %s: %s", name, exc)
        return results

    def register_single(
        self,
        schema: dict[str, Any],
    ) -> bool:
        """Register a single tool schema. Returns True on success.

        Currently always returns False (see H-18 note above).
        """
        if not self._registration_supported:
            logger.warning(
                "OllamaToolRegistrar.register_single(): not supported by "
                "current Ollama API; pass schemas inline to /api/chat."
            )
            return False
        func = schema.get("function", {})
        name = func.get("name", "unknown")
        try:
            self._register_single(schema)
            self._registered.add(name)
            logger.info("Registered tool: %s", name)
            return True
        except (urllib.error.URLError, OSError, RuntimeError) as exc:
            logger.warning("Failed to register %s: %s", name, exc)
            return False

    def _register_single(self, schema: dict[str, Any]) -> None:
        """POST a single tool schema to Ollama's /api/tools endpoint."""
        # Extract just the function definition for Ollama
        func_def = schema.get("function", {})
        payload = json.dumps({
            "name": func_def.get("name"),
            "description": func_def.get("description", ""),
            "parameters": func_def.get("parameters", {"type": "object", "properties": {}}),
        }).encode("utf-8")

        url = f"{self.base_url}/api/tools"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            if resp.status != 200:
                raise RuntimeError(
                    f"Ollama returned status {resp.status}"
                )

    # ── Querying ───────────────────────────────────────────────────────

    def list_registered_tools(self) -> list[str]:
        """Return names of tools registered in this session."""
        return sorted(self._registered)

    def check_ollama_health(self) -> bool:
        """Check if Ollama is reachable. Returns True if healthy."""
        try:
            req = urllib.request.Request(self.base_url + "/")
            with urllib.request.urlopen(
                req, timeout=self.timeout
            ) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError):
            return False

    def list_ollama_models(self) -> list[dict[str, Any]]:
        """Query Ollama for available models via /api/tags."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(
                req, timeout=self.timeout
            ) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("models", [])
        except (urllib.error.URLError, OSError, ValueError) as exc:
            logger.warning("Failed to list models: %s", exc)
            return []
