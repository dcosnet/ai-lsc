"""AI-LSC — License catalog + acceptance gate.

Defines the three license categories the AI-LSC license gate recognizes:

1. **OSI-approved open source** (``Category.OSI``) — licenses that pass
   the Open Source Initiative's approval criteria.  These CAN be
   auto-approved by the user via the license-approvals registry.
   Examples: MIT, Apache-2.0, GPL-3.0, AGPL-3.0, BSD-3-Clause, MPL-2.0.

2. **Source-available / fair-code** (``Category.SOURCE_AVAILABLE``) —
   licenses that publish source but impose additional restrictions
   (field-of-use limits, commercial-use cliffs, managed-service
   restrictions).  These CANNOT be auto-approved; the user must accept
   each tool individually.  Examples: BSL-1.1, SSPL, RSALv2,
   Sustainable Use License, Dify Open Source License.

3. **Proprietary / ToS-governed** (``Category.PROPRIETARY``) —
   closed-source tools whose use is governed by a vendor Terms-of-
   Service agreement.  These CANNOT be auto-approved and always show
   a prominent disclaimer warning about ToS restrictions before
   install.  Example: Claude Code (Anthropic ToS).

The license-approvals registry (``config/license_approvals.json``) is
a user-editable list of SPDX IDs that have been pre-approved.  Only
OSI-approved licenses can appear in this list — the
:func:`LicenseGate.add_auto_approval` method rejects attempts to
auto-approve source-available or proprietary licenses.

The license-acceptances registry (``config/license_acceptances.json``)
is auto-managed by the gate and records every per-tool acceptance the
user has made (so they aren't prompted twice for the same tool).
"""

from __future__ import annotations

import enum
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class Category(enum.Enum):
    """License category — drives the gate's acceptance flow."""

    OSI = "osi"
    SOURCE_AVAILABLE = "source_available"
    PROPRIETARY = "proprietary"

    @property
    def can_auto_approve(self) -> bool:
        """True if the user is allowed to add this license to the
        auto-approval registry."""
        return self is Category.OSI

    @property
    def needs_disclaimer(self) -> bool:
        """True if the acceptance dialog should show a prominent
        ToS/disclaimer warning."""
        return self in (Category.SOURCE_AVAILABLE, Category.PROPRIETARY)


@dataclass(frozen=True)
class LicenseInfo:
    """Static information about a single license."""

    spdx: str
    """SPDX identifier (e.g. ``"MIT"``, ``"Apache-2.0"``, ``"Proprietary"``).
    For non-SPDX licenses (Dify OSL, Sustainable Use License), use the
    canonical short name."""

    name: str
    """Human-readable license name (e.g. ``"MIT License"``,
    ``"Apache License 2.0"``)."""

    category: Category
    """Which acceptance-flow category this license belongs to."""

    url: str
    """URL to the full license text (or the vendor's ToS page for
    proprietary licenses)."""

    summary: str
    """One-paragraph summary of what the license permits / restricts.
    Shown in the acceptance dialog above the full text link."""

    disclaimer: str = ""
    """Extra disclaimer shown for source-available / proprietary
    licenses.  Empty for OSI-approved licenses."""


# ── The catalog ───────────────────────────────────────────────────────

