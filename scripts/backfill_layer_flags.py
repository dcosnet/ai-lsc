"""H-15: backfill missing boolean flag keys in registry layer files.

Every registry entry must declare all 7 flag keys per the ToolFlags
schema.  Layer files that pre-date the schema expansion only declare
the first three (has_cli / has_gui / has_web).  This script appends the
missing four (is_ollama / is_passive / is_mcp /
is_skills_collection) defaulting to ``False`` to every flags block in
every layer file under ``registry/layers/``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

LAYER_DIR = Path(__file__).resolve().parent.parent / "src/ai_lsc/registry/layers"
REQUIRED_KEYS = [
    "has_cli",
    "has_gui",
    "has_web",
    "is_ollama",
    "is_passive",
    "is_mcp",
    "is_skills_collection",
]

# Matches a `"flags": { ... }` block, capturing the inner body.
_FLAGS_RE = re.compile(
    r'("flags":\s*\{)([^}]*)(\})',
    re.DOTALL,
)


def backfill(text: str) -> tuple[str, int]:
    """Return (new_text, number_of_blocks_updated)."""
    updated = 0

    def repl(m: re.Match) -> str:
        nonlocal updated
        head, body, tail = m.group(1), m.group(2), m.group(3)
        present = set(re.findall(r'"([a-z_]+)"\s*:', body))
        missing = [k for k in REQUIRED_KEYS if k not in present]
        if not missing:
            return m.group(0)
        indent_match = re.search(r'\n([ \t]+)"', body)
        indent = indent_match.group(1) if indent_match else "        "
        # Build the new body from scratch.  Strip trailing whitespace
        # and any trailing comma from the existing body so we can append
        # new lines cleanly; if the body is empty (was `{}`), start fresh.
        body_stripped = body.rstrip()
        body_stripped = re.sub(r',\s*$', '', body_stripped)
        new_lines = []
        if body_stripped:
            new_lines.append(body_stripped + ",")
        for i, k in enumerate(missing):
            suffix = "," if i < len(missing) - 1 else ""
            new_lines.append(f'{indent}"{k}": False{suffix}')
        updated += 1
        close_indent = indent[:-4] if len(indent) >= 4 else ""
        return f"{head}" + "\n".join(new_lines) + f"\n{close_indent}{tail}"

    new_text = _FLAGS_RE.sub(repl, text)
    return new_text, updated


def main() -> int:
    if not LAYER_DIR.is_dir():
        print(f"layer dir not found: {LAYER_DIR}", file=sys.stderr)
        return 2
    total_blocks = 0
    total_files = 0
    for path in sorted(LAYER_DIR.glob("*.py")):
        original = path.read_text(encoding="utf-8")
        new_text, blocks = backfill(original)
        if blocks:
            path.write_text(new_text, encoding="utf-8")
            print(f"  {path.name}: updated {blocks} flags block(s)")
            total_blocks += blocks
            total_files += 1
        else:
            print(f"  {path.name}: no changes needed")
    print(f"\nUpdated {total_blocks} flags block(s) across {total_files} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
