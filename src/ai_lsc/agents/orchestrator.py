"""
AI-LSC — 7-layer agentic orchestration pipeline.

Implements the full agentic architecture that transforms a user's natural
language request into a sequence of tool calls, skill injections, and
sub-agent operations:

    Layer 1: **Router** — Classify the request and route to the right handler.
    Layer 2: **Skill Loader** — Load relevant skill summaries and full prompts.
    Layer 3: **Clarification Gate** — Confidence-gated user interaction.
    Layer 4: **Outline Planner** — Generate a step-by-step execution plan.
    Layer 5: **Tool Orchestrator** — Translate plan into tool call sequences.
    Layer 6: **Subagent Spawner** — Delegate subtasks to specialized agents.
    Layer 7: **Quality Enforcer** — Validate results and retry if needed.

Each layer is optional and can be bypassed based on confidence scores
and task complexity.  Simple requests ("start qdrant") skip straight
from Router → Tool Orchestrator → execution.

Usage
-----
    orch = AgentOrchestrator(
        dispatcher=dispatcher,
        skill_resolver=skill_resolver,
        redis_bridge=redis_bridge,
        ollama_port=11434,
    )
    result = orch.execute("start the RAG pipeline and search quarterly report")
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from ai_lsc.agents.clarification_gate import ClarificationGate, ClarificationDecision
from ai_lsc.agents.model_pool import WarmModelPool
from ai_lsc.agents.redis_bridge import RedisBridge
from ai_lsc.agents.skill_injector import SkillInjector
from ai_lsc.agents.skill_resolver import EnhancedSkillResolver
from ai_lsc.constants import (
    AGENT_DEFAULT_MODEL,
    AGENT_MAX_ROUNDS,
    CLARIFICATION_SKIP_THRESHOLD,
)
from ai_lsc.utils.logging import get_logger

if TYPE_CHECKING:
    from ai_lsc.agents.dispatcher import AgentDispatcher

logger = get_logger(__name__)

# Word-boundary regex for detecting runtime errors in tool output.
# The negative lookahead `(?![\w\-])` ensures we don't flag legitimate
# hyphenated compounds like "error-correction module initialized" or
# word extensions like "errors occurred" — only standalone error words
# (followed by whitespace, punctuation, or end-of-string) are matched.
_ERROR_RE = re.compile(
    r"\b(?:error|failed|not found|timeout|exception|traceback)(?![\w\-])",
    re.IGNORECASE,
)


@dataclass
class OrchestratorResult:
    """Final result from the orchestration pipeline."""

    success: bool
    response: str
    layers_executed: list[str] = field(default_factory=list)
    tool_calls_made: list[dict[str, Any]] = field(default_factory=list)
    skills_loaded: list[str] = field(default_factory=list)
    rounds: int = 0
    model: str = ""
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "response": self.response,
            "layers_executed": self.layers_executed,
            "tool_calls_made": self.tool_calls_made,
            "skills_loaded": self.skills_loaded,
            "rounds": self.rounds,
            "model": self.model,
            "duration_seconds": round(self.duration_seconds, 2),
            "metadata": self.metadata,
        }


class AgentOrchestrator:
    """7-layer agentic orchestration pipeline.

    Parameters
    ----------
    dispatcher :
        An ``AgentDispatcher`` for executing tool calls.
    skill_resolver :
        An ``EnhancedSkillResolver`` for skill discovery.
    redis_bridge :
        A ``RedisBridge`` for hot-path coordination (can be None).
    skills_root :
        Path to the skills directory.
    ollama_port :
        Port of the Ollama API server.
    timeout :
        HTTP timeout per Ollama call in seconds.
    max_rounds :
        Maximum tool-call rounds per request.
    on_needs_clarification :
        Optional callback invoked when user clarification is needed.
        Receives a ``ClarificationDecision`` and should return the
        user's response (or an empty string to abort).
    """

    def __init__(
        self,
        dispatcher: "AgentDispatcher",
        skill_resolver: EnhancedSkillResolver,
        redis_bridge: RedisBridge | None = None,
        skills_root: str = "",
        ollama_port: int = 11434,
        timeout: float = 300.0,
        max_rounds: int = AGENT_MAX_ROUNDS,
        on_needs_clarification: Callable[[ClarificationDecision], str] | None = None,
    ) -> None:
        from ai_lsc.constants import BASE_DIR
        self.skills_root = skills_root or os.path.join(BASE_DIR, "skills")
        self.dispatcher = dispatcher
        self.skill_resolver = skill_resolver
        self.redis = redis_bridge
        self.ollama_port = ollama_port
        self.timeout = timeout
        self.max_rounds = max_rounds
        self.on_clarify = on_needs_clarification

        # Sub-components
        self.model_pool = WarmModelPool(ollama_port=ollama_port)
        self.clarification_gate = ClarificationGate(ollama_port=ollama_port)
        self.skill_injector = SkillInjector(skill_resolver, self.skills_root)

        # Active state tracking
        self.active_tools: set[str] = set()
        self._conversation_history: list[dict[str, str]] = []

    # ── Main Execution Entry Point ─────────────────────────────────────

    def execute(
        self,
        user_message: str,
        model: str | None = None,
        available_tools: list[str] | None = None,
    ) -> OrchestratorResult:
        """Execute a user request through the full orchestration pipeline.

        Parameters
        ----------
        user_message :
            The user's natural language request.
        model :
            Override the auto-selected model.
        available_tools :
            Explicit list of tool IDs the orchestrator can use.

        Returns
        -------
        An ``OrchestratorResult`` with the final output and metadata.
        """
        start_time = time.monotonic()
        layers_executed: list[str] = []
        tool_calls_made: list[dict[str, Any]] = []
        skills_loaded: list[str] = []
        use_model = model if model is not None else AGENT_DEFAULT_MODEL

        try:
            # ── Layer 1: Router ───────────────────────────────────
            route = self._route(user_message, available_tools)
            layers_executed.append("router")
            if model is None:
                use_model = route.get("model", use_model)
            logger.info(
                "Route: intent=%s, confidence=%.2f, model=%s",
                route.get("intent", "unknown"),
                route.get("confidence", 0),
                use_model,
            )

            # ── Layer 2: Skill Loader ────────────────────────────
            skills = self._load_skills(user_message)
            layers_executed.append("skill_loader")
            if skills:
                skills_loaded.extend(s.name for s in skills)
                logger.info("Loaded %d skills: %s", len(skills), [s.name for s in skills])

            # ── Layer 3: Clarification Gate ───────────────────────
            decision = self._clarify(user_message, available_tools)
            layers_executed.append("clarification_gate")

            if decision.mode == "clarify" and self.on_clarify:
                response = self.on_clarify(decision)
                if not response:
                    return OrchestratorResult(
                        success=False,
                        response="Request cancelled by user.",
                        layers_executed=layers_executed,
                        model=use_model,
                        duration_seconds=time.monotonic() - start_time,
                    )
                user_message = response  # User clarified
            elif decision.mode == "clarify":
                logger.info("Clarification needed but no callback — proceeding with defaults")

            # ── Layer 4: Outline Planner ───────────────────────────
            plan = self._plan(user_message, skills, decision)
            layers_executed.append("outline_planner")
            logger.info("Plan: %d steps", len(plan.get("steps", [])))

            # ── Layer 5: Tool Orchestrator ─────────────────────────
            results, calls = self._orchestrate(plan, use_model, skills)
            layers_executed.append("tool_orchestrator")
            tool_calls_made.extend(calls)

            # ── Layer 6: Subagent Spawner ──────────────────────────
            if plan.get("needs_subagents"):
                sub_results = self._spawn_subagents(plan, use_model)
                layers_executed.append("subagent_spawner")
                results.append(f"Sub-agent results: {json.dumps(sub_results)}")

            # ── Layer 7: Quality Enforcer ──────────────────────────
            final = self._enforce_quality(results, user_message)
            layers_executed.append("quality_enforcer")

            return OrchestratorResult(
                success=True,
                response=final,
                layers_executed=layers_executed,
                tool_calls_made=tool_calls_made,
                skills_loaded=skills_loaded,
                rounds=len(calls),
                model=use_model,
                duration_seconds=time.monotonic() - start_time,
            )

        except Exception as exc:
            logger.error("Orchestration failed: %s", exc)
            return OrchestratorResult(
                success=False,
                response=f"Orchestration error: {exc}",
                layers_executed=layers_executed,
                tool_calls_made=tool_calls_made,
                model=use_model,
                duration_seconds=time.monotonic() - start_time,
            )

    # ── Layer 1: Router ────────────────────────────────────────────────

    def _route(
        self,
        message: str,
        tools: list[str] | None,
    ) -> dict[str, Any]:
        """Classify the request and determine the best model tier."""
        classification = self.clarification_gate._classify(message, tools)

        intent = classification.get("intent", "unknown")
        tool_id = classification.get("tool_id", "")
        confidence = classification.get("confidence", 0.5)

        # Select model tier based on intent complexity
        task_type = self._intent_to_task_type(intent)
        model = self.model_pool.acquire(task_type)

        return {
            "intent": intent,
            "tool_id": tool_id,
            "confidence": confidence,
            "task_type": task_type,
            "model": model,
            "arguments": classification.get("arguments", {}),
        }

    @staticmethod
    def _intent_to_task_type(intent: str) -> str:
        """Map an intent string to a model task type."""
        intent_lower = intent.lower()
        if any(w in intent_lower for w in ["start", "stop", "check", "list", "install"]):
            return "classification"
        if any(w in intent_lower for w in ["summarize", "clarify", "explain"]):
            return "utility"
        if any(w in intent_lower for w in ["analyze", "reason", "review", "code", "script"]):
            return "reasoning"
        if any(w in intent_lower for w in ["generate", "write", "create", "document"]):
            return "generation"
        return "reasoning"

    # ── Layer 2: Skill Loader ─────────────────────────────────────────

    def _load_skills(
        self,
        message: str,
    ) -> list[Any]:
        """Find and load skills matching the user's request.

        Keyword triggers are used for matching today.  Semantic matching
        via Qdrant is tracked as a future enhancement (see TODO in this
        method) but is not yet wired up.
        """
        # TODO(security): add Qdrant-backed semantic skill search once the
        # embedding collection is provisioned.  Until then, keyword-only.
        matches = self.skill_resolver.find_by_trigger(message)

        return matches[:3]  # Limit to 3 skills max

    # ── Layer 3: Clarification Gate ───────────────────────────────────

    def _clarify(
        self,
        message: str,
        tools: list[str] | None,
    ) -> ClarificationDecision:
        """Run the clarification gate on the request."""
        return self.clarification_gate.evaluate(message, tools)

    # ── Layer 4: Outline Planner ──────────────────────────────────────

    def _plan(
        self,
        message: str,
        skills: list[Any],
        decision: ClarificationDecision,
    ) -> dict[str, Any]:
        """Generate an execution plan for the request.

        For high-confidence simple requests, the plan is a single step
        derived from the clarification decision. For complex requests,
        it calls the planner model.
        """
        # Simple path: use the decision directly
        if decision.mode == "skip" and decision.tool_id:
            return {
                "steps": [
                    {
                        "action": decision.intent,
                        "tool": decision.tool_id,
                        "arguments": decision.arguments,
                    }
                ],
                "needs_subagents": False,
                "complexity": "simple",
            }

        # Complex path: ask the model to plan
        plan = self._generate_plan(message, skills)
        return plan

    def _generate_plan(
        self,
        message: str,
        skills: list[Any],
    ) -> dict[str, Any]:
        """Use the planner model to generate a multi-step plan."""
        skill_names = [s.name for s in skills] if skills else []

        system_prompt = (
            "You are a task planner for the AI-LSC agentic system. "
            "Break the user's request into atomic steps. "
            "Respond with ONLY valid JSON:\n"
            '{"steps": [{"action": "<description>", "tool": "<tool_id or empty>", '
            '"arguments": {<params>}}, ...], '
            '"needs_subagents": <bool>, '
            '"complexity": "simple|moderate|complex"}'
        )

        if skill_names:
            system_prompt += f"\nAvailable skills: {', '.join(skill_names)}"

        try:
            import urllib.request

            payload = json.dumps({
                "model": AGENT_DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Plan this request: {message}"},
                ],
                "stream": False,
                "options": {"temperature": 0.0},
            }).encode("utf-8")

            req = urllib.request.Request(
                f"http://127.0.0.1:{self.ollama_port}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("message", {}).get("content", "").strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1]
                    if content.endswith("```"):
                        content = content[:-3]
                return json.loads(content)
        except Exception as exc:
            logger.warning("Plan generation failed: %s", exc)

        # Fallback plan
        return {
            "steps": [{"action": message, "tool": "", "arguments": {}}],
            "needs_subagents": False,
            "complexity": "simple",
        }

    # ── Layer 5: Tool Orchestrator ──────────────────────────────────────

    def _orchestrate(
        self,
        plan: dict[str, Any],
        model: str,
        skills: list[Any],
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Execute the plan steps via the dispatcher."""
        results: list[str] = []
        calls_made: list[dict[str, Any]] = []

        for step in plan.get("steps", []):
            tool_id = step.get("tool", "")
            action = step.get("action", "")
            arguments = step.get("arguments", {})

            if not tool_id:
                # No specific tool — let the agent loop handle it
                result = self._agent_execute(action, model, skills)
                results.append(result.get("final_response", ""))
                calls_made.extend(result.get("tool_calls_made", []))
            else:
                # Direct tool call
                result = self.dispatcher.execute_tool_call({
                    "name": tool_id,
                    "arguments": arguments,
                })
                results.append(result.get("result_text", ""))
                calls_made.append({
                    "name": tool_id,
                    "arguments": arguments,
                    "result": result,
                })

        return results, calls_made

    def _agent_execute(
        self,
        task: str,
        model: str,
        skills: list[Any],
    ) -> dict[str, Any]:
        """Use the agent loop for complex multi-tool tasks."""
        from ai_lsc.agents.agent_loop import AgentLoop

        # Build tool schemas
        from ai_lsc.agents.tool_bridge import ToolBridge
        bridge = ToolBridge(self.dispatcher.registry, self.active_tools)
        schemas = bridge.generate_all_schemas()

        loop = AgentLoop(
            dispatcher=self.dispatcher,
            ollama_port=self.ollama_port,
            model=model,
            system_prompt=self._build_system_prompt(skills),
            timeout=self.timeout,
            max_rounds=self.max_rounds,
        )
        loop.set_tool_schemas(schemas)

        # Inject skill summaries if available
        if skills:
            summary = self.skill_injector.build_skill_summary(self.active_tools)
            return loop.run(f"{summary}\n\nTask: {task}", model=model)

        return loop.run(task, model=model)

    def _build_system_prompt(self, skills: list[Any]) -> str:
        """Build the system prompt with skill context."""
        parts = [
            "You are the AI-LSC Stack Operator. You can manage the entire "
            "local AI tool stack using the provided tools. Always check "
            "service status before starting or stopping services.",
        ]
        if skills:
            parts.append(
                "\nActive skills: "
                + ", ".join(f"{s.name} ({s.description})" for s in skills)
            )
        return "\n".join(parts)

    # ── Layer 6: Subagent Spawner ──────────────────────────────────────

    def _spawn_subagents(
        self,
        plan: dict[str, Any],
        model: str,
    ) -> list[dict[str, Any]]:
        """Spawn sub-agents for parallelizable subtasks."""
        results: list[dict[str, Any]] = []

        for step in plan.get("steps", []):
            if step.get("parallelizable"):
                try:
                    sub_result = self._agent_execute(
                        step.get("action", ""),
                        model,
                        [],
                    )
                    results.append({
                        "step": step.get("action", ""),
                        "result": sub_result.get("final_response", ""),
                    })
                except Exception as exc:
                    results.append({
                        "step": step.get("action", ""),
                        "error": str(exc),
                    })

        return results

    # ── Layer 7: Quality Enforcer ──────────────────────────────────────

    def _enforce_quality(
        self,
        results: list[str],
        original_request: str,
    ) -> str:
        """Validate and refine the results.

        Uses word-boundary matching so legitimate phrases like
        "error-correction module initialized" are not flagged.
        """
        if not results:
            return "No results generated."

        # Check for error indicators in results (word-boundary regex).
        errors = [r for r in results if _ERROR_RE.search(r)]

        if errors:
            # Filter out errors, keep successful results
            clean = [r for r in results if r not in errors]
            if clean:
                return "\n".join(clean) + (
                    f"\n\n(Warnings: {len(errors)} step(s) had issues)"
                )
            return "All steps failed: " + "; ".join(errors[:3])

        return "\n".join(results)

    # ── Public API ─────────────────────────────────────────────────────

    def update_active_tools(self, tools: set[str]) -> None:
        """Update the set of currently active tools."""
        self.active_tools = set(tools)

    def get_status(self) -> dict[str, Any]:
        """Return orchestrator status for monitoring."""
        return {
            "model_pool": self.model_pool.status_summary(),
            "active_tools": sorted(self.active_tools),
            "conversation_length": len(self._conversation_history),
            "redis": self.redis.health_check() if self.redis else {"connected": False},
        }
