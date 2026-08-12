"""AI-LSC skills sub-package.

Provides the public ``SkillRuntimeResolver`` facade used by the UI
(SkillsConsole) and the main window.  The heavy lifting is delegated to
:mod:`ai_lsc.agents.skill_resolver` which contains
``EnhancedSkillResolver`` with full metadata, dependency-checking, and
trigger-matching capabilities.
"""

from ai_lsc.skills.resolver import SkillRuntimeResolver  # noqa: F401

__all__ = ["SkillRuntimeResolver"]