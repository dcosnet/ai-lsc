"""
AI-LSC / Open Engineer -- Import Pipeline.

Imports Open Engineer files (context records, RFCs, spec documents,
examples) and converts them to StandardTemplate objects that can be
consumed by AI-LSC's StackTemplateManager.

The importer can operate in two modes:

1. **File import** -- Import a single OE markdown file and produce a
   StandardTemplate.  The engineering context is extracted from the
   markdown structure; the stack config must be provided separately
   or inferred from OE-0003 fields.

2. **Directory import** -- Scan an Open Engineer repository checkout
   (or any directory tree) and import all discoverable OE files.
   Produces a list of StandardTemplates.

Usage example::

    from ai_lsc.registry.openengineer.importer import OpenEngineerImporter

    imp = OpenEngineerImporter()
    templates = imp.import_directory("/path/to/openengineer")

    for t in templates:
        ai_lsc_tpl = standard_template_to_ai_lsc(t)
        # Pass to StackTemplateManager...
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_lsc.registry.openengineer.parser import OEContextParser
from ai_lsc.registry.openengineer.schema import (
    OE_REQUIRED_FIELDS,
    StandardTemplate,
    standard_template_to_ai_lsc,
)

# Directories in an OE repo that contain importable content.
_OE_CONTENT_DIRS: list[str] = [
    "examples",
    "spec",
    "rfc",
    "reference",
    "laws",
]

# File extensions we attempt to parse.
_OE_PARSE_EXTENSIONS: set[str] = {".md", ".markdown", ".txt"}

# Root-level files that are repo meta, not OE content.
_OE_ROOT_SKIP_NAMES: frozenset[str] = frozenset({
    "README.md", "CONTRIBUTING.md", "CHARTER.md",
    "LICENSE", "ROADMAP.md",
})


class OpenEngineerImporter:
    """Import Open Engineer files into StandardTemplate objects.

    Parameters
    ----------
    parser :
        Optional OEContextParser instance.  If None, a default
        (non-strict) parser is created.
    default_tools :
        Default tool IDs to include in stack_config when no tools
        are inferred from the OE content.
    """

    def __init__(
        self,
        parser: OEContextParser | None = None,
        default_tools: list[str] | None = None,
    ) -> None:
        self.parser = parser or OEContextParser(strict=False)
        self.default_tools = default_tools or []

    # ── Single file import ──────────────────────────────────────────

    def import_file(
        self,
        path: str | Path,
        stack_config: dict[str, Any] | None = None,
    ) -> StandardTemplate:
        """Import a single OE file into a StandardTemplate.

        Parameters
        ----------
        path :
            Path to the markdown file.
        stack_config :
            Optional AI-LSC stack configuration to merge.  If provided,
            these tools/endpoints/tags override any inferred values.

        Returns
        -------
        A :class:`StandardTemplate` with extracted context and
        (optionally) merged stack config.
        """
        p = Path(path)
        parsed = self.parser.parse_file(p)

        # Derive template ID from filename
        template_id = self._derive_template_id(p, parsed["title"])
        source_type = parsed["source_type"]

        # Build the StandardTemplate
        template = StandardTemplate(
            template_id=template_id,
            name=parsed["title"],
            source_file=str(p),
            source_type=source_type,
            engineering_context=parsed["context"],
            oe_spec_refs=self._extract_spec_refs(parsed, source_type),
            metadata={
                "parsed_sections": len(parsed["raw_sections"]),
                "oe_fields_found": [
                    k for k in OE_REQUIRED_FIELDS
                    if k in parsed["context"]
                ],
                "oe_fields_missing": [
                    k for k in OE_REQUIRED_FIELDS
                    if k not in parsed["context"]
                ],
            },
        )

        # Infer stack config from OE content when not provided
        inferred = self._infer_stack_config(parsed, template_id)
        if stack_config:
            inferred.update(stack_config)
        template.stack_config = inferred

        # Run conformance check
        template.check_conformance()

        return template

    # ── Directory import ───────────────────────────────────────────

    def import_directory(
        self,
        directory: str | Path,
        stack_config_overrides: dict[str, dict[str, Any]] | None = None,
    ) -> list[StandardTemplate]:
        """Scan an OE repo directory and import all content files.

        Parameters
        ----------
        directory :
            Root of the Open Engineer repository (or any directory
            containing markdown files with OE structure).
        stack_config_overrides :
            Optional dict mapping template_id to stack_config dicts.
            Used to provide AI-LSC tool mappings for specific OE files.

        Returns
        -------
        List of :class:`StandardTemplate` objects, sorted by source path.
        """
        root = Path(directory)
        if not root.is_dir():
            return []

        overrides = stack_config_overrides or {}
        templates: list[StandardTemplate] = []

        # Pass 1 — known OE content subdirs (templates inferred from OE fields).
        for subdir_name in _OE_CONTENT_DIRS:
            subdir = root / subdir_name
            if not subdir.is_dir():
                continue
            templates.extend(self._scan_dir(subdir, overrides=overrides, drop_unknown=False))

        # Pass 2 — root-level standalone OE files (drop unknowns so README/LICENSE/etc.
        # do not pollute the import). The _OE_ROOT_SKIP_NAMES filter applies here only.
        templates.extend(self._scan_dir(root, overrides=None, drop_unknown=True, skip=_OE_ROOT_SKIP_NAMES))

        return sorted(templates, key=lambda t: t.source_file)

    def _scan_dir(
        self,
        subdir: Path,
        *,
        overrides: dict[str, dict[str, Any]] | None = None,
        drop_unknown: bool = False,
        skip: frozenset[str] | None = None,
    ) -> list[StandardTemplate]:
        """Import every parseable file directly inside *subdir*.

        Single-responsibility scan loop: yields one StandardTemplate per
        parseable markdown file. Errors per file are swallowed so one bad
        file does not abort the scan.
        """
        results: list[StandardTemplate] = []
        for md_file in sorted(subdir.iterdir()):
            if not md_file.is_file():
                continue
            if md_file.suffix.lower() not in _OE_PARSE_EXTENSIONS:
                continue
            if md_file.name.startswith("."):
                continue
            if skip and md_file.name in skip:
                continue
            try:
                tpl_id = self._derive_template_id(md_file, md_file.stem)
                override = (overrides or {}).get(tpl_id)
                template = self.import_file(md_file, stack_config=override)
            except Exception:
                continue
            if drop_unknown and template.source_type == "unknown":
                continue
            results.append(template)
        return results

    # ── Bulk convert to AI-LSC format ──────────────────────────────

    def import_as_ai_lsc_templates(
        self,
        directory: str | Path,
        stack_config_overrides: dict[str, dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Import an OE directory and return AI-LSC-compatible template dicts.

        Convenience method that combines :meth:`import_directory` with
        :func:`standard_template_to_ai_lsc`.

        Returns
        -------
        List of dicts compatible with StackTemplateManager.
        """
        templates = self.import_directory(directory, stack_config_overrides)
        return [standard_template_to_ai_lsc(t) for t in templates]

    # ── Stack config inference ──────────────────────────────────────

    def _infer_stack_config(
        self,
        parsed: dict[str, Any],
        template_id: str,
    ) -> dict[str, Any]:
        """Infer AI-LSC stack config from OE content.

        Attempts to extract tool references, layer mappings, and
        endpoint configuration from the engineering context fields.
        """
        ctx = parsed["context"]
        config: dict[str, Any] = {
            "id": template_id,
            "tools": list(self.default_tools),
            "tags": self._infer_tags(parsed, ctx),
            "endpoints": {},
            "notes": {},
        }

        # Infer tools from context mentions
        mentioned_tools = self._extract_tool_mentions(ctx)
        for tool_id in mentioned_tools:
            if tool_id not in config["tools"]:
                config["tools"].append(tool_id)

        # Infer notes from supplementary context
        if "open_questions" in ctx:
            config["notes"]["open_questions"] = ctx["open_questions"]
        if "discipline_specific_data" in ctx:
            config["notes"]["discipline_data"] = ctx["discipline_specific_data"]
        if "traceability" in ctx:
            config["notes"]["traceability"] = ctx["traceability"]

        # Store source type in notes
        config["notes"]["oe_source_type"] = parsed["source_type"]
        config["notes"]["oe_metadata"] = parsed["metadata"]

        return config

    # ── Tool mention extraction ─────────────────────────────────────

    _KNOWN_TOOL_PATTERNS: list[tuple[str, str]] = [
        (r"\bollama\b", "ollama"),
        (r"\bvllm\b", "vllm"),
        (r"\bllama\.?cpp\b", "llamacpp"),
        (r"\blitellm\b", "litellm"),
        (r"\bopen\s*web\s*ui\b", "openwebui"),
        (r"\bqdrant\b", "qdrant"),
        (r"\bredis\b", "redis"),
        (r"\bchroma[\s-]?db\b", "chromadb"),
        (r"\bpostgres(?:ql)?\b", "postgresql"),
        (r"\bmaria[\s-]?db\b", "mariadb"),
        (r"\bgrafana\b", "grafana"),
        (r"\bprometheus\b", "prometheus"),
        (r"\bterraform\b", "terraform"),
        (r"\bansible\b", "ansible"),
        (r"\bpulumi\b", "pulumi"),
        (r"\bwhisper\b", "whisper"),
        (r"\bdocling\b", "docling"),
        (r"\bfabric\b", "fabric"),
        (r"\baider\b", "aider"),
        (r"\bclaude\s*code\b", "claude_code"),
        (r"\bcrewai\b", "crewai"),
        (r"\bautogen\b", "autogen"),
        (r"\bn8n\b", "n8n"),
        (r"\bdify\b", "dify"),
        (r"\bflowise\b", "flowise"),
        (r"\bopenjarvis\b", "openjarvis"),
        (r"\bhermes\b", "hermes"),
        (r"\bopendataloader\b", "opendataloader"),
        (r"\bgraphrag\b", "graphrag"),
        (r"\bcrawl4ai\b", "crawl4ai"),
        (r"\belasticsearch\b", "elasticsearch"),
        (r"\bneo4j\b", "neo4j"),
        (r"\blance[\s-]?db\b", "lancedb"),
    ]

    def _extract_tool_mentions(self, context: dict[str, str]) -> list[str]:
        """Scan context text for known AI-LSC tool name mentions."""
        import re

        full_text = "\n".join(context.values())
        found: list[str] = []
        seen: set[str] = set()

        for pattern, tool_id in self._KNOWN_TOOL_PATTERNS:
            if tool_id not in seen and re.search(pattern, full_text, re.IGNORECASE):
                found.append(tool_id)
                seen.add(tool_id)

        return found

    # ── Tag inference ───────────────────────────────────────────────

    def _infer_tags(
        self,
        parsed: dict[str, Any],
        context: dict[str, str],
    ) -> list[str]:
        """Generate tags from OE metadata and context content."""
        tags = ["openengineer"]

        source_type = parsed["source_type"]
        if source_type == "rfc":
            tags.extend(["rfc", "proposal"])
        elif source_type == "context_record":
            tags.extend(["context-record", "engineering-decision"])
        elif source_type == "spec":
            tags.extend(["specification", "standard"])
        elif source_type == "example":
            tags.extend(["example", "demonstration"])

        # Add discipline tags from content
        full_text = "\n".join(context.values()).lower()
        discipline_tags = [
            ("software", "software"),
            ("civil", "civil"),
            ("aerospace", "aerospace"),
            ("mechanical", "mechanical"),
            ("electrical", "electrical"),
            ("chemical", "chemical"),
            ("biomedical", "biomedical"),
            ("environmental", "environmental"),
            ("manufacturing", "manufacturing"),
        ]
        for keyword, tag in discipline_tags:
            if keyword in full_text and tag not in tags:
                tags.append(tag)

        # Add OE concept tags
        oe_concept_tags = [
            ("thread integrity", "thread-integrity"),
            ("stewardship", "stewardship"),
            ("inheritance", "inheritance"),
            ("spiral re-evaluation", "spiral-re-evaluation"),
            ("verification", "verification"),
            ("observation first", "observation-first"),
            ("bedrock", "bedrock"),
            ("enduring concept", "enduring-concept"),
        ]
        for keyword, tag in oe_concept_tags:
            if keyword in full_text and tag not in tags:
                tags.append(tag)

        return tags

    # ── Spec reference extraction ──────────────────────────────────

    @staticmethod
    def _extract_spec_refs(
        parsed: dict[str, Any],
        source_type: str,
    ) -> list[str]:
        """Extract OE specification document references from content."""
        import re

        full_text = "\n".join(
            f"{h}\n{c}" for h, c in parsed["raw_sections"]
        )

        # Find OE-NNNN references
        refs = set(re.findall(r"\b(OE-\d{4})\b", full_text))

        # Add implicit refs based on source type
        if source_type == "rfc":
            refs.add("OE-0000")  # All RFCs relate to the Charter
        elif source_type == "context_record":
            refs.add("OE-0003")  # Context records implement OE-0003

        return sorted(refs)

    # ── Template ID derivation ──────────────────────────────────────

    @staticmethod
    def _derive_template_id(path: Path, title: str) -> str:
        """Derive a stable template ID from path and title."""
        # Use parent dir name + filename stem for disambiguation
        parent = path.parent.name if path.parent.name else "root"
        stem = path.stem

        # Slugify
        raw = f"oe-{parent}-{stem}"
        slug = raw.lower().replace("_", "-").replace(" ", "-")
        # Collapse repeated hyphens
        while "--" in slug:
            slug = slug.replace("--", "-")
        return slug.strip("-")