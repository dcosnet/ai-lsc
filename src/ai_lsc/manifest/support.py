"""
AI-LSC — Manifest support.

Reads and writes ``.ai-lsc-project.json`` and ``.ai-lsc-jobs.json``
files that provide project-level context for the chat interface.
Pure filesystem + JSON work — no UI.

Manifest schema (``.ai-lsc-project.json``)::

    {
        "project":            "my-project",
        "description":       "Brief description for AI context",
        "language":          "python",
        "entry_point":       "src/main.py",
        "architecture":       "System architecture notes",
        "environment_notes": "Runtime environment details",
        "dependencies":       ["package1", "package2"],
        "context_files":      ["src/**/*.py", "README.md"],
        "exclude":            ["__pycache__", "*.pyc", ".git"]
    }

JCL schema (``.ai-lsc-jobs.json``)::

    {
        "jobs": [
            {"name": "...", "command": "...", "cwd": "..."},
            ...
        ]
    }
"""

from __future__ import annotations

import glob as glob_mod
import json
from pathlib import Path
from typing import Any

from ai_lsc.constants import MANIFEST_FILE_NAME, JCL_FILE_NAME

# Maximum directory traversal depth when searching for manifests.
_MAX_WALK_DEPTH: int = 20


class ManifestSupport:
    """Static utility class for manifest and JCL file operations."""

    @staticmethod
    def discover_manifest(directory: str | Path) -> Path | None:
        """Walk up from *directory* to find the nearest manifest file.

        Stops after ``_MAX_WALK_DEPTH`` iterations or when the
        filesystem root is reached.
        """
        current = Path(directory).resolve()
        for _ in range(_MAX_WALK_DEPTH):
            candidate = current / MANIFEST_FILE_NAME
            if candidate.exists():
                return candidate
            parent = current.parent
            if parent == current:
                return None
            current = parent
        return None

    @staticmethod
    def load_manifest(path: str | Path) -> dict[str, Any]:
        """Load and return the manifest dict, or ``{}`` on failure."""
        p = Path(path)
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return {}

    @staticmethod
    def build_system_context(manifest: dict[str, Any]) -> str:
        """Build a flat system-prompt text block from manifest data.

        Source-of-truth boundary: this method renders a *derived* view of
        the manifest dict. The manifest file itself is an optional
        convenience; if absent, callers fall back to defaults — the
        registry layer files in :mod:`ai_lsc.registry.layers` remain
        the authoritative source for tool definitions.
        """
        # (manifest_key, label) pairs in display order. Each entry whose
        # manifest value is truthy becomes one line in the prompt.
        _FIELDS: tuple[tuple[str, str], ...] = (
            ("description",       "Description"),
            ("language",          "Language"),
            ("entry_point",       "Entry Point"),
            ("architecture",      "Architecture"),
            ("environment_notes", "Environment"),
        )
        project = manifest.get("project", "Unknown Project")
        dependencies = manifest.get("dependencies", [])

        parts = [f"Project: {project}"]
        parts.extend(
            f"{label}: {manifest.get(key)}"
            for key, label in _FIELDS
            if manifest.get(key)
        )
        if dependencies:
            parts.append(f"Dependencies: {', '.join(dependencies)}")

        return "\n".join(parts)

    @staticmethod
    def resolve_context_files(
        manifest: dict[str, Any],
        base_dir: str | Path,
    ) -> list[str]:
        """Resolve glob patterns in the manifest to real file paths."""
        base = Path(base_dir)
        patterns = manifest.get("context_files", [])
        exclude = set(manifest.get("exclude", []))

        # Single-pass comprehension: expand every pattern, keep only
        # regular files whose path does not contain any excluded token.
        return [
            f
            for pattern in patterns
            for f in glob_mod.glob(str(base / pattern), recursive=True)
            if Path(f).is_file() and not any(ex in f for ex in exclude)
        ]

    @staticmethod
    def load_jcl(path: str | Path) -> list[dict[str, Any]]:
        """Load job entries from a JCL file, or ``[]`` on failure."""
        p = Path(path)
        if not p.exists():
            return []
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data.get("jobs", [])
        except (OSError, ValueError, json.JSONDecodeError):
            return []

    @staticmethod
    def create_manifest_template(path: str | Path) -> Path:
        """Write a starter manifest template to *path*.

        Returns the path of the created file.
        """
        p = Path(path)
        template = {
            "project": "my-project",
            "description": "Brief project description for AI context",
            "language": "python",
            "entry_point": "src/main.py",
            "architecture": "Describe the system architecture",
            "environment_notes": "Runtime environment details",
            "dependencies": ["package1", "package2"],
            "context_files": ["src/**/*.py", "README.md"],
            "exclude": ["__pycache__", "*.pyc", ".git", "node_modules"],
        }
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(template, indent=4), encoding="utf-8")
        return p
