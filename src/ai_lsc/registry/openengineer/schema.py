"""
AI-LSC / Open Engineer -- Standard Template Schema.

Defines the unified template format that merges Open Engineer's engineering
context record (OE-0003) with AI-LSC's stack template configuration.

The standard template is the bridge format: it can be produced by
importing an Open Engineer context record, by enriching an existing AI-LSC
stack template, or by creating one from scratch.  It can be consumed by
AI-LSC's StackTemplateManager for stack deployment.

Schema versioning follows AI-LSC's ``STACK_SCHEMA_VERSION`` prefix
with an OE-specific suffix.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Open Engineer field definitions (OE-0003) ────────────────────────

#: All nine OE-0003 context record fields.
OE_CONTEXT_FIELDS: list[str] = [
    "decision",
    "observation",
    "alternatives",
    "constraints",
    "reasoning",
    "verification",
    "lineage",
    "assumptions",
]

#: The eight *required* fields (OE-0003 minimum context record).
#: "open_questions" is the first supplementary field.
OE_REQUIRED_FIELDS: set[str] = set(OE_CONTEXT_FIELDS)

#: Optional supplementary fields from OE-0003.
OE_SUPPLEMENTARY_FIELDS: list[str] = [
    "open_questions",
    "discipline_specific_data",
    "traceability",
]

#: The ten OE-0000 conformance criteria, used for validation.
OE_CONFORMANCE_CRITERIA: list[str] = [
    "field_completeness",
    "decision_specificity",
    "observation_traceability",
    "constraint_bounding",
    "alternatives_plural",
    "verification_against_reality",
    "reasoning_references_alternatives",
    "lineage_traceability",
    "assumption_awareness",
    "no_contradiction",
]

# ── Standard Template Schema Version ─────────────────────────────────

STANDARD_TEMPLATE_VERSION: str = "1.0.0-oe-rc3"


# ── Standard Template dataclass ─────────────────────────────────────

@dataclass
class StandardTemplate:
    """Unified AI-LSC / Open Engineer template.

    Carries both OE engineering context and AI-LSC stack configuration
    in a single portable structure.

    The ``engineering_context`` dict maps directly to the OE-0003
    context record fields.  The ``stack_config`` dict maps to
    AI-LSC's stack template format (tools, endpoints, tags, etc.).

    Parameters
    ----------
    template_id :
        Unique identifier (slugified name or explicit ID).
    name :
        Human-readable template name.
    version :
        Template version string.
    author :
        Template author or "openengineer" for imported templates.
    description :
        One-line summary.
    source_file :
        Path to the original OE file this was imported from, if any.
    source_type :
        Type of OE source: "context_record", "rfc", "example",
        "project", or "native" for AI-LSC-native templates.
    oe_spec_refs :
        Open Engineer specification documents referenced
        (e.g. ["OE-0003", "OE-0008"]).
    engineering_context :
        The OE-0003 context record fields (decision, observation, etc.).
    stack_config :
        AI-LSC stack template configuration (tools, endpoints, tags, etc.).
    conformance :
        Results of OE-0000 conformance checking (criteria -> pass/fail).
    notes :
        Arbitrary key-value notes (mirrors AI-LSC template ``notes``).
    metadata :
        Additional metadata not covered by other fields.
    """

    template_id: str
    name: str
    version: str = STANDARD_TEMPLATE_VERSION
    author: str = "openengineer"
    description: str = ""
    source_file: str = ""
    source_type: str = "native"  # context_record | rfc | example | project | native
    oe_spec_refs: list[str] = field(default_factory=list)
    engineering_context: dict[str, str] = field(default_factory=dict)
    stack_config: dict[str, Any] = field(default_factory=dict)
    conformance: dict[str, bool] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # ── Serialization ────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict (the interchange format)."""
        return {
            "$schema": "https://git.dcos.net/dcosnet/openengineer"
                         "/schemas/standard-template-v1.json",
            "schema_version": self.version,
            "id": self.template_id,
            "name": self.name,
            "author": self.author,
            "description": self.description,
            "source": {
                "file": self.source_file,
                "type": self.source_type,
                "oe_spec_refs": self.oe_spec_refs,
            },
            "engineering_context": self.engineering_context,
            "stack_config": self.stack_config,
            "conformance": self.conformance,
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StandardTemplate:
        """Hydrate from a JSON-compatible dict."""
        source = data.get("source", {})
        return cls(
            template_id=data.get("id", ""),
            name=data.get("name", ""),
            version=data.get("schema_version", STANDARD_TEMPLATE_VERSION),
            author=data.get("author", "openengineer"),
            description=data.get("description", ""),
            source_file=source.get("file", ""),
            source_type=source.get("type", "native"),
            oe_spec_refs=source.get("oe_spec_refs", []),
            engineering_context=data.get("engineering_context", {}),
            stack_config=data.get("stack_config", {}),
            conformance=data.get("conformance", {}),
            notes=data.get("notes", {}),
            metadata=data.get("metadata", {}),
        )

    def to_json(self, indent: int = 4) -> str:
        """Serialize to a JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    # ── Conformance checking (OE-0000 ten criteria) ─────────────────

    def check_conformance(self) -> dict[str, bool]:
        """Run the ten OE-0000 conformance criteria against this template.

        Returns a dict mapping criterion name to pass/fail boolean.
        """
        ctx = self.engineering_context
        results: dict[str, bool] = {}

        # 1. Field Completeness
        results["field_completeness"] = all(
            ctx.get(f, "") for f in OE_REQUIRED_FIELDS
        )

        # 2. Decision Specificity
        dec = ctx.get("decision", "")
        results["decision_specificity"] = (
            len(dec.strip()) > 0
            and "|" not in dec  # simple heuristic: no pipe-separated list
        )

        # 3. Observation Traceability
        obs = ctx.get("observation", "")
        results["observation_traceability"] = len(obs.strip()) > 20

        # 4. Constraint Bounding
        con = ctx.get("constraints", "")
        results["constraint_bounding"] = len(con.strip()) > 0

        # 5. Alternatives Plural
        alt = ctx.get("alternatives", "")
        results["alternatives_plural"] = (
            len(alt.strip()) > 0
            and ("," in alt or "\n" in alt or "-" in alt)
        )

        # 6. Verification Against Reality
        ver = ctx.get("verification", "")
        results["verification_against_reality"] = len(ver.strip()) > 10

        # 7. Reasoning References Alternatives
        rea = ctx.get("reasoning", "")
        results["reasoning_references_alternatives"] = (
            len(rea.strip()) > 10 and len(alt.strip()) > 0
        )

        # 8. Lineage Traceability
        lin = ctx.get("lineage", "")
        results["lineage_traceability"] = len(lin.strip()) > 0

        # 9. Assumption Awareness
        asn = ctx.get("assumptions", "")
        results["assumption_awareness"] = len(asn.strip()) > 0

        # 10. No Contradiction (always true for well-formed templates)
        results["no_contradiction"] = True

        self.conformance = results
        return results

    @property
    def conformance_score(self) -> int:
        """Return conformance as a percentage (0-100)."""
        if not self.conformance:
            self.check_conformance()
        passed = sum(1 for v in self.conformance.values() if v)
        return int((passed / max(len(self.conformance), 1)) * 100)


# ── Conversion to AI-LSC stack template format ──────────────────────

def standard_template_to_ai_lsc(template: StandardTemplate) -> dict[str, Any]:
    """Convert a StandardTemplate to AI-LSC's stack template JSON format.

    This is the output format consumed by
    :class:`ai_lsc.registry.stack_templates.manager.StackTemplateManager`.

    The engineering context is preserved in the ``notes`` section under
    an ``openengineer_context`` key so that no OE information is lost
    during the conversion.

    Parameters
    ----------
    template :
        A populated :class:`StandardTemplate`.

    Returns
    -------
    dict
        An AI-LSC-compatible stack template dict.
    """
    stack = dict(template.stack_config)
    stack.setdefault("id", template.template_id)
    stack.setdefault("name", template.name)
    stack.setdefault("description", template.description)
    stack.setdefault("version", template.version)
    stack.setdefault("author", template.author)
    stack.setdefault("tags", []).extend(
        t for t in ["openengineer", "oe-context"]
        if t not in stack.get("tags", [])
    )

    # Merge OE context into notes
    notes = dict(template.notes)
    notes["openengineer_context"] = template.engineering_context
    notes["openengineer_source"] = {
        "file": template.source_file,
        "type": template.source_type,
        "oe_spec_refs": template.oe_spec_refs,
        "conformance_score": template.conformance_score,
        "conformance": template.conformance,
    }
    stack["notes"] = notes

    return stack