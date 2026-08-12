"""
AI-LSC — Agentic orchestration package.

**DEFERRED to v4.0** — This package is preserved for reference but is not
imported or used in v3.0 (Ankh of Jah).  The agentic tool-use bridge will
return in v4.0 with a redesigned architecture.

All symbols are set to ``None`` so that existing code referencing them
gracefully degrades rather than raising ``ImportError``.
"""

from __future__ import annotations

# All agent symbols set to None for v3.0 — will be reactivated in v4.0
ToolBridge = None
AgentDispatcher = None
AgentLoop = None
EnhancedSkillResolver = None
AgentOrchestrator = None
OrchestratorResult = None
WarmModelPool = None
ClarificationGate = None
ClarificationDecision = None
SkillInjector = None
RedisBridge = None
QdrantBridge = None
LiteLLMConfigGenerator = None
LibreChatConfigGenerator = None

__all__ = [
    "ToolBridge",
    "AgentDispatcher",
    "AgentLoop",
    "EnhancedSkillResolver",
    "AgentOrchestrator",
    "OrchestratorResult",
    "WarmModelPool",
    "ClarificationGate",
    "ClarificationDecision",
    "SkillInjector",
    "RedisBridge",
    "QdrantBridge",
    "LiteLLMConfigGenerator",
    "LibreChatConfigGenerator",
]
