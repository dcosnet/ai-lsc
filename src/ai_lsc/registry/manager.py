"""
AI-LSC — Registry manager.

Load / merge / query the on-disk ecosystem registry.  The canonical source
of truth is the per-layer modules in ``ai_lsc.registry.layers`` (discovered
automatically by :mod:`ai_lsc.registry.loader`).  On first run the merged
registry is written to ``<base_dir>/registry/ecosystem.json``; on subsequent
runs structural fields (layer, level, role, category) are synced from the
layer files while user customisations (description, installer tweaks,
flags, filesystem paths) are preserved.

All path operations use ``pathlib.Path`` instead of ``os.path``.
"""

from __future__ import annotations

import json
from itertools import chain
from pathlib import Path
from typing import Any

import logging

from ai_lsc.registry.loader import load_merged_registry

logger = logging.getLogger(__name__)


class RegistryManager:
    """Knowledge-graph engine backed by a JSON file on disk.

    Parameters
    ----------
    registry_dir:
        Absolute path to the directory containing ``ecosystem.json``.
    """

    def __init__(self, registry_dir: str | Path) -> None:
        self.registry_dir = Path(registry_dir)
        self.registry_file: Path = self.registry_dir / "ecosystem.json"
        self.data: dict[str, dict[str, Any]] = {}
        self._bootstrap()

    # ── Bootstrap / merge ────────────────────────────────────────────

    def _bootstrap(self) -> None:
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        # Always load the canonical registry from per-layer files.
        upstream = load_merged_registry()

        if not self.registry_file.exists():
            # First run — seed ecosystem.json from layer files.
            self.data = dict(upstream)
            self.registry_file.write_text(
                json.dumps(self.data, indent=4), encoding="utf-8"
            )
        else:
            try:
                self.data = json.loads(
                    self.registry_file.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError) as exc:
                logger.error(
                    "Failed to parse %s: %s -- re-creating from layer files",
                    self.registry_file, exc,
                )
                self.data = dict(upstream)
                self.registry_file.write_text(
                    json.dumps(self.data, indent=4), encoding="utf-8",
                )

        # Sync: merge new tools, update structural fields from upstream.
        self._sync_with_upstream(upstream)

    def _sync_with_upstream(
        self, upstream: dict[str, dict[str, Any]]
    ) -> None:
        """Merge upstream (per-layer files) into the on-disk registry.

        * New tools (not in ecosystem.json) are added wholesale.
        * Existing tools get their structural fields (layer, level, role,
          category, name, installer, launcher, deps, flags, license)
          updated from upstream so the topology stays consistent.
        * User-added keys that don't exist upstream are preserved.
        """
        changed = False
        structural_keys = {
            "name", "level", "layer", "role", "category",
            "installer", "launcher", "deps", "flags", "license",
            "description",
        }

        for tool_id, up_meta in upstream.items():
            if tool_id not in self.data:
                # Brand-new tool — add it.
                self.data[tool_id] = up_meta
                changed = True
            else:
                # Existing tool — sync structural fields from upstream.
                existing = self.data[tool_id]
                for key in structural_keys:
                    up_val = up_meta.get(key)
                    if up_val is not None and existing.get(key) != up_val:
                        existing[key] = up_val
                        changed = True
                # Inject tool_id if missing.
                if "tool_id" not in existing:
                    existing["tool_id"] = tool_id
                    changed = True

        if changed:
            self.registry_file.write_text(
                json.dumps(self.data, indent=4), encoding="utf-8"
            )

    # ── Queries ──────────────────────────────────────────────────────

    def get_all_tools(self) -> dict[str, dict[str, Any]]:
        """Return the full registry dict."""
        return self.data

    def get_tool(self, tool_id: str) -> dict[str, Any]:
        """Return a single tool's raw dict, or ``{}`` if unknown."""
        return self.data.get(tool_id, {})

    def get_grouped_by_layer(self) -> dict[str, list[tuple[str, dict]]]:
        """Return tools grouped and sorted by their ``layer`` field."""
        layers: dict[str, list[tuple[str, dict]]] = {}
        for t_id, meta in self.data.items():
            layers.setdefault(
                meta.get("layer", "Uncategorized"), []
            ).append((t_id, meta))
        return dict(sorted(layers.items()))

    # Host-level prerequisites referenced in deps but not managed as
    # registry tools (mirrors _system_deps in stack/connections.py).
    SYSTEM_DEPS: frozenset[str] = frozenset({"kubectl", "java"})

    def check_dependencies(
        self, selected: list[str],
    ) -> list[str]:
        """Return tool IDs that are required but missing from *selected*."""
        all_deps = list(chain.from_iterable(
            self.get_tool(t).get("deps", [])
            for t in selected
            if not t.startswith("skill:")
        ))
        return list({
            d for d in all_deps
            if d not in selected and d not in self.SYSTEM_DEPS
        })