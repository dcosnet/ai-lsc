"""
AI-LSC — Enhanced skill resolver with dependency checking.

Extends the base ``SkillRuntimeResolver`` with:
  - Structured skill metadata from ``.skill.json`` companion files
  - Tool dependency resolution (skills that require running services)
  - Trigger-keyword matching for automatic skill activation
  - Skill categorization and filtering

Skill file layout
-----------------
A skill can now be accompanied by a ``.skill.json`` metadata file::

    skills/
        rag-analyst          ← Modelfile with SYSTEM block
        rag-analyst.skill.json  ← Structured metadata

The ``.skill.json`` format::

    {
        "name": "rag-analyst",
        "description": "Analyze documents using RAG pipeline",
        "required_tools": ["qdrant", "ollama"],
        "triggers": ["analyze document", "search knowledge base"],
        "input_schema": { ... },
        "category": "analysis"
    }

Usage
-----
    resolver = EnhancedSkillResolver(skills_root, registry_data)
    skill = resolver.resolve("rag-analyst")
    matches = resolver.find_by_trigger("analyze the quarterly report")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SkillDefinition:
    """Structured metadata for a single skill.

    Parameters
    ----------
    name :
        Skill identifier (matches the Modelfile filename).
    description :
        Human-readable description.
    system_prompt :
        Extracted SYSTEM block from the Modelfile.
    required_tools :
        Tool IDs from the registry that must be running.
    triggers :
        Keywords/phrases that should activate this skill.
    input_schema :
        JSON schema for skill input parameters.
    category :
        Skill category for grouping/filtering.
    extra :
        Additional metadata from the .skill.json file.
    """

    __slots__ = (
        "name", "description", "system_prompt",
        "required_tools", "triggers", "input_schema",
        "category", "extra",
    )

    def __init__(
        self,
        name: str,
        description: str = "",
        system_prompt: str = "",
        required_tools: list[str] | None = None,
        triggers: list[str] | None = None,
        input_schema: dict[str, Any] | None = None,
        category: str = "general",
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.required_tools = required_tools or []
        self.triggers = triggers or []
        self.input_schema = input_schema
        self.category = category
        self.extra = extra or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-safe dict."""
        return {
            "name": self.name,
            "description": self.description,
            "has_system_prompt": bool(self.system_prompt),
            "required_tools": self.required_tools,
            "triggers": self.triggers,
            "category": self.category,
            **self.extra,
        }


class EnhancedSkillResolver:
    """Enhanced skill resolver with metadata and dependency checking.

    Parameters
    ----------
    skills_root :
        Path to the skills directory.
    registry_data :
        Full registry dict for dependency resolution.
    """

    def __init__(
        self,
        skills_root: str | Path,
        registry_data: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.skills_root = Path(skills_root)
        self.registry = registry_data or {}
        self._cache: dict[str, SkillDefinition] = {}

    # ── Skill resolution ────────────────────────────────────────────

    def resolve(self, skill_name: str) -> SkillDefinition:
        """Resolve a skill by name, loading metadata from disk."""
        if skill_name in self._cache:
            return self._cache[skill_name]

        skill_file = self.skills_root / skill_name
        meta_file = self.skills_root / f"{skill_name}.skill.json"

        # Extract system prompt from Modelfile
        system_prompt = self._extract_system_prompt(skill_file)

        # Load metadata from companion JSON
        meta = self._load_skill_meta(meta_file)

        definition = SkillDefinition(
            name=meta.get("name", skill_name),
            description=meta.get(
                "description",
                self._extract_description(skill_file),
            ),
            system_prompt=system_prompt,
            required_tools=meta.get("required_tools", []),
            triggers=meta.get("triggers", []),
            input_schema=meta.get("input_schema"),
            category=meta.get("category", "general"),
            extra=meta,
        )
        self._cache[skill_name] = definition
        return definition

    # ── Trigger matching ─────────────────────────────────────────────

    def find_by_trigger(
        self, text: str,
    ) -> list[SkillDefinition]:
        """Find skills whose triggers match the given text.

        Used for automatic skill activation when a user message
        contains trigger keywords.
        """
        text_lower = text.lower()
        matches: list[SkillDefinition] = []
        for name in self._scan_skill_files():
            skill = self.resolve(name)
            for trigger in skill.triggers:
                if trigger.lower() in text_lower:
                    matches.append(skill)
                    break
        return matches

    # ── Dependency checking ─────────────────────────────────────────

    def check_dependencies(
        self,
        skill_name: str,
        active_tools: set[str],
    ) -> list[str]:
        """Return required tools that are not yet running.

        Parameters
        ----------
        skill_name :
            The skill to check.
        active_tools :
            Set of currently active tool IDs.
        """
        skill = self.resolve(skill_name)
        return [
            t for t in skill.required_tools
            if t not in active_tools
        ]

    def get_skills_for_active_tools(
        self,
        active_tools: set[str],
    ) -> list[SkillDefinition]:
        """Return all skills whose dependencies are satisfied."""
        results: list[SkillDefinition] = []
        for name in self._scan_skill_files():
            skill = self.resolve(name)
            missing = self.check_dependencies(name, active_tools)
            if not missing:
                results.append(skill)
        return results

    # ── Listing ──────────────────────────────────────────────────────

    def list_all(self) -> list[SkillDefinition]:
        """Return all skill definitions."""
        return [self.resolve(n) for n in self._scan_skill_files()]

    def list_by_category(
        self, category: str,
    ) -> list[SkillDefinition]:
        """Return skills filtered by category."""
        return [
            s for s in self.list_all()
            if s.category == category
        ]

    # ── Internal helpers ────────────────────────────────────────────

    def _scan_skill_files(self) -> list[str]:
        """Return names of Modelfile skill definitions."""
        if not self.skills_root.is_dir():
            return []
        return sorted(
            p.name for p in self.skills_root.iterdir()
            if p.is_file() and not p.name.endswith(".skill.json")
            and not p.name.endswith(".json")
        )

    def _extract_system_prompt(self, path: Path) -> str:
        """Extract SYSTEM block from a Modelfile."""
        if not path.exists():
            return ""
        import re
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""
        patterns = [
            (r'SYSTEM\s+"""(.*?)"""', re.DOTALL | re.IGNORECASE),
            (r'SYSTEM\s+"(.*?)"', re.IGNORECASE),
        ]
        return next(
            (m.group(1).strip()
             for pattern, flags in patterns
             for m in [re.search(pattern, content, flags)]
             if m),
            "",
        )

    def _extract_description(self, path: Path) -> str:
        """Extract a one-line description from a Modelfile."""
        prompt = self._extract_system_prompt(path)
        if not prompt:
            return ""
        first_line = prompt.split("\n")[0].strip()
        return first_line[:200] if first_line else ""

    @staticmethod
    def _load_skill_meta(path: Path) -> dict[str, Any]:
        """Load metadata from a .skill.json companion file."""
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