CATALOG: dict[str, LicenseInfo] = {
    # ── OSI-approved open source (auto-approvable) ───────────────────
    "MIT": LicenseInfo(
        spdx="MIT",
        name="MIT License",
        category=Category.OSI,
        url="https://opensource.org/licenses/MIT",
        summary=(
            "Permissive license allowing almost any use — commercial, "
            "private, modification, distribution — provided the copyright "
            "notice and license text are included."
        ),
    ),
    "Apache-2.0": LicenseInfo(
        spdx="Apache-2.0",
        name="Apache License 2.0",
        category=Category.OSI,
        url="https://opensource.org/licenses/Apache-2.0",
        summary=(
            "Permissive license allowing commercial use, modification, "
            "and distribution with patent grant.  Requires copyright "
            "notice + license text + notice of changes."
        ),
    ),
    "GPL-2.0": LicenseInfo(
        spdx="GPL-2.0",
        name="GNU General Public License v2.0",
        category=Category.OSI,
        url="https://opensource.org/licenses/GPL-2.0",
        summary=(
            "Copyleft license requiring that derivative works be "
            "distributed under the same GPL-2.0 terms, with source code."
        ),
    ),
    "GPL-3.0": LicenseInfo(
        spdx="GPL-3.0",
        name="GNU General Public License v3.0",
        category=Category.OSI,
        url="https://opensource.org/licenses/GPL-3.0",
        summary=(
            "Copyleft license requiring that derivative works be "
            "distributed under the same GPL-3.0 terms, with source code.  "
            "Includes patent grant + anti-tivoization clauses."
        ),
    ),
    "AGPL-3.0": LicenseInfo(
        spdx="AGPL-3.0",
        name="GNU Affero General Public License v3.0",
        category=Category.OSI,
        url="https://opensource.org/licenses/AGPL-3.0",
        summary=(
            "Copyleft license like GPL-3.0 but with an additional "
            "network-use clause: users interacting with the software "
            "over a network are entitled to the source code."
        ),
    ),
    "LGPL-3.0": LicenseInfo(
        spdx="LGPL-3.0",
        name="GNU Lesser General Public License v3.0",
        category=Category.OSI,
        url="https://opensource.org/licenses/LGPL-3.0",
        summary=(
            "Weak copyleft license allowing linking from proprietary "
            "software, but modifications to the LGPL-licensed code itself "
            "must be shared under LGPL."
        ),
    ),
    "BSD-2-Clause": LicenseInfo(
        spdx="BSD-2-Clause",
        name="BSD 2-Clause License",
        category=Category.OSI,
        url="https://opensource.org/licenses/BSD-2-Clause",
        summary=(
            "Permissive license allowing almost any use provided the "
            "copyright notice and license text are included."
        ),
    ),
    "BSD-3-Clause": LicenseInfo(
        spdx="BSD-3-Clause",
        name="BSD 3-Clause License",
        category=Category.OSI,
        url="https://opensource.org/licenses/BSD-3-Clause",
        summary=(
            "Permissive license like BSD-2-Clause but with an additional "
            "clause prohibiting use of the copyright holder's name for "
            "endorsement."
        ),
    ),
    "MPL-2.0": LicenseInfo(
        spdx="MPL-2.0",
        name="Mozilla Public License 2.0",
        category=Category.OSI,
        url="https://opensource.org/licenses/MPL-2.0",
        summary=(
            "File-level copyleft: modifications to MPL-licensed files "
            "must be shared under MPL, but the rest of the project can "
            "be under any license (including proprietary)."
        ),
    ),
    "ISC": LicenseInfo(
        spdx="ISC",
        name="ISC License",
        category=Category.OSI,
        url="https://opensource.org/licenses/ISC",
        summary=(
            "Permissive license functionally equivalent to MIT/BSD, with "
            "simpler language."
        ),
    ),
    "PostgreSQL": LicenseInfo(
        spdx="PostgreSQL",
        name="PostgreSQL License",
        category=Category.OSI,
        url="https://www.postgresql.org/about/licence/",
        summary=(
            "Permissive BSD-like license specific to PostgreSQL.  Allows "
            "commercial use, modification, and distribution with "
            "copyright notice."
        ),
    ),
    "Python": LicenseInfo(
        spdx="Python",
        name="Python Software Foundation License",
        category=Category.OSI,
        url="https://docs.python.org/3/license.html",
        summary=(
            "Permissive license (PSF) for CPython and the Python "
            "standard library.  OSI-approved, GPL-compatible, allows "
            "commercial use and modification."
        ),
    ),

    # ── Source-available / fair-code (NOT auto-approvable) ───────────
    "BSL-1.1": LicenseInfo(
        spdx="BSL-1.1",
        name="Business Source License 1.1",
        category=Category.SOURCE_AVAILABLE,
        url="https://mariadb.com/bsl11/",
        summary=(
            "Source-available license that restricts production use for "
            "a defined period (typically 4 years) after which it "
            "converts to an open-source license (often Apache-2.0 or "
            "GPL).  Used by HashiCorp Terraform, CockroachDB, etc."
        ),
        disclaimer=(
            "This license is NOT OSI-approved.  It imposes "
            "field-of-use restrictions (you may not use the software to "
            "offer a competing managed service).  Review the full text "
            "before accepting."
        ),
    ),
    "SSPL": LicenseInfo(
        spdx="SSPL",
        name="Server Side Public License",
        category=Category.SOURCE_AVAILABLE,
        url="https://www.mongodb.com/licensing/server-side-public-license",
        summary=(
            "Source-available license requiring that if you offer the "
            "software as a managed service, you must open-source your "
            "ENTIRE service stack (including all supporting "
            "infrastructure code).  Used by MongoDB."
        ),
        disclaimer=(
            "This license is NOT OSI-approved.  It has an aggressive "
            "copyleft reach that extends to your entire service stack "
            "if you offer the software as a managed service.  Review "
            "carefully before accepting."
        ),
    ),
    "RSALv2": LicenseInfo(
        spdx="RSALv2",
        name="Redis Source Available License 2.0",
        category=Category.SOURCE_AVAILABLE,
        url="https://redis.com/legal/rsalv2-agreement/",
        summary=(
            "Source-available license prohibiting offering the software "
            "as a managed service, cloud service, or database service "
            "to third parties.  Used by Redis (post-7.4)."
        ),
        disclaimer=(
            "This license is NOT OSI-approved.  It prohibits offering "
            "the software as a managed/cloud/database service.  Review "
            "the full text before accepting."
        ),
    ),
    "Sustainable-Use": LicenseInfo(
        spdx="Sustainable-Use",
        name="Sustainable Use License (n8n fair-code)",
        category=Category.SOURCE_AVAILABLE,
        url="https://github.com/n8n-io/n8n/blob/master/LICENSE.md",
        summary=(
            "Fair-code license allowing internal and commercial use, "
            "but prohibiting offering the software as a hosted service "
            "to third parties.  Used by n8n."
        ),
        disclaimer=(
            "This license is NOT OSI-approved.  It prohibits offering "
            "the software as a hosted service to third parties.  "
            "Review the full text before accepting."
        ),
    ),
    "Dify-OSL": LicenseInfo(
        spdx="Dify-OSL",
        name="Dify Open Source License",
        category=Category.SOURCE_AVAILABLE,
        url="https://github.com/langgenius/dify/blob/main/LICENSE",
        summary=(
            "Custom fair-code license allowing non-production and "
            "internal commercial use, but restricting offering Dify as "
            "a multi-tenant SaaS.  Used by Dify."
        ),
        disclaimer=(
            "This license is NOT OSI-approved.  It restricts offering "
            "the software as a multi-tenant SaaS.  Review the full text "
            "before accepting."
        ),
    ),

    # ── Proprietary / ToS-governed (always needs individual acceptance) ──
    "Proprietary": LicenseInfo(
        spdx="Proprietary",
        name="Proprietary License",
        category=Category.PROPRIETARY,
        url="",
        summary=(
            "Closed-source software governed by the vendor's Terms of "
            "Service.  Use is permitted only as expressly allowed by "
            "the vendor's ToS."
        ),
        disclaimer=(
            "WARNING: This tool is proprietary and governed by the "
            "vendor's Terms of Service.  AI-LSC forces localhost-only "
            "endpoints where possible, but you are responsible for "
            "reviewing and complying with the vendor's ToS.  Do NOT "
            "install if you do not agree to the vendor's ToS."
        ),
    ),
    "Anthropic-ToS": LicenseInfo(
        spdx="Anthropic-ToS",
        name="Anthropic Terms of Service",
        category=Category.PROPRIETARY,
        url="https://www.anthropic.com/legal/terms",
        summary=(
            "Anthropic's Terms of Service govern use of Claude Code "
            "and other Anthropic products.  Closed-source, "
            "ToS-restricted."
        ),
        disclaimer=(
            "WARNING: Claude Code is proprietary software governed by "
            "Anthropic's Terms of Service.  AI-LSC forces "
            "ANTHROPIC_BASE_URL to a localhost LiteLLM proxy by "
            "default, but if you override this to call api.anthropic.com "
            "directly, you are bound by Anthropic's ToS.  Review at "
            "anthropic.com/legal/terms before accepting."
        ),
    ),
    "LMStudio-ToS": LicenseInfo(
        spdx="LMStudio-ToS",
        name="LM Studio Terms of Service (BLOCKED)",
        category=Category.PROPRIETARY,
        url="https://lmstudio.ai/terms",
        summary=(
            "LM Studio's Terms of Service are considered too "
            "restrictive for AI-LSC's SaaS-only policy — the tool is "
            "on the blocklist and CANNOT be installed."
        ),
        disclaimer=(
            "BLOCKED: LM Studio is on the AI-LSC SaaS-only blocklist "
            "due to aggressive Terms-of-Service restrictions.  This "
            "tool cannot be installed through AI-LSC.  Use Ollama, "
            "vLLM, or llama.cpp as a local alternative."
        ),
    ),
}


def get_license_info(spdx: str) -> LicenseInfo | None:
    """Look up license info by SPDX ID.  Returns ``None`` if unknown."""
    return CATALOG.get(spdx)


def category_for(spdx: str) -> Category:
    """Return the category for an SPDX ID, defaulting to PROPRIETARY
    for unknown licenses (defensive — unknown = restricted)."""
    info = CATALOG.get(spdx)
    if info is None:
        return Category.PROPRIETARY
    return info.category


def all_licenses() -> dict[str, LicenseInfo]:
    """Return the full catalog (for UI enumeration)."""
    return dict(CATALOG)


def osi_approved_spdx_ids() -> list[str]:
    """Return SPDX IDs that are OSI-approved (auto-approvable)."""
    return sorted(
        spdx for spdx, info in CATALOG.items()
        if info.category is Category.OSI
    )


__all__ = [
    "Category",
    "LicenseInfo",
    "CATALOG",
    "get_license_info",
    "category_for",
    "all_licenses",
    "osi_approved_spdx_ids",
]
