"""
AI-LSC — Filesystem helpers.

Directory creation, file watching, and tree-traversal utilities used
by both UI and orchestration code.  All path operations use
:mod:`pathlib`.
"""

from __future__ import annotations

from pathlib import Path

from ai_lsc.constants import BASE_DIR, REQUIRED_DIRS, TREE_SKIP_PATTERNS


def ensure_base_dirs(base_dir: str | Path | None = None) -> list[Path]:
    """Create all required sub-directories under *base_dir*.

    Returns the list of created (or already-existing) directories.
    """
    root = Path(base_dir) if base_dir is not None else Path(BASE_DIR)
    created: list[Path] = []
    for rel in REQUIRED_DIRS:
        p = root / rel
        p.mkdir(parents=True, exist_ok=True)
        created.append(p)
    return created


def walk_tree(
    root: str | Path,
    skip_patterns: set[str] | None = None,
    max_depth: int = 4,
) -> list[Path]:
    """Recursively collect files, honouring *skip_patterns* and *max_depth*.

    Only files (not directories) are returned.  The default skip set
    matches ``TREE_SKIP_PATTERNS``.

    M-36: uses ``Path.rglob`` instead of an explicit recursive helper so
    we don't accumulate stack frames and the traversal stays within a
    single function.
    """
    root = Path(root)
    skip = skip_patterns or TREE_SKIP_PATTERNS
    results: list[Path] = []
    for entry in root.rglob("*"):
        # Enforce max_depth by comparing path depth relative to root.
        try:
            rel_depth = len(entry.relative_to(root).parts)
        except ValueError:
            continue
        if rel_depth > max_depth:
            continue
        if any(part in skip for part in entry.parts):
            continue
        if entry.is_file():
            results.append(entry)
    return results
