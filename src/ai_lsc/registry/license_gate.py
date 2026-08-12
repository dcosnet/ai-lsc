"""AI-LSC — License acceptance gate.

Sits between the user's "Install" click and the actual installer
strategy dispatch.  For every tool installation, the gate checks the
tool's ``license`` SPDX ID against three sources:

1. **SaaS blocklist** (in :mod:`ai_lsc.registry.validator`) — if the
   tool_id is blocked, raise :class:`LicenseBlocked` immediately.  No
   dialog, no acceptance, no install.

2. **Auto-approval registry** (``config/license_approvals.json``) — a
   user-editable list of OSI-approved SPDX IDs that have been
   pre-approved.  If the tool's license is in this list, install
   proceeds without a dialog.  Only OSI-approved licenses can appear
   here; :meth:`LicenseGate.add_auto_approval` rejects attempts to
   auto-approve source-available or proprietary licenses.

3. **Per-tool acceptance registry** (``config/license_acceptances.json``)
   — auto-managed by the gate; records every per-tool acceptance the
   user has made so they aren't prompted twice for the same tool.

If none of the three sources cover the tool, the gate raises
:class:`LicenseAcceptanceRequired` (carrying the license info).  The
UI catches this exception and shows the
:class:`~ai_lsc.ui.dialogs.license_dialog.LicenseAcceptanceDialog`.
On dialog accept, the UI calls :meth:`LicenseGate.accept` and retries
the install.

Files managed
-------------
* ``config/license_approvals.json`` — ``{"licenses": ["MIT", "Apache-2.0"], "updated_at": "..."}``
* ``config/license_acceptances.json`` — ``{"ollama": {"spdx": "MIT", "accepted_at": "...", "via": "auto-approved"}, ...}``
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_lsc.registry.licenses import (
    CATALOG,
    Category,
    LicenseInfo,
    category_for,
    get_license_info,
)
from ai_lsc.registry.validator import SAAS_BLOCKLIST
from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)


# ── Exceptions ────────────────────────────────────────────────────────


class LicenseError(Exception):
    """Base class for license-gate failures."""


@dataclass
class LicenseBlocked(LicenseError):
    """Raised when the tool_id is on the SaaS blocklist."""

    tool_id: str
    reason: str = ""

    def __str__(self) -> str:
        return (
            f"Tool {self.tool_id!r} is blocked — {self.reason or 'on SaaS-only blocklist'}"
        )


@dataclass
class LicenseAcceptanceRequired(LicenseError):
    """Raised when the tool's license has not been accepted yet.

    The UI catches this and shows the
    :class:`~ai_lsc.ui.dialogs.license_dialog.LicenseAcceptanceDialog`.
    """

    tool_id: str
    license_info: LicenseInfo

    def __str__(self) -> str:
        return (
            f"Tool {self.tool_id!r} requires license acceptance: "
            f"{self.license_info.name} ({self.license_info.spdx})"
        )


# ── Result enum ───────────────────────────────────────────────────────


@dataclass
class GateResult:
    """Outcome of a license-gate check."""

    status: str  # "accepted" | "auto_approved" | "needs_acceptance" | "blocked"
    tool_id: str
    spdx: str = ""
    license_info: LicenseInfo | None = None
    reason: str = ""

    @property
    def can_install(self) -> bool:
        return self.status in ("accepted", "auto_approved")


# ── The gate ──────────────────────────────────────────────────────────


class LicenseGate:
    """License acceptance gate.

    Parameters
    ----------
    config_dir :
        Directory where ``license_approvals.json`` and
        ``license_acceptances.json`` live.  Defaults to the AI-LSC
        ``config/`` directory under ``BASE_DIR``.
    """

    APPROVALS_FILE = "license_approvals.json"
    ACCEPTANCES_FILE = "license_acceptances.json"

    def __init__(self, config_dir: str | Path | None = None) -> None:
        if config_dir is None:
            from ai_lsc.constants import BASE_DIR
            config_dir = os.path.join(BASE_DIR, "config")
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._approvals_path = self.config_dir / self.APPROVALS_FILE
        self._acceptances_path = self.config_dir / self.ACCEPTANCES_FILE

    # ── Public API ───────────────────────────────────────────────────

    def check(self, tool_id: str, spdx: str) -> GateResult:
        """Check whether the tool can be installed under its license.

        Returns a :class:`GateResult`.  The caller should:

        * if ``result.can_install`` → proceed with the install.
        * if ``result.status == "blocked"`` → log + abort; do NOT
          retry.
        * if ``result.status == "needs_acceptance"`` → raise
          :class:`LicenseAcceptanceRequired` (or catch + show dialog).
        """
        # 1. SaaS blocklist — hard block, no acceptance possible.
        if tool_id.lower() in SAAS_BLOCKLIST:
            return GateResult(
                status="blocked",
                tool_id=tool_id,
                spdx=spdx,
                license_info=get_license_info(spdx),
                reason=(
                    f"tool_id {tool_id!r} is on the SaaS-only blocklist"
                ),
            )

        # 2. Look up the license info.  Unknown SPDX → treat as
        # PROPRIETARY (defensive — unknown = restricted).
        info = get_license_info(spdx)
        if info is None:
            info = CATALOG["Proprietary"]
            logger.warning(
                "Tool %r has unknown license SPDX %r — treating as "
                "Proprietary (defensive).  Add the SPDX to "
                "registry/licenses.py to fix.",
                tool_id, spdx,
            )

        # 3. Auto-approval registry — only OSI licenses can be here,
        # but double-check in case the file was hand-edited.
        if spdx in self._load_approvals():
            if info.category is Category.OSI:
                return GateResult(
                    status="auto_approved",
                    tool_id=tool_id,
                    spdx=spdx,
                    license_info=info,
                    reason=f"auto-approved via {spdx}",
                )
            # Non-OSI license in the approvals file — ignore it +
            # log a warning so the user can fix the file.
            logger.warning(
                "License %r is in the auto-approvals registry but is "
                "not OSI-approved (category=%s).  Ignoring — this "
                "license requires individual acceptance.",
                spdx, info.category.value,
            )

        # 4. Per-tool acceptance registry.
        acceptances = self._load_acceptances()
        record = acceptances.get(tool_id)
        if record and record.get("spdx") == spdx:
            return GateResult(
                status="accepted",
                tool_id=tool_id,
                spdx=spdx,
                license_info=info,
                reason=f"accepted via {record.get('via', 'individual')} at {record.get('accepted_at', '?')}",
            )

        # 5. Needs acceptance — caller raises LicenseAcceptanceRequired.
        return GateResult(
            status="needs_acceptance",
            tool_id=tool_id,
            spdx=spdx,
            license_info=info,
        )

    def accept(
        self,
        tool_id: str,
        spdx: str,
        *,
        via: str = "individual",
    ) -> None:
        """Record that the user has accepted the tool's license.

        Parameters
        ----------
        tool_id :
            The tool whose license was accepted.
        spdx :
            The SPDX ID that was accepted (recorded so a license
            change later re-prompts).
        via :
            How the acceptance happened — ``"individual"`` (dialog),
            ``"auto-approved"`` (was in the approvals registry at
            check time but we're recording it for audit), or
            ``"cli"`` (accepted via a non-UI code path).
        """
        acceptances = self._load_acceptances()
        acceptances[tool_id] = {
            "spdx": spdx,
            "accepted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "via": via,
        }
        self._save_acceptances(acceptances)
        logger.info(
            "License %r accepted for tool %r (via %s)",
            spdx, tool_id, via,
        )

    def add_auto_approval(self, spdx: str) -> None:
        """Add an SPDX ID to the auto-approval registry.

        Raises :class:`ValueError` if the license is not OSI-approved
        (source-available and proprietary licenses cannot be
        auto-approved — the user must accept each tool individually).
        """
        info = get_license_info(spdx)
        if info is None:
            raise ValueError(
                f"Unknown license SPDX {spdx!r} — not in the catalog.  "
                f"Add it to registry/licenses.py first."
            )
        if info.category is not Category.OSI:
            raise ValueError(
                f"License {spdx!r} ({info.name}) is {info.category.value} "
                f"— only OSI-approved open-source licenses can be "
                f"auto-approved.  Source-available and proprietary "
                f"licenses require per-tool acceptance."
            )
        approvals = self._load_approvals()
        if spdx not in approvals:
            approvals.append(spdx)
            self._save_approvals(approvals)
            logger.info("License %r added to auto-approvals registry", spdx)

    def remove_auto_approval(self, spdx: str) -> None:
        """Remove an SPDX ID from the auto-approval registry."""
        approvals = self._load_approvals()
        if spdx in approvals:
            approvals.remove(spdx)
            self._save_approvals(approvals)
            logger.info("License %r removed from auto-approvals registry", spdx)

    def revoke_acceptance(self, tool_id: str) -> None:
        """Revoke a per-tool acceptance (the user will be re-prompted
        on next install)."""
        acceptances = self._load_acceptances()
        if tool_id in acceptances:
            del acceptances[tool_id]
            self._save_acceptances(acceptances)
            logger.info("License acceptance revoked for tool %r", tool_id)

    def list_auto_approvals(self) -> list[str]:
        """Return the current list of auto-approved SPDX IDs."""
        return list(self._load_approvals())

    def list_acceptances(self) -> dict[str, dict[str, Any]]:
        """Return the current per-tool acceptance registry."""
        return dict(self._load_acceptances())

    # ── Internal: file I/O ──────────────────────────────────────────

    def _load_approvals(self) -> list[str]:
        if not self._approvals_path.exists():
            return []
        try:
            data = json.loads(self._approvals_path.read_text(encoding="utf-8"))
            licenses = data.get("licenses", [])
            if isinstance(licenses, list):
                return [str(x) for x in licenses]
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load %s: %s", self._approvals_path, exc)
        return []

    def _save_approvals(self, licenses: list[str]) -> None:
        data = {
            "licenses": list(licenses),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "_comment": (
                "Auto-approved SPDX IDs.  Only OSI-approved open-source "
                "licenses can appear here — source-available and "
                "proprietary licenses require per-tool acceptance.  "
                "Edit manually or via the LicenseAcceptanceDialog."
            ),
        }
        self._approvals_path.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _load_acceptances(self) -> dict[str, dict[str, Any]]:
        if not self._acceptances_path.exists():
            return {}
        try:
            data = json.loads(self._acceptances_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # Accept both {tool_id: {...}} and {"acceptances": {...}}
                if "acceptances" in data and isinstance(data["acceptances"], dict):
                    return data["acceptances"]
                return data
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load %s: %s", self._acceptances_path, exc)
        return {}

    def _save_acceptances(self, acceptances: dict[str, dict[str, Any]]) -> None:
        data = {
            "acceptances": acceptances,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "_comment": (
                "Per-tool license acceptance registry.  Auto-managed "
                "by LicenseGate.accept().  Each entry records the SPDX "
                "ID accepted, the timestamp, and how the acceptance "
                "happened (individual / auto-approved / cli)."
            ),
        }
        self._acceptances_path.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


__all__ = [
    "LicenseGate",
    "LicenseError",
    "LicenseBlocked",
    "LicenseAcceptanceRequired",
    "GateResult",
]
