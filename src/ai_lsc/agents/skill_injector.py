"""
AI-LSC — Three-phase skill injection.

Manages progressive skill loading into agent context to minimize token
usage while maximizing capability:

    Phase 1: **Summary** — One-line skill description injected into the
              system prompt so the agent knows what skills exist.
    Phase 2: **Full skill** — Complete system prompt loaded when the agent
              selects a skill for a task.
    Phase 3: **Sub-files** — Additional reference files loaded on demand
              (e.g. examples, templates, schema files).

This avoids stuffing 50+ skill system prompts into context up front.

Usage
-----
    injector = SkillInjector(skill_resolver, skills_root)
    # Phase 1: Build summary for system prompt
    summary = injector.build_skill_summary()
    # Phase 2: Get full skill prompt
    full = injector.get_full_prompt("rag-analyst")
    # Phase 3: Load sub-files for deep context
    subs = injector.load_sub_files("rag-analyst", ["examples/", "schema.json"])
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_lsc.agents.skill_resolver import EnhancedSkillResolver, SkillDefinition
from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)


class SkillInjector:
    """Three-phase skill injection manager.

    Parameters
    ----------
    skill_resolver :
        An ``EnhancedSkillResolver`` for loading skill metadata.
    skills_root :
        Path to the skills directory on disk.
    """

    def __init__(
        self,
        skill_resolver: EnhancedSkillResolver,
        skills_root: str | Path,
    ) -> None:
        self.resolver = skill_resolver
        self.skills_root = Path(skills_root)
        self._phase2_cache: dict[str, str] = {}
        self._phase3_cache: dict[str, dict[str, str]] = {}

    # ── Phase 1: Skill Summary ─────────────────────────────────────────

    def build_skill_summary(self, active_tools: set[str] | None = None) -> str:
        """Build a compact summary of all available skills.

        This is injected into the system prompt so the agent knows
        what skills exist without loading their full prompts.

        Parameters
        ----------
        active_tools :
            Currently active tool IDs — skills whose deps are met
            are marked as [READY], others as [needs: deps...].

        Returns
        -------
        A multi-line summary string suitable for system prompt injection.
        """
        active = active_tools or set()
        lines = ["Available Skills:", "=" * 40]

        skills = self.resolver.list_all()
        if not skills:
            lines.append("  (no skills registered)")
            return "\n".join(lines)

        for skill in skills:
            missing = self.resolver.check_dependencies(skill.name, active)
            if not missing:
                status = "[READY]"
            else:
                status = f"[needs: {', '.join(missing)}]"

            triggers = ", ".join(skill.triggers[:3]) if skill.triggers else "no triggers"
            lines.append(
                f"  {skill.name} {status} — {skill.description}\n"
                f"    Triggers: {triggers}"
            )

        lines.append("")
        lines.append(
            "Use inject_skill to load a skill's full prompt. "
            "Only READY skills can be used immediately."
        )
        return "\n".join(lines)

    # ── Phase 2: Full Skill Prompt ─────────────────────────────────────

    def get_full_prompt(self, skill_name: str) -> str:
        """Load the complete system prompt for a skill.

        Cached after first load to avoid repeated disk I/O.

        Parameters
        ----------
        skill_name :
            The skill identifier.

        Returns
        -------
        The full system prompt text, or an error message if not found.
        """
        if skill_name in self._phase2_cache:
            return self._phase2_cache[skill_name]

        skill = self.resolver.resolve(skill_name)

        if not skill.system_prompt:
            msg = f"Skill '{skill_name}' has no SYSTEM block defined."
            logger.warning(msg)
            self._phase2_cache[skill_name] = msg
            return msg

        # Wrap the system prompt with skill context
        prompt_parts = [
            f"<skill name=\"{skill.name}\">",
            f"<description>{skill.description}</description>",
            f"<category>{skill.category}</category>",
        ]

        if skill.input_schema:
            import json
            schema_str = json.dumps(skill.input_schema, indent=2)
            prompt_parts.append(
                f"<input_schema>\n{schema_str}\n</input_schema>"
            )

        if skill.required_tools:
            prompt_parts.append(
                f"<required_tools>{', '.join(skill.required_tools)}</required_tools>"
            )

        prompt_parts.append(f"<system_prompt>\n{skill.system_prompt}\n</system_prompt>")
        prompt_parts.append("</skill>")

        full_prompt = "\n".join(prompt_parts)
        self._phase2_cache[skill_name] = full_prompt
        logger.info("Loaded full prompt for skill: %s (%d chars)",
                     skill_name, len(full_prompt))
        return full_prompt

    # ── Phase 3: Sub-files ──────────────────────────────────────────────

    def load_sub_files(
        self,
        skill_name: str,
        file_paths: list[str],
    ) -> dict[str, str]:
        """Load additional reference files for a skill.

        Sub-files are stored alongside the skill in a directory
        named ``<skill_name>.d/``::

            skills/
                rag-analyst           ← Modelfile
                rag-analyst.skill.json ← Metadata
                rag-analyst.d/         ← Sub-files directory
                    examples/
                        query.txt
                    schema.json
                    prompts/
                        summarize.txt

        Parameters
        ----------
        skill_name :
            The skill identifier.
        file_paths :
            Relative paths within the skill's ``.d/`` directory.

        Returns
        -------
        A dict mapping file path → content string.
        """
        cache_key = skill_name
        if cache_key not in self._phase3_cache:
            self._phase3_cache[cache_key] = {}

        results: dict[str, str] = {}
        skill_dir = self.skills_root / f"{skill_name}.d"

        for rel_path in file_paths:
            # Check cache first
            if rel_path in self._phase3_cache[cache_key]:
                results[rel_path] = self._phase3_cache[cache_key][rel_path]
                continue

            full_path = skill_dir / rel_path
            if not full_path.exists():
                results[rel_path] = f"[File not found: {rel_path}]"
                continue

            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                results[rel_path] = content
                self._phase3_cache[cache_key][rel_path] = content
                logger.info("Loaded sub-file for %s: %s (%d chars)",
                             skill_name, rel_path, len(content))
            except OSError as exc:
                results[rel_path] = f"[Error reading {rel_path}: {exc}]"
                logger.warning("Failed to load sub-file %s/%s: %s",
                               skill_name, rel_path, exc)

        return results

    def list_sub_files(self, skill_name: str) -> list[str]:
        """List available sub-files for a skill."""
        skill_dir = self.skills_root / f"{skill_name}.d"
        if not skill_dir.is_dir():
            return []
        return sorted(
            str(p.relative_to(skill_dir))
            for p in skill_dir.rglob("*")
            if p.is_file()
        )

    # ── Cache management ───────────────────────────────────────────────

    def clear_cache(self, skill_name: str | None = None) -> None:
        """Clear cached prompts. If skill_name is None, clears all."""
        if skill_name is None:
            self._phase2_cache.clear()
            self._phase3_cache.clear()
        else:
            self._phase2_cache.pop(skill_name, None)
            self._phase3_cache.pop(skill_name, None)

    def get_injection_context(
        self,
        skill_name: str,
        active_tools: set[str],
        include_sub_files: bool = False,
    ) -> dict[str, Any]:
        """Build the complete injection context for a skill.

        Returns a dict with all phases assembled, ready for the
        dispatcher to send back to the LLM.
        """
        skill = self.resolver.resolve(skill_name)
        missing = self.resolver.check_dependencies(skill_name, active_tools)

        context: dict[str, Any] = {
            "skill_name": skill.name,
            "description": skill.description,
            "category": skill.category,
            "missing_deps": missing,
            "ready": len(missing) == 0,
            "full_prompt": self.get_full_prompt(skill_name) if not missing else "",
        }

        if include_sub_files and not missing:
            available_subs = self.list_sub_files(skill_name)
            if available_subs:
                context["sub_files"] = self.load_sub_files(
                    skill_name, available_subs[:5]  # limit to 5 sub-files
                )

        return context
