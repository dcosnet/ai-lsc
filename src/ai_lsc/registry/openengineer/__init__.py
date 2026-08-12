"""AI-LSC -- OpenEngineer integration sub-package.

Bridges the Open Engineer standard (https://git.dcos.net/dcosnet/openengineer)
with AI-LSC's stack template system.  Open Engineer defines a methodology for
preserving engineering context -- the reasoning, observations, decisions, and
constraints that shape engineering work.  This package imports Open Engineer
context records and project files as AI-LSC stack templates, creating a
standard template format that unifies both systems.

Key concepts
-----------
* **OE Context Record** -- The 9-field structured record defined in OE-0003
  (Decision, Observation, Alternatives, Constraints, Reasoning, Verification,
  Lineage, Assumptions, plus optional fields).  This is the unit of
  preservation in Open Engineer.

* **Standard Template** -- The merged AI-LSC / Open Engineer template format
  that carries both OE engineering context and AI-LSC stack configuration
  (tools, layers, endpoints, deployment targets).

* **Import Pipeline** -- Read an Open Engineer file (markdown context record,
  RFC, example, or project manifest) and produce a Standard Template that
  AI-LSC's StackTemplateManager can consume.

Modules
-------
* ``schema``     -- Standard template schema definition and constants
* ``parser``     -- OE markdown context record parser
* ``importer``  -- Import pipeline (OE file -> Standard Template)
* ``templates``  -- Built-in OE-derived stack templates
"""

from ai_lsc.registry.openengineer.schema import (
    OE_CONTEXT_FIELDS,
    OE_REQUIRED_FIELDS,
    OE_SUPPLEMENTARY_FIELDS,
    OE_CONFORMANCE_CRITERIA,
    StandardTemplate,
    standard_template_to_ai_lsc,
)
from ai_lsc.registry.openengineer.parser import OEContextParser
from ai_lsc.registry.openengineer.importer import OpenEngineerImporter

__all__ = [
    # Schema
    "OE_CONTEXT_FIELDS",
    "OE_REQUIRED_FIELDS",
    "OE_SUPPLEMENTARY_FIELDS",
    "OE_CONFORMANCE_CRITERIA",
    "StandardTemplate",
    "standard_template_to_ai_lsc",
    # Parser
    "OEContextParser",
    # Importer
    "OpenEngineerImporter",
]