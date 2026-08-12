"""Public skill resolver facade.

Re-exports :class:`~ai_lsc.agents.skill_resolver.EnhancedSkillResolver`
as ``SkillRuntimeResolver`` so that UI code can import from the stable
``ai_lsc.skills`` namespace without reaching into the ``agents`` sub-
package (which is marked as deferred/internal for v3.x).
"""

from ai_lsc.agents.skill_resolver import (
    EnhancedSkillResolver,
    SkillDefinition,
)

# Public name consumed by __init__.py, main_window.py, and
# ui/pages/skills_console.py.
SkillRuntimeResolver = EnhancedSkillResolver

__all__ = ["SkillRuntimeResolver", "SkillDefinition"]