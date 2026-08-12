"""
AI-LSC — Confidence-gated clarification gate.

Implements a three-tier clarification strategy that avoids interrupting
the user for obvious tasks while ensuring ambiguous requests get proper
scoping:

    1. **Skip** (confidence >= 0.95): Execute immediately, no questions.
    2. **Quick confirm** (confidence >= 0.70): Ask a single yes/no before proceeding.
    3. **Full clarification** (confidence < 0.70): Ask up to 6 focused questions.

The gate uses the 8B classifier model to estimate intent confidence,
then routes through the appropriate path.

Usage
-----
    gate = ClarificationGate(ollama_port=11434)
    decision = gate.evaluate("start qdrant on port 6333")
    # → ClarificationDecision(mode="skip", ...)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from ai_lsc.constants import (
    CLARIFICATION_CONFIRM_THRESHOLD,
    CLARIFICATION_SKIP_THRESHOLD,
)
from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ClarificationDecision:
    """Result of the clarification gate evaluation."""

    mode: str  # "skip", "confirm", "clarify"
    confidence: float
    intent: str
    tool_id: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    question: str = ""  # for "confirm" mode
    questions: list[dict[str, str]] = field(default_factory=list)  # for "clarify" mode

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "confidence": round(self.confidence, 3),
            "intent": self.intent,
            "tool_id": self.tool_id,
            "arguments": self.arguments,
            "question": self.question,
            "questions": self.questions,
        }


class ClarificationGate:
    """Confidence-gated clarification for agentic requests.

    Parameters
    ----------
    ollama_port :
        Port of the Ollama API server (classifier model).
    classifier_model :
        Small model used for intent classification (default 8B).
    timeout :
        HTTP timeout for classification calls.
    """

    def __init__(
        self,
        ollama_port: int = 11434,
        classifier_model: str = "qwen2.5:7b",
        timeout: float = 30.0,
    ) -> None:
        self.base_url = f"http://127.0.0.1:{ollama_port}"
        self.classifier_model = classifier_model
        self.timeout = timeout

    # ── Main evaluation ────────────────────────────────────────────────

    def evaluate(
        self,
        user_message: str,
        available_tools: list[str] | None = None,
    ) -> ClarificationDecision:
        """Evaluate a user message and return a clarification decision.

        Parameters
        ----------
        user_message :
            The raw user request.
        available_tools :
            Known tool IDs to help with classification.

        Returns
        -------
        A ClarificationDecision with the appropriate mode and data.
        """
        classification = self._classify(user_message, available_tools)

        confidence = classification.get("confidence", 0.5)
        intent = classification.get("intent", "unknown")
        tool_id = classification.get("tool_id", "")
        arguments = classification.get("arguments", {})

        if confidence >= CLARIFICATION_SKIP_THRESHOLD:
            return ClarificationDecision(
                mode="skip",
                confidence=confidence,
                intent=intent,
                tool_id=tool_id,
                arguments=arguments,
            )
        elif confidence >= CLARIFICATION_CONFIRM_THRESHOLD:
            question = (
                f"I'll {intent} using {tool_id or 'the appropriate tool'}. "
                f"Proceed?"
            )
            return ClarificationDecision(
                mode="confirm",
                confidence=confidence,
                intent=intent,
                tool_id=tool_id,
                arguments=arguments,
                question=question,
            )
        else:
            questions = self._generate_questions(
                user_message, intent, tool_id, available_tools
            )
            return ClarificationDecision(
                mode="clarify",
                confidence=confidence,
                intent=intent,
                tool_id=tool_id,
                arguments=arguments,
                questions=questions,
            )

    # ── Classification ─────────────────────────────────────────────────

    def _classify(
        self,
        message: str,
        tools: list[str] | None = None,
    ) -> dict[str, Any]:
        """Call the classifier model to extract intent, tool, and confidence."""
        tools_str = ", ".join(tools[:20]) if tools else "start_service, stop_service, check_service_status, pull_model, list_available_tools, inject_skill, open_web_interface, search_registry, install_tool"

        system_prompt = (
            "You are an intent classifier for the AI-LSC agentic system. "
            "Analyze the user's request and respond with ONLY valid JSON:\n"
            '{"intent": "<short action description>", '
            '"tool_id": "<ai_lsc tool identifier or empty string>", '
            '"arguments": {<tool parameters if known>}, '
            '"confidence": <0.0-1.0 float>}\n\n'
            f"Available tools: {tools_str}\n"
            "Respond with JSON only, no explanation."
        )

        payload = json.dumps({
            "model": self.classifier_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "stream": False,
            "options": {"temperature": 0.0},
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("message", {}).get("content", "")
                # Parse JSON from the response (may be wrapped in markdown)
                cleaned = content.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                return json.loads(cleaned)
        except (json.JSONDecodeError, urllib.error.URLError) as exc:
            logger.warning("Classification failed: %s", exc)
        except Exception as exc:
            logger.error("Classifier error: %s", exc)

        return {
            "intent": "unknown",
            "tool_id": "",
            "arguments": {},
            "confidence": 0.3,
        }

    # ── Question generation ─────────────────────────────────────────────

    def _generate_questions(
        self,
        message: str,
        intent: str,
        tool_id: str,
        tools: list[str] | None,
    ) -> list[dict[str, str]]:
        """Generate focused clarification questions for ambiguous requests.

        Returns up to 6 questions, each with a header and question string.
        """
        # Seed questions based on intent category
        seed_questions: list[dict[str, str]] = []

        if not tool_id and tools:
            seed_questions.append({
                "header": "Tool",
                "question": f"Which tool should I use? Options: {', '.join(tools[:8])}",
            })

        if "start" in intent or "deploy" in intent:
            seed_questions.extend([
                {"header": "Port", "question": "What port should the service listen on?"},
                {"header": "Config", "question": "Any specific configuration or model to use?"},
            ])
        elif "pull" in intent or "download" in intent:
            seed_questions.append({
                "header": "Model",
                "question": "Which specific model should I pull?",
            })
        elif "search" in intent or "find" in intent:
            seed_questions.extend([
                {"header": "Scope", "question": "What layer or category should I search in?"},
                {"header": "Filter", "question": "Any specific criteria (running only, web-enabled, etc.)?"},
            ])
        elif "analyze" in intent or "review" in intent:
            seed_questions.extend([
                {"header": "Target", "question": "What file, directory, or service should I analyze?"},
                {"header": "Depth", "question": "How thorough should the analysis be (quick vs deep)?"},
            ])

        # Fill remaining slots with general-purpose questions
        general = [
            {"header": "Priority", "question": "How urgent is this task?"},
            {"header": "Output", "question": "What output format do you prefer (text, JSON, file)?"},
            {"header": "Scope", "question": "Should this affect the running pipeline?"},
        ]

        used_headers = {q["header"] for q in seed_questions}
        for g in general:
            if len(seed_questions) >= 6:
                break
            if g["header"] not in used_headers:
                seed_questions.append(g)
                used_headers.add(g["header"])

        return seed_questions[:6]
