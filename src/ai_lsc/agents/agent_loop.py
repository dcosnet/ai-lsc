"""
AI-LSC — Standalone headless agent execution loop.

Implements the multi-turn observation/action cycle for autonomous
agent execution without a GUI.  The loop:

    1. Sends user message + tool schemas to Ollama
    2. Receives response (may contain tool_calls)
    3. Executes tool_calls via AgentDispatcher
    4. Sends tool results back to Ollama
    5. Repeats until the model stops making tool calls

This enables headless operation where AI-LSC agents can orchestrate
the stack autonomously — e.g., "set up my RAG pipeline" would
trigger: start qdrant → pull embedding model → inject rag skill →
open webui.

Usage
-----
    loop = AgentLoop(dispatcher, ollama_port=11434, model="qwen2.5:72b")
    result = loop.run("Start the vector database and pull embedding model")
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)

# Safety limit: max tool-call rounds per user message
MAX_ROUNDS: int = 20


class AgentLoop:
    """Headless multi-turn agent execution loop.

    Parameters
    ----------
    dispatcher :
        An ``AgentDispatcher`` for executing tool calls.
    ollama_port :
        Port of the Ollama API server.
    model :
        Default model to use for agent conversations.
    system_prompt :
        Optional system prompt injected at the start.
    timeout :
        HTTP timeout per Ollama call in seconds.
    max_rounds :
        Maximum tool-call rounds before forcing a stop.
    """

    def __init__(
        self,
        dispatcher: Any,  # AgentDispatcher
        ollama_port: int = 11434,
        model: str = "qwen2.5:32b",
        system_prompt: str = "",
        timeout: float = 300.0,
        max_rounds: int = MAX_ROUNDS,
    ) -> None:
        self.dispatcher = dispatcher
        self.base_url = f"http://127.0.0.1:{ollama_port}"
        self.model = model
        self.system_prompt = system_prompt
        self.timeout = timeout
        self.max_rounds = max_rounds
        self.conversation_history: list[dict[str, str]] = []
        self._tool_schemas: list[dict[str, Any]] = []

    def set_tool_schemas(
        self, schemas: list[dict[str, Any]],
    ) -> None:
        """Set the tool schemas available to the agent."""
        self._tool_schemas = schemas

    # ── Main execution ────────────────────────────────────────────────

    def run(
        self,
        user_message: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Execute an agent task end-to-end.

        Parameters
        ----------
        user_message :
            The task description from the user.
        model :
            Override the default model for this run.

        Returns
        -------
        dict with ``final_response``, ``tool_calls_made``, ``rounds``.
        """
        use_model = model or self.model
        all_tool_calls: list[dict[str, Any]] = []

        # Build initial messages
        messages: list[dict[str, str]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_message})

        for round_num in range(self.max_rounds):
            logger.info(
                "Agent round %d/%d — model: %s",
                round_num + 1, self.max_rounds, use_model,
            )

            # Call Ollama
            response = self._call_ollama(messages, use_model)
            if response is None:
                break

            assistant_msg = response.get("message", {})
            content = assistant_msg.get("content", "")
            tool_calls = assistant_msg.get("tool_calls", [])

            messages.append(assistant_msg)

            # No tool calls → agent is done
            if not tool_calls:
                logger.info(
                    "Agent finished after %d rounds", round_num + 1,
                )
                self.conversation_history = messages
                return {
                    "final_response": content,
                    "tool_calls_made": all_tool_calls,
                    "rounds": round_num + 1,
                    "model": use_model,
                }

            # Execute each tool call
            for tc in tool_calls:
                func = tc.get("function", {})
                tc_name = func.get("name", "unknown")
                raw_args = func.get("arguments", "{}")
                try:
                    tc_args = json.loads(raw_args) if raw_args else {}
                except json.JSONDecodeError as exc:
                    # LLMs frequently emit malformed JSON tool-call arguments.
                    # Send the parse error back to the model so it can
                    # self-correct on the next round instead of crashing.
                    logger.warning(
                        "Malformed tool arguments for %s: %s (raw=%r)",
                        tc_name, exc, raw_args,
                    )
                    messages.append({
                        "role": "tool",
                        "content": json.dumps({
                            "error": "malformed_arguments",
                            "detail": str(exc),
                            "received": raw_args,
                        }),
                    })
                    continue

                logger.info("Executing tool: %s(%s)", tc_name, tc_args)
                result = self.dispatcher.execute_tool_call({
                    "name": tc_name,
                    "arguments": tc_args,
                })

                all_tool_calls.append({
                    "name": tc_name,
                    "arguments": tc_args,
                    "result": result,
                })

                # Send tool result back to Ollama
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result),
                })

        # Max rounds reached
        self.conversation_history = messages
        return {
            "final_response": "(Agent hit max rounds limit)",
            "tool_calls_made": all_tool_calls,
            "rounds": self.max_rounds,
            "model": use_model,
        }

    # ── Ollama HTTP ─────────────────────────────────────────────────

    def _call_ollama(
        self,
        messages: list[dict[str, str]],
        model: str,
    ) -> dict[str, Any] | None:
        """Send a chat request to Ollama. Returns parsed response."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if self._tool_schemas:
            payload["tools"] = self._tool_schemas

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(
                req, timeout=self.timeout
            ) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            logger.error("Ollama connection failed: %s", exc)
            return None
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.error("Agent loop error: %s", exc)
            return None
