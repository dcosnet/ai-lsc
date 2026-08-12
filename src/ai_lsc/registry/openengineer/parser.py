"""
AI-LSC / Open Engineer -- Context Record Parser.

Parses Open Engineer markdown files into structured engineering context
records.  Supports the three OE document types that carry usable
engineering context:

* **Context Records** (examples/, spec/ OE-0003 format) -- structured
  records with the 9 required fields (Decision, Observation, Alternatives,
  Constraints, Reasoning, Verification, Lineage, Assumptions).

* **RFCs** (rfc/) -- proposals with Abstract, Motivation, Observation,
  Engineering Principle, Reasoning, Relationship sections.

* **Spec Documents** (spec/) -- formal specification documents with
  Definition sections, Law references, and structured content.

The parser uses heading-level heuristics and field-name matching to
extract context from prose markdown.  It does not require rigid front-
matter -- it follows the OE principle that structure carries meaning.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# ── OE field name canonicalization ──────────────────────────────────

# Maps common heading variations to canonical OE-0003 field names.
_FIELD_ALIASES: dict[str, str] = {
    # Direct OE-0003 field names
    "decision": "decision",
    "observation": "observation",
    "observations": "observation",
    "alternatives": "alternatives",
    "alternative": "alternatives",
    "constraints": "constraints",
    "constraint": "constraints",
    "reasoning": "reasoning",
    "verification": "verification",
    "lineage": "lineage",
    "assumptions": "assumptions",
    "assumption": "assumptions",
    # Supplementary fields
    "open questions": "open_questions",
    "discipline-specific data": "discipline_specific_data",
    "traceability": "traceability",
    # RFC-specific sections -> OE context mapping
    "abstract": "decision",
    "motivation": "observation",
    "proposal": "decision",
    "engineering principle": "reasoning",
    "relationship to existing concepts": "lineage",
    "relationship": "lineage",
    # Spec document sections -> OE context mapping
    "definition": "decision",
    "overview": "observation",
    "scope": "constraints",
    "applicable laws": "constraints",
    "known limitations": "assumptions",
    "implications": "reasoning",
}

# Heading patterns for each OE field -- order matters (more specific first).
_HEADING_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^#+\s*(?:##\s*)?Decision\s*[:\-]?\s*", re.IGNORECASE), "decision"),
    (re.compile(r"^#+\s*(?:##\s*)?Observation\s*[:\-]?\s*", re.IGNORECASE), "observation"),
    (re.compile(r"^#+\s*(?:##\s*)?Alternatives?\s*[:\-]?\s*", re.IGNORECASE), "alternatives"),
    (re.compile(r"^#+\s*(?:##\s*)?Constraint\s*[:\-]?\s*", re.IGNORECASE), "constraints"),
    (re.compile(r"^#+\s*(?:##\s*)?Reasoning\s*[:\-]?\s*", re.IGNORECASE), "reasoning"),
    (re.compile(r"^#+\s*(?:##\s*)?Verification\s*[:\-]?\s*", re.IGNORECASE), "verification"),
    (re.compile(r"^#+\s*(?:##\s*)?Lineage\s*[:\-]?\s*", re.IGNORECASE), "lineage"),
    (re.compile(r"^#+\s*(?:##\s*)?Assumption\s*[:\-]?\s*", re.IGNORECASE), "assumptions"),
    (re.compile(r"^#+\s*(?:##\s*)?Open\s+Questions?\s*[:\-]?\s*", re.IGNORECASE), "open_questions"),
    (re.compile(r"^#+\s*(?:##\s*)?Traceability\s*[:\-]?\s*", re.IGNORECASE), "traceability"),
    # RFC sections
    (re.compile(r"^#+\s*(?:##\s*)?Abstract\s*[:\-]?\s*", re.IGNORECASE), "decision"),
    (re.compile(r"^#+\s*(?:##\s*)?Motivation\s*[:\-]?\s*", re.IGNORECASE), "observation"),
    (re.compile(r"^#+\s*(?:##\s*)?Proposal\s*[:\-]?\s*", re.IGNORECASE), "decision"),
    (re.compile(r"^#+\s*(?:##\s*)?Engineering\s+Principle\s*[:\-]?\s*", re.IGNORECASE), "reasoning"),
    (re.compile(r"^#+\s*(?:##\s*)?Relationship\s*(?:to\s+Existing\s+Concepts)?\s*[:\-]?\s*", re.IGNORECASE), "lineage"),
    # Spec sections
    (re.compile(r"^#+\s*(?:##\s*)?Definition\s*[:\-]?\s*", re.IGNORECASE), "decision"),
    (re.compile(r"^#+\s*(?:##\s*)?Overview\s*[:\-]?\s*", re.IGNORECASE), "observation"),
    (re.compile(r"^#+\s*(?:##\s*)?Scope\s*[:\-]?\s*", re.IGNORECASE), "constraints"),
    (re.compile(r"^#+\s*(?:##\s*)?Known\s+Limitations?\s*[:\-]?\s*", re.IGNORECASE), "assumptions"),
    (re.compile(r"^#+\s*(?:##\s*)?Applicable\s+Laws?\s*[:\-]?\s*", re.IGNORECASE), "constraints"),
    (re.compile(r"^#+\s*(?:##\s*)?Implications?\s*[:\-]?\s*", re.IGNORECASE), "reasoning"),
]


class OEContextParser:
    """Parse Open Engineer markdown files into structured context records.

    The parser extracts OE-0003 context fields from markdown by identifying
    heading-delimited sections.  Each section's content becomes the value
    for the corresponding OE field.

    Parameters
    ----------
    strict :
        If True, only recognized OE-0003 field names are extracted.
        If False, all heading-delimited sections are captured.
    """

    def __init__(self, strict: bool = False) -> None:
        self.strict = strict

    # ── Public API ───────────────────────────────────────────────────

    def parse_file(self, path: str | Path) -> dict[str, Any]:
        """Parse an Open Engineer markdown file and extract context.

        Parameters
        ----------
        path :
            Path to a markdown file.

        Returns
        -------
        dict with keys:
            * ``context`` -- extracted OE-0003 fields (str -> str)
            * ``title`` -- first H1 heading found (or filename stem)
            * ``source_type`` -- detected type: "context_record",
              "rfc", "spec", or "unknown"
            * ``metadata`` -- front-matter or status line info
            * ``raw_sections`` -- all heading -> content pairs found
        """
        p = Path(path)
        if not p.exists():
            return self._empty_result(p)

        text = p.read_text(encoding="utf-8", errors="ignore")
        return self.parse_text(text, source_path=str(p))

    def parse_text(
        self,
        text: str,
        source_path: str = "",
    ) -> dict[str, Any]:
        """Parse markdown text and extract OE context fields.

        Parameters
        ----------
        text :
            The full markdown content.
        source_path :
            Optional path for metadata (used as title fallback).

        Returns
        -------
        Same structure as :meth:`parse_file`.
        """
        sections = self._split_into_sections(text)
        title = self._extract_title(text, source_path)
        source_type = self._detect_source_type(text, sections)
        metadata = self._extract_metadata(text)

        # Map section headings to OE fields
        context: dict[str, str] = {}
        for heading, content in sections:
            field_name = self._heading_to_field(heading)
            if field_name:
                # If the field already has content, append with separator
                existing = context.get(field_name, "")
                if existing:
                    context[field_name] = f"{existing}\n\n---\n\n{content.strip()}"
                else:
                    context[field_name] = content.strip()
            elif not self.strict:
                # In non-strict mode, capture unrecognized sections too
                safe_key = heading.strip().lower().replace(" ", "_")[:60]
                context[f"_section_{safe_key}"] = content.strip()

        return {
            "context": context,
            "title": title,
            "source_type": source_type,
            "metadata": metadata,
            "raw_sections": sections,
        }

    # ── Section splitting ───────────────────────────────────────────

    @staticmethod
    def _split_into_sections(
        text: str,
    ) -> list[tuple[str, str]]:
        """Split markdown into (heading, content) pairs.

        Uses H2 (##) and H3 (###) as section delimiters.  Content
        before the first H2 is captured under a virtual "preamble" heading.
        """
        lines = text.split("\n")
        sections: list[tuple[str, str]] = []
        current_heading = "preamble"
        current_lines: list[str] = []

        for line in lines:
            # Match H2 or H3 headings
            m = re.match(r"^(#{2,3})\s+(.+)$", line.strip())
            if m:
                # Save previous section
                content = "\n".join(current_lines).strip()
                if content or current_heading != "preamble":
                    sections.append((current_heading, content))
                current_heading = m.group(2).strip()
                current_lines = []
            else:
                current_lines.append(line)

        # Don't forget the last section
        content = "\n".join(current_lines).strip()
        if content:
            sections.append((current_heading, content))

        return sections

    # ── Heading to OE field mapping ─────────────────────────────────

    def _heading_to_field(self, heading: str) -> str | None:
        """Map a section heading to a canonical OE field name."""
        # Try regex patterns first (most specific)
        for pattern, field_name in _HEADING_PATTERNS:
            if pattern.match(heading):
                return field_name

        # Fallback: normalize and look up in aliases
        normalized = heading.strip().lower().rstrip(":").rstrip("-").strip()
        return _FIELD_ALIASES.get(normalized)

    # ── Title extraction ────────────────────────────────────────────

    @staticmethod
    def _extract_title(text: str, source_path: str = "") -> str:
        """Extract the title from the first H1 heading."""
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if m:
            # Strip common suffixes like status badges
            title = m.group(1).strip()
            title = re.sub(r"\*\*Status:.*?\*\*", "", title).strip()
            title = re.sub(r"\*\*Version:.*?\*\*", "", title).strip()
            title = re.sub(r"\*\*Phase:.*?\*\*", "", title).strip()
            return title
        if source_path:
            return Path(source_path).stem
        return "Untitled"

    # ── Source type detection ───────────────────────────────────────

    @staticmethod
    def _detect_source_type(
        text: str,
        sections: list[tuple[str, str]],
    ) -> str:
        """Detect whether the file is a context record, RFC, or spec."""
        lower = text[:2000].lower()

        # RFC pattern
        if re.search(r"^# RFC-\d+", text, re.MULTILINE):
            return "rfc"
        if "status:** proposed" in lower or "status:** rc" in lower:
            if "abstract" in lower and "engineering principle" in lower:
                return "rfc"

        # Spec document pattern
        if "depends on:" in lower and "oe-" in lower:
            return "spec"

        # Context record: has multiple OE-0003 fields as headings
        oe_field_count = 0
        for heading, _ in sections:
            normalized = heading.strip().lower()
            if normalized in {
                "decision", "observation", "alternatives", "constraints",
                "reasoning", "verification", "lineage", "assumptions",
            }:
                oe_field_count += 1

        if oe_field_count >= 3:
            return "context_record"

        return "unknown"

    # ── Metadata extraction ─────────────────────────────────────────

    @staticmethod
    def _extract_metadata(text: str) -> dict[str, str]:
        """Extract status, version, phase, depends-on from the document header."""
        meta: dict[str, str] = {}
        header = text[:1500]

        for field in ("status", "version", "phase", "depends on"):
            pattern = re.compile(
                rf"\*\*{re.escape(field)}:?\*\*\s*(.+)",
                re.IGNORECASE,
            )
            m = pattern.search(header)
            if m:
                meta[field.lower().replace(" ", "_")] = m.group(1).strip()

        return meta

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _empty_result(path: Path) -> dict[str, Any]:
        return {
            "context": {},
            "title": path.stem if path.exists() else "missing",
            "source_type": "unknown",
            "metadata": {},
            "raw_sections": [],
        }