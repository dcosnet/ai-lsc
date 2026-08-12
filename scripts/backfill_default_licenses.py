"""Second-pass license backfill: for every tool that STILL doesn't have
a `license` field after backfill_tool_licenses.py ran, inject
`"license": "Proprietary"` (the defensive default — the gate will
require individual acceptance).

After running this, the validator should pass with 0 missing-license
errors.  The user can then review the tools marked "Proprietary" and
update their licenses in defaults.py / layer files if any are actually
open-source.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/home/z/my-project/workspace/ai-lsc")
LAYER_DIR = ROOT / "src/ai_lsc/registry/layers"
DEFAULTS_PATH = ROOT / "src/ai_lsc/registry/defaults.py"

DEFAULT_LICENSE = "Proprietary"

_DESC_RE = re.compile(
    r'(?P<indent>[ \t]+)"description":\s*(?:"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'),?',
    re.DOTALL,
)
_LICENSE_RE = re.compile(
    r'(?P<indent>[ \t]+)"license":\s*(?:"[^"]+"|\'[^\']+\'),?\n',
)


def backfill_text(text: str) -> tuple[str, int, list[str]]:
    """Backfill `license` fields with the default for any tool block
    that doesn't already have one.  Returns (new_text, count, tool_ids_filled).
    """
    updated = 0
    filled_ids = []

    pos = 0
    out = []
    for m in re.finditer(r"'([a-zA-Z0-9_]+)':\s*\{", text):
        tool_id = m.group(1)
        if tool_id in ("TOOLS",):
            continue

        # Find block end via brace-depth counting
        block_start = m.end() - 1
        depth = 0
        i = block_start
        in_string = False
        string_char = None
        block_end = -1
        while i < len(text):
            ch = text[i]
            if in_string:
                if ch == '\\':
                    i += 2
                    continue
                if ch == string_char:
                    in_string = False
                    string_char = None
                i += 1
                continue
            if ch in ('"', "'"):
                in_string = True
                string_char = ch
                i += 1
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    if end < len(text) and text[end] == ',':
                        end += 1
                    block_end = end
                    break
            i += 1
        if block_end == -1:
            continue

        block = text[block_start:block_end]

        # Skip if already has a license field
        if _LICENSE_RE.search(block):
            continue

        # Inject license after description
        desc_match = _DESC_RE.search(block)
        if not desc_match:
            continue

        spdx = DEFAULT_LICENSE
        insert_at = desc_match.end()
        indent = desc_match.group("indent")
        new_block = (
            block[:insert_at]
            + "\n"
            + f'{indent}"license": \'{spdx}\','
            + block[insert_at:]
        )

        out.append(text[pos:m.start()])
        out.append(text[m.start():block_start])
        out.append(new_block)
        pos = block_end
        updated += 1
        filled_ids.append(tool_id)

    out.append(text[pos:])
    return "".join(out), updated, filled_ids


def main() -> int:
    total = 0
    all_filled = []

    for path in [DEFAULTS_PATH, *sorted(LAYER_DIR.glob("*.py"))]:
        if path.name == "__init__.py":
            continue
        original = path.read_text(encoding="utf-8")
        new_text, count, filled = backfill_text(original)
        if count:
            path.write_text(new_text, encoding="utf-8")
            print(f"  {path.name}: {count} tools defaulted to {DEFAULT_LICENSE!r}")
            for tid in filled:
                print(f"    - {tid}")
            total += count
            all_filled.extend(filled)

    print(f"\nDefaulted {total} tool(s) to {DEFAULT_LICENSE!r}.")
    print("Review these and update their licenses if any are actually open-source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
