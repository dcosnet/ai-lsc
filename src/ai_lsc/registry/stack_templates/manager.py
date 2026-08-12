"""Stack template manager -- loads, lists, and resolves templates.

Templates are JSON files in ``ai_lsc/registry/stack_templates/``.  Each
template defines:

* ``name``: human-readable template name
* ``description``: one-line summary
* ``tags``: searchable category labels
* ``version``: template version string
* ``tools``: list of tool references (registry IDs or git-source dicts)

The manager can resolve a template into a flat list of tool IDs by
merging registry lookups with git-source entries (which are auto-registered
as new tools on the fly).

Open Engineer Integration
-------------------------

When the ``openengineer`` sub-package is importable, the manager
automatically loads OE-derived standard templates.  These templates
carry full OE-0003 engineering context alongside AI-LSC stack config.

An optional ``openengineer_dir`` parameter (or the environment
variable ``AI_LSC_OE_DIR``) points to a local Open Engineer repo
checkout.  All OE markdown files are imported and converted to
AI-LSC templates via the standard template bridge.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_TEMPLATES_DIR = Path(__file__).resolve().parent

# Try to import the OE integration; fail gracefully if unavailable.
try:
    from ai_lsc.registry.openengineer.schema import (
        standard_template_to_ai_lsc,
    )
    from ai_lsc.registry.openengineer.templates import get_templates as _get_oe_templates
    from ai_lsc.registry.openengineer.importer import OpenEngineerImporter
    _HAS_OE = True
except ImportError:
    _HAS_OE = False


class StackTemplateManager:
    """Discover and resolve stack templates.

    Parameters
    ----------
    extra_dirs :
        Additional directories to scan for template files
        (e.g. user-supplied ``~/.config/ai-lsc/stack_templates/``).
    """

    def __init__(
        self,
        extra_dirs: list[str | Path] | None = None,
        openengineer_dir: str | Path | None = None,
    ) -> None:
        self._templates: dict[str, dict[str, Any]] = {}
        self._scan_dirs = [_TEMPLATES_DIR]
        if extra_dirs:
            self._scan_dirs.extend(
                Path(d) for d in extra_dirs if Path(d).is_dir()
            )
        self._oe_templates_count: int = 0
        self._load_all()

        # Load OE-derived templates
        if _HAS_OE:
            self._load_openengineer_templates(openengineer_dir)

    # ── Discovery ────────────────────────────────────────────────────

    def _load_all(self) -> None:
        """Scan all template directories and load valid templates."""
        for directory in self._scan_dirs:
            for fname in sorted(directory.iterdir()):
                if fname.suffix in (".json", ".yaml", ".yml"):
                    try:
                        tpl = self._load_file(fname)
                    except Exception:
                        continue
                    if tpl:
                        self._templates[tpl["id"]] = tpl

    @staticmethod
    def _load_file(path: Path) -> dict[str, Any] | None:
        """Load and validate a single template file."""
        suffix = path.suffix.lower()

        if suffix == ".json":
            raw = json.loads(path.read_text(encoding="utf-8"))
        else:
            # YAML support -- optional dependency
            try:
                import yaml  # noqa: F401
            except ImportError:
                return None
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))

        if not isinstance(raw, dict):
            return None
        if "name" not in raw or "tools" not in raw:
            return None

        # Synthesise a stable ID from the filename if not given
        raw.setdefault("id", path.stem)
        raw.setdefault("tags", [])
        raw.setdefault("version", "1.0")
        raw.setdefault("description", "")
        raw.setdefault("author", "ai-lsc")
        return raw

    # ── OpenEngineer integration ───────────────────────────────────

    def _load_openengineer_templates(
        self,
        openengineer_dir: str | Path | None = None,
    ) -> None:
        """Load built-in OE templates and optionally import from a repo dir.

        Built-in OE templates are always loaded (they carry full
        engineering context for key OE concepts).  If *openengineer_dir*
        is provided (or the ``AI_LSC_OE_DIR`` env var is set), all
        discoverable OE markdown files are also imported.
        """
        # 1. Load built-in OE-derived templates
        for oe_tpl in _get_oe_templates():
            ai_lsc_dict = standard_template_to_ai_lsc(oe_tpl)
            tid = ai_lsc_dict.get("id", "")
            if tid:
                self._templates[tid] = ai_lsc_dict
                self._oe_templates_count += 1

        # 2. Import from an Open Engineer repo directory (if provided)
        oe_dir = openengineer_dir or os.environ.get("AI_LSC_OE_DIR")
        if oe_dir and Path(oe_dir).is_dir():
            importer = OpenEngineerImporter()
            imported = importer.import_as_ai_lsc_templates(oe_dir)
            for tpl_dict in imported:
                tid = tpl_dict.get("id", "")
                if tid and tid not in self._templates:
                    self._templates[tid] = tpl_dict
                    self._oe_templates_count += 1

    def import_openengineer_file(
        self,
        path: str | Path,
        stack_config: dict[str, Any] | None = None,
    ) -> str | None:
        """Import a single Open Engineer file as an AI-LSC template.

        Parameters
        ----------
        path :
            Path to an OE markdown file.
        stack_config :
            Optional AI-LSC stack config to merge with inferred config.

        Returns
        -------
        The template ID of the imported template, or ``None`` on failure.
        """
        if not _HAS_OE:
            return None
        try:
            # M-41: OpenEngineerImporter already imported at module level
            # (line 44); don't re-import inside this method.
            importer = OpenEngineerImporter()
            oe_tpl = importer.import_file(path, stack_config=stack_config)
            ai_lsc_dict = standard_template_to_ai_lsc(oe_tpl)
            tid = ai_lsc_dict.get("id", "")
            if tid:
                self._templates[tid] = ai_lsc_dict
                self._oe_templates_count += 1
            return tid
        except (OSError, ValueError, KeyError, AttributeError):
            return None

    # ── Queries ──────────────────────────────────────────────────────

    def list_templates(self) -> list[dict[str, Any]]:
        """Return all loaded templates as summary dicts."""
        return [
            {
                "id": tpl["id"],
                "name": tpl["name"],
                "description": tpl.get("description", ""),
                "tags": tpl.get("tags", []),
                "version": tpl.get("version", "1.0"),
                "tool_count": len(tpl.get("tools", [])),
                "source": self._template_source(tpl),
            }
            for tpl in sorted(
                self._templates.values(), key=lambda t: t["name"]
            )
        ]

    def get_template(self, template_id: str) -> dict[str, Any] | None:
        """Return the full template dict, or ``None``."""
        return self._templates.get(template_id)

    def _is_builtin(self, template_id: str) -> bool:
        return any(
            (d / f"{template_id}.json").exists()
            or (d / f"{template_id}.yaml").exists()
            or (d / f"{template_id}.yml").exists()
            for d in self._scan_dirs
        )

    def _template_source(self, tpl: dict[str, Any]) -> str:
        """Determine the source category of a template."""
        tags = [t.lower() for t in tpl.get("tags", [])]
        notes = tpl.get("notes", {})

        # OE-native templates (built-in from the openengineer package)
        if "openengineer" in tags and "oe-context" in tags:
            return "openengineer"

        # OE-imported templates (from a repo directory)
        if "openengineer" in tags:
            return "openengineer-import"

        if self._is_builtin(tpl.get("id", "")):
            return "builtin"
        return "custom"

    def filter_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """Return templates matching a given tag."""
        return [
            t for t in self.list_templates()
            if tag.lower() in [x.lower() for x in t["tags"]]
        ]

    # ── Resolution ────────────────────────────────────────────────────

    def resolve_tool_ids(
        self,
        template_id: str,
        registry: object | None = None,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Resolve a template into registry tool IDs + new-tool entries.

        Parameters
        ----------
        template_id :
            The template to resolve.
        registry :
            Optional ``RegistryManager`` used to validate existing
            tool IDs and look up dependency chains.

        Returns
        -------
        (known_ids, new_entries) :
            *known_ids* are tool IDs already in the registry.
            *new_entries* are raw dicts for tools that need to be
            auto-registered (git-source entries).

        Example
        -------
        >>> ids, new = mgr.resolve_tool_ids("claude-code-setup", registry)
        >>> # ids = ["claude_code", "ollama", "aider", ...]
        >>> # new = [{"name": "Godmod3", "source": "https://...", ...}]
        """
        tpl = self._templates.get(template_id)
        if not tpl:
            return [], []

        known_ids: list[str] = []
        new_entries: list[dict[str, Any]] = []

        for tool_ref in tpl.get("tools", []):
            if isinstance(tool_ref, str):
                # Plain registry ID reference
                known_ids.append(tool_ref)
            elif isinstance(tool_ref, dict):
                # Structured reference
                if "id" in tool_ref:
                    known_ids.append(tool_ref["id"])
                elif "source" in tool_ref:
                    # Git-source: new tool to auto-register
                    new_entries.append(tool_ref)
                    # Synthesise an ID from the source URL
                    known_ids.append(tool_ref.get(
                        "id",
                        _derive_id_from_source(tool_ref["source"]),
                    ))

        # M-18: dedup while preserving order via dict.fromkeys()
        deduped_ids = list(dict.fromkeys(known_ids))

        return deduped_ids, new_entries

    # ── Creation ─────────────────────────────────────────────────────

    def create_template(
        self,
        name: str,
        tools: list[str | dict[str, Any]],
        description: str = "",
        tags: list[str] | None = None,
        template_id: str | None = None,
        save_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Create a new template and optionally save it to disk.

        Parameters
        ----------
        name :
            Human-readable template name.
        tools :
            List of tool IDs (str) or git-source dicts.
        description :
            One-line description.
        tags :
            Category labels for searchability.
        template_id :
            Override the auto-derived ID (defaults to slugified name).
        save_dir :
            Directory to write the JSON file.  If ``None`` the
            template is only kept in memory.

        Returns
        -------
        The created template dict.
        """
        tpl: dict[str, Any] = {
            "id": template_id or name.lower().replace(" ", "-").replace("_", "-"),
            "name": name,
            "description": description,
            "tags": tags or [],
            "version": "1.0",
            "author": "user",
            "tools": tools,
        }

        self._templates[tpl["id"]] = tpl

        if save_dir:
            out = Path(save_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{tpl['id']}.json").write_text(
                json.dumps(tpl, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )

        return tpl

    def delete_template(self, template_id: str) -> bool:
        """Remove a template (memory only, does not delete files)."""
        return self._templates.pop(template_id, None) is not None


def _derive_id_from_source(source: str) -> str:
    """Derive a tool ID from a git URL.

    Examples
    --------
    >>> _derive_id_from_source("https://github.com/user/my-tool")
    'my_tool'
    >>> _derive_id_from_source("https://github.com/user/my-tool.git")
    'my_tool'
    """
    # Strip trailing .git and get last path segment
    url = source.rstrip("/").removesuffix(".git")
    slug = url.rsplit("/", 1)[-1].lower()
    return slug.replace("-", "_")
