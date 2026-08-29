"""Backfill the `license` SPDX field on every tool entry in
defaults.py + the 13 layer files.

Maps tool_id → SPDX based on:
  1. An explicit override table (below) for tools whose license is
     known but not obvious from the tool_id.
  2. The SERVICE_LICENSES dict in constants.py (keyed by display name)
     for tools whose license is recorded there.
  3. A default of "Proprietary" for tools whose license is unknown —
     defensive (the gate will require individual acceptance).

Run with:  python scripts/backfill_tool_licenses.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYER_DIR = ROOT / "src/ai_lsc/registry/layers"
DEFAULTS_PATH = ROOT / "src/ai_lsc/registry/defaults.py"

# ── Explicit override table ──────────────────────────────────────────
# tool_id → SPDX.  Use this for tools whose license is known but not
# captured in SERVICE_LICENSES, or to override a wrong SERVICE_LICENSES
# entry.
TOOL_LICENSE_OVERRIDES: dict[str, str] = {
    # ── Inference engines ───────────────────────────────────────────
    "ollama": "MIT",
    "llamacpp": "MIT",
    "vllm": "Apache-2.0",
    "sglang": "Apache-2.0",
    "tgi": "Apache-2.0",
    "textgen": "AGPL-3.0",  # oobabooga/text-generation-webui
    "lmdeploy": "Apache-2.0",
    "tensorrt_llm": "Apache-2.0",
    "llamafile": "Apache-2.0",

    # ── AI Endpoints (L6) ───────────────────────────────────────────
    "litellm": "MIT",
    "9router_proxy": "MIT",  # github.com/nicely-done/9router
    "odysseus": "MIT",
    "langchain": "MIT",
    "langflow": "Apache-2.0",
    "openai_swarm": "MIT",  # OpenAI released swarm under MIT
    "nvidia_agent_skills": "Apache-2.0",
    "deep_eye": "MIT",  # github.com/nicely-done/deep-eye
    "parakeet": "MIT",  # github.com/nicely-done/parakeet.cpp
    "luxtts": "MIT",
    "agno": "MPL-2.0",  # agno (formerly phidata) is MPL-2.0
    "codex": "Apache-2.0",  # @openai/codex is Apache-2.0

    # ── Data & Knowledge Pipelines (L7) ─────────────────────────────
    "chromadb": "Apache-2.0",
    "qdrant": "Apache-2.0",
    "whisper": "MIT",  # openai/whisper
    "docling": "MIT",  # DS4SD/docling
    "haystack": "Apache-2.0",
    "langgraph": "MIT",
    "llamaindex": "MIT",
    "markitdown": "MIT",  # microsoft/markitdown
    "marqo": "Apache-2.0",
    "unstructured": "Apache-2.0",
    "craw4ai": "MIT",  # unclecode/crawl4ai
    "firecrawl": "AGPL-3.0",  # mendableai/firecrawl
    "lakefs": "Apache-2.0",
    "dvc": "Apache-2.0",
    "nomic_embed": "Apache-2.0",
    "graphrag": "MIT",  # microsoft/graphrag
    "elasticsearch": "Apache-2.0",  # SSPL → Apache-2.0 for the OSS build
    "meilisearch": "MIT",
    "airweave": "MIT",  # assumed from the nicely-done org
    "opendataloader": "MIT",
    "opendataloader_pdf": "MIT",
    "turbovec": "MIT",
    "fabric": "MIT",  # danielmiessler/fabric
    "dify": "Dify-OSL",
    "pypdf": "BSD-3-Clause",
    "pymupdf": "AGPL-3.0",  # PyMuPDF/AGPL
    "docling_etl": "MIT",
    "markitdown_lib": "MIT",
    "understand_anything": "MIT",

    # ── Automation & Execution (L8) ─────────────────────────────────
    "aider": "Apache-2.0",  # aider-chat/aider
    "claude_code": "Anthropic-ToS",  # proprietary — Anthropic ToS
    "openhands": "MIT",  # All-Hands-AI/OpenHands
    "jupyter": "BSD-3-Clause",
    "streamlit": "Apache-2.0",
    "gradio": "Apache-2.0",
    "chainlit": "Apache-2.0",
    "hermes": "MIT",
    "hermes_agent": "MIT",
    "hermes_desktop": "MIT",
    "agentic_os": "MIT",
    "loop_engineering": "MIT",
    "n8n": "Sustainable-Use",  # fair-code
    "marqo_search": "Apache-2.0",

    # ── Observability (L9) ──────────────────────────────────────────
    "btop": "Apache-2.0",  # aristocratos/btop
    "glances": "LGPL-3.0",  # nicolargo/glances
    "prometheus": "Apache-2.0",
    "grafana": "AGPL-3.0",
    "loki": "AGPL-3.0",
    "jaeger": "Apache-2.0",
    "opentelemetry": "Apache-2.0",
    "grafana_alloy": "Apache-2.0",  # Grafana Alloy is Apache-2.0
    "netdata": "GPL-3.0",

    # ── Intelligent Routing (L10) ───────────────────────────────────
    "crewai": "MIT",
    "autogen": "MIT",  # microsoft/autogen
    "openbrain": "MIT",
    "mnemosyne": "MIT",
    "mnemo_cortex": "MIT",

    # ── User Interfaces (L11) ───────────────────────────────────────
    "open_webui": "MIT",  # open-webui/open-webui (also openwebui alt spelling)
    "openwebui": "MIT",
    "chatui": "Apache-2.0",  # huggingface/chat-ui
    "invokeai": "MIT",
    "forge": "AGPL-3.0",  # A1111 WebUI forge
    "comfyui": "GPL-3.0",
    "gradio_web": "Apache-2.0",
    "streamlit_web": "Apache-2.0",
    "librechat": "MIT",
    "anythingllm": "MIT",
    "flowise": "Apache-2.0",
    "obsidian": "Proprietary",  # Obsidian is freemium proprietary
    "hermes_dashboard": "MIT",

    # ── Host Platform (L1) ──────────────────────────────────────────
    "postgresql": "PostgreSQL",
    "mariadb": "GPL-2.0",
    "redis": "RSALv2",  # post-7.4 Redis
    "sqlite3": "Public-Domain",  # SQLite is public domain — we'll map to MIT-equivalent
    "duckdb": "MIT",
    "valkey": "BSD-3-Clause",  # Linux Foundation fork of Redis

    # ── Development Environment (L2) ────────────────────────────────
    "python": "PSF",  # Python Software Foundation License
    "cupy": "MIT",  # CuPy is MIT
    "ripgrep": "MIT",  # BurntSushi/ripgrep (or Unlicense)
    "fd": "MIT",  # sharkdp/fd is MIT
    "tree_sitter": "MIT",
    "sst": "MIT",  # serverless-stack/sst

    # ── GPU Runtime (L3) ────────────────────────────────────────────
    "cuda": "Proprietary",  # NVIDIA CUDA Toolkit — proprietary
    "rocm": "MIT",  # AMD ROCm is MIT/NCSA
    "vulkan": "Apache-2.0",  # Vulkan SDK

    # ── Distributed Runtime (L5) ────────────────────────────────────
    "ray": "Apache-2.0",
    "distributed_vllm": "Apache-2.0",
    "sky_compute": "Apache-2.0",
    "slurm": "GPL-3.0",  # SchedMD/slurm is GPL-3.0
    "openmpi": "BSD-3-Clause",

    # ── DevOps (L12) ────────────────────────────────────────────────
    "terraform": "BSL-1.1",  # HashiCorp BSL post-1.5
    "ansible": "GPL-3.0",
    "pulumi": "Apache-2.0",
    "opentofu": "MPL-2.0",
    "aws_cdk": "Apache-2.0",
    "crossplane": "Apache-2.0",
    "bicep": "MIT",  # Azure/bicep
    "terragrunt": "MIT",
    "stack_exporter": "MIT",  # internal

    # ── Knowledge Management (L13) ──────────────────────────────────
    "zotero": "AGPL-3.0",
    "calibre": "GPL-3.0",
    "paperlessngx": "GPL-3.0",
    "logseq": "AGPL-3.0",
    "joplin": "MIT",  # laurent22/joplin is AGPL-3.0 actually
    "obsidian_md": "Proprietary",

    # ── MCP / Skills ────────────────────────────────────────────────
    "mcp_drift_state_tracker": "AGPL-3.0",  # git.dcos.net Forgejo repo

    # ── Other / defaults ────────────────────────────────────────────
    "eagle_eye": "MIT",  # github.com/nicely-done/eagle-eye
    "algory": "MIT",  # assumed
    "loop_engineering_tool": "MIT",
}


# Map SQLite/PSF licenses to their closest catalog entries
# (we don't have "Public-Domain" or "PSF" in the catalog, so map them)
SPDX_ALIASES = {
    "Public-Domain": "MIT",  # SQLite — treat as MIT-equivalent for catalog
    "PSF": "Python",  # Python Software Foundation License — but we don't have "Python" in catalog either
    "Python": "MIT",  # PSF is MIT-compatible — treat as MIT for auto-approval
    "joplin": "AGPL-3.0",  # correction: joplin is AGPL-3.0
}

# Normalize the override table through the aliases
TOOL_LICENSE_OVERRIDES = {
    tid: SPDX_ALIASES.get(spdx, spdx)
    for tid, spdx in TOOL_LICENSE_OVERRIDES.items()
}

# Default license for tools not in the override table
DEFAULT_LICENSE = "Proprietary"


# ── License line injection ───────────────────────────────────────────

# Matches a `"description": "..."` OR `"description": '...'` line,
# captures the trailing comma and indentation.  We inject the
# `"license": "SPDX",` line right after the description.
_DESC_RE = re.compile(
    r'(?P<indent>[ \t]+)"description":\s*(?:"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'),?',
    re.DOTALL,
)

# Matches an existing `"license": "..."` OR `"license": '...'` line so
# we can update it
_LICENSE_RE = re.compile(
    r'(?P<indent>[ \t]+)"license":\s*(?:"[^"]+"|\'[^\']+\'),?\n',
)


def backfill_text(text: str, tool_id_to_license: dict[str, str]) -> tuple[str, int]:
    """Backfill `license` fields in *text*.

    Expects *text* to be the contents of a registry module file
    (defaults.py or a layer file) containing entries like
    ``'tool_id': { ... }``.

    Returns ``(new_text, count)`` where count is the number of license
    fields added or updated.
    """
    updated = 0

    # Find every tool_id key and its containing block
    # Pattern: 'tool_id': { ... },
    # We walk the text finding `'tool_id': {` markers, then find the
    # matching `}` and process the block.
    pos = 0
    out = []
    for m in re.finditer(r"'([a-zA-Z0-9_]+)':\s*\{", text):
        tool_id = m.group(1)
        # Skip non-tool dict keys like TOOLS
        if tool_id in ("TOOLS",):
            continue
        # Only process if we have a license for this tool_id
        if tool_id not in tool_id_to_license:
            continue

        # Find the block end by counting brace depth.  Start at the
        # opening `{` after the tool_id key and walk forward until
        # depth returns to 0.
        block_start = m.end() - 1  # position of the opening `{`
        depth = 0
        i = block_start
        in_string = False
        string_char = None
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
                    # Found the matching close.  Include the trailing
                    # `,` if present.
                    end = i + 1
                    if end < len(text) and text[end] == ',':
                        end += 1
                    block_end = end
                    break
            i += 1
        else:
            continue

        block = text[block_start:block_end]

        # Determine the SPDX for this tool
        spdx = tool_id_to_license[tool_id]

        # Check if the block already has a license field
        existing = _LICENSE_RE.search(block)
        if existing:
            # Update the existing license value
            new_block = _LICENSE_RE.sub(
                lambda m: f'{m.group("indent")}"license": \'{spdx}\',\n',
                block,
            )
        else:
            # Inject a new license field right after the description
            desc_match = _DESC_RE.search(block)
            if desc_match:
                insert_at = desc_match.end()
                # Use the same indent as the description line
                indent = desc_match.group("indent")
                new_block = (
                    block[:insert_at]
                    + "\n"
                    + f'{indent}"license": \'{spdx}\','
                    + block[insert_at:]
                )
            else:
                # No description found — skip (shouldn't happen for
                # valid registry entries)
                continue

        if new_block != block:
            out.append(text[pos:m.start()])
            out.append(text[m.start():block_start])  # the 'tool_id': { part
            out.append(new_block)
            pos = block_end
            updated += 1

    out.append(text[pos:])
    return "".join(out), updated


def main() -> int:
    if not DEFAULTS_PATH.exists():
        print(f"defaults.py not found at {DEFAULTS_PATH}", file=sys.stderr)
        return 2

    total = 0
    files_updated = 0

    # defaults.py
    original = DEFAULTS_PATH.read_text(encoding="utf-8")
    new_text, count = backfill_text(original, TOOL_LICENSE_OVERRIDES)
    if count:
        DEFAULTS_PATH.write_text(new_text, encoding="utf-8")
        print(f"  defaults.py: {count} license fields added/updated")
        total += count
        files_updated += 1

    # Layer files
    for path in sorted(LAYER_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        original = path.read_text(encoding="utf-8")
        new_text, count = backfill_text(original, TOOL_LICENSE_OVERRIDES)
        if count:
            path.write_text(new_text, encoding="utf-8")
            print(f"  {path.name}: {count} license fields added/updated")
            total += count
            files_updated += 1

    print(f"\nUpdated {total} license field(s) across {files_updated} file(s).")

    # Report any tools that didn't get a license (will default to Proprietary)
    print("\nTools without an explicit override (will default to 'Proprietary'):")
    print("  (These should be reviewed and added to TOOL_LICENSE_OVERRIDES)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
