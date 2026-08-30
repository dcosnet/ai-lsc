#!/usr/bin/env python3
"""Finish the 10-Layer Systems Architecture Taxonomy migration for AI-LSC.

This is the corrected, completed version of the partial migration that was
started in the repo root ``apply_taxonomy_migration.py`` (which had defect
fixes needed: regexes that could not match multi-word layer names, a ``sys``
scoping bug, lossy installer handling, and no ``defaults.py`` install).

Stages
------
1. defaults   — build the new 108-tool ``defaults.py``: taxonomy fields
                (level/layer/role/category) + richer descriptions from the
                master-target registry; operational fields (installer,
                launcher, deps, flags, license, filesystem) preserved from
                the previous registry.
2. layers     — realign the 11 modular layer files (185 tools) to the
                10-layer taxonomy; classify the 78 tools absent from the
                master registry; reconcile ``kanban`` into the layer files.
3. wiring     — migrate ``stack/connections.py``: static layer= values get
                their new-layer names; loop-based bulk allocations become
                dynamic registry lookups (with a supplement for wired tools
                outside DEFAULT_REGISTRY).
4. categorymap— extend the db_manager CATEGORY_MAP (+ reference file) so
                the categorisation cascade covers every registry category.
5. docfixes   — validator level range, stale header comments.

Run from the repo root of the tree being migrated:
    python3 scripts/migrate_10layer.py --new-defaults /path/to/new/defaults.py [stage...]
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path.cwd().resolve()                             # tree being migrated
SRC = REPO / "src"

NEW_LAYERS = [
    "Host Platform & Infrastructure",
    "Development Runtime & Environment",
    "GPU Acceleration & Optimization",
    "Local Inference Engines",
    "Intelligent API Routers & Proxies",
    "Multi-Agent Orchestration Runtimes",
    "Agentic Software Engineering & Sandboxes",
    "Decentralized Knowledge & Vector Stores",
    "Data Extraction & Pipeline Harvest",
    "Human Interface & System Operations",
]
LAYER_LEVEL = {name: i + 1 for i, name in enumerate(NEW_LAYERS)}

# Classification of the 78 modular-layer tools that are absent from the
# 108-tool master registry.  Assignments follow the 10-layer philosophy:
#   L1  foundational daemons (data, isolation, edge, identity, secrets)
#   L2  runtimes, compilers, build, debug, shells, VCS
#   L6  agent coordination / reasoning / workflow frameworks
#   L7  agentic software engineering (coding agents, code skills)
#   L8  agent memory + vector/graph stores
#   L10 human interfaces, telemetry, IaC, cluster + security operations
TOOL_CLASSIFICATION: dict[str, str] = {
    # L1 — Host Platform & Infrastructure
    "certbot": "Host Platform & Infrastructure",
    "cloudflared": "Host Platform & Infrastructure",
    "nginx": "Host Platform & Infrastructure",
    "docker": "Host Platform & Infrastructure",
    "podman": "Host Platform & Infrastructure",
    "lxc": "Host Platform & Infrastructure",
    "firecracker": "Host Platform & Infrastructure",
    "qemu": "Host Platform & Infrastructure",
    "libvirt": "Host Platform & Infrastructure",
    "tmux": "Host Platform & Infrastructure",
    "keycloak": "Host Platform & Infrastructure",
    "vault": "Host Platform & Infrastructure",
    "fail2ban": "Host Platform & Infrastructure",
    # L2 — Development Runtime & Environment
    "bash": "Development Runtime & Environment",
    "fish": "Development Runtime & Environment",
    "zsh": "Development Runtime & Environment",
    "mksh": "Development Runtime & Environment",
    "git": "Development Runtime & Environment",
    "deno": "Development Runtime & Environment",
    "go": "Development Runtime & Environment",
    "java_jdk": "Development Runtime & Environment",
    "julia": "Development Runtime & Environment",
    "nodejs": "Development Runtime & Environment",
    "perl": "Development Runtime & Environment",
    "php": "Development Runtime & Environment",
    "ruby": "Development Runtime & Environment",
    "rust": "Development Runtime & Environment",
    "gcc": "Development Runtime & Environment",
    "make": "Development Runtime & Environment",
    "cmake": "Development Runtime & Environment",
    "bison": "Development Runtime & Environment",
    "fakeroot": "Development Runtime & Environment",
    "patchelf": "Development Runtime & Environment",
    "pkg_config": "Development Runtime & Environment",
    "upx": "Development Runtime & Environment",
    "uv": "Development Runtime & Environment",
    "gdb": "Development Runtime & Environment",
    "ltrace": "Development Runtime & Environment",
    "strace": "Development Runtime & Environment",
    "valgrind": "Development Runtime & Environment",
    "distcc": "Development Runtime & Environment",
    "dma": "Development Runtime & Environment",
    # L3 — GPU Acceleration & Optimization
    "tinygrad": "GPU Acceleration & Optimization",
    # L4 — Local Inference Engines
    "sglang": "Local Inference Engines",
    # L5 — Intelligent API Routers & Proxies
    "meshllm": "Intelligent API Routers & Proxies",
    # L6 — Multi-Agent Orchestration Runtimes
    "agent_reach": "Multi-Agent Orchestration Runtimes",
    "algory": "Multi-Agent Orchestration Runtimes",
    "atlas_os": "Multi-Agent Orchestration Runtimes",
    "glassmind": "Multi-Agent Orchestration Runtimes",
    "headroom": "Multi-Agent Orchestration Runtimes",
    "honcho": "Multi-Agent Orchestration Runtimes",
    "letta": "Multi-Agent Orchestration Runtimes",
    "nightshift": "Multi-Agent Orchestration Runtimes",
    "nvidia_agent_skills": "Multi-Agent Orchestration Runtimes",
    "odysseus": "Multi-Agent Orchestration Runtimes",
    "openbrain": "Multi-Agent Orchestration Runtimes",
    "ray": "Multi-Agent Orchestration Runtimes",
    # L7 — Agentic Software Engineering & Sandboxes
    "gemini_cli": "Agentic Software Engineering & Sandboxes",
    "goose": "Agentic Software Engineering & Sandboxes",
    "opencode": "Agentic Software Engineering & Sandboxes",
    "qwen_code": "Agentic Software Engineering & Sandboxes",
    "zcoder": "Agentic Software Engineering & Sandboxes",
    "picode": "Agentic Software Engineering & Sandboxes",
    "graphify": "Agentic Software Engineering & Sandboxes",
    # L8 — Decentralized Knowledge & Vector Stores
    "everos_memory": "Decentralized Knowledge & Vector Stores",
    "mem0": "Decentralized Knowledge & Vector Stores",
    "mnemo_cortex": "Decentralized Knowledge & Vector Stores",
    "turbovec": "Decentralized Knowledge & Vector Stores",
    # L10 — Human Interface & System Operations
    "hermes_webui": "Human Interface & System Operations",
    "jan": "Human Interface & System Operations",
    "btop": "Human Interface & System Operations",
    "eagle_eye": "Human Interface & System Operations",
    "crossplane": "Human Interface & System Operations",
    "pssh": "Human Interface & System Operations",
    "n8n": "Human Interface & System Operations",
    "clamav": "Human Interface & System Operations",
    "trivy": "Human Interface & System Operations",
    "opa": "Human Interface & System Operations",
}

# Categories added to the CATEGORY_MAP cascade for the classified tools
# (category -> layer).  Role mirrors the category, per existing convention.
EXTRA_CATEGORY_LAYERS: dict[str, str] = {
    "VCS": "Development Runtime & Environment",
    "Shell": "Development Runtime & Environment",
    "Runtime": "Development Runtime & Environment",
    "Build": "Development Runtime & Environment",
    "Build Monitoring": "Development Runtime & Environment",
    "Distributed Compilation": "Development Runtime & Environment",
    "Debugging": "Development Runtime & Environment",
    "Terminal": "Host Platform & Infrastructure",
    "Networking": "Host Platform & Infrastructure",
    "Containers": "Host Platform & Infrastructure",
    "Virtualization": "Host Platform & Infrastructure",
    "Auth": "Host Platform & Infrastructure",
    "Secrets Management": "Host Platform & Infrastructure",
    "Intrusion Prevention": "Host Platform & Infrastructure",
    "Antivirus": "Human Interface & System Operations",
    "Container Security": "Human Interface & System Operations",
    "Policy Engine": "Human Interface & System Operations",
    "IaC Control Plane": "Human Interface & System Operations",
    "Cluster SSH": "Human Interface & System Operations",
    "Project Management": "Human Interface & System Operations",
    "Workflow Automation": "Multi-Agent Orchestration Runtimes",
    "Multi-Agent": "Multi-Agent Orchestration Runtimes",
    "AI Agent": "Multi-Agent Orchestration Runtimes",
    "Agent OS": "Multi-Agent Orchestration Runtimes",
    "Agent Toolkit": "Multi-Agent Orchestration Runtimes",
    "Agent Framework": "Multi-Agent Orchestration Runtimes",
    "Reasoning Engine": "Multi-Agent Orchestration Runtimes",
    "Agent Workflow": "Multi-Agent Orchestration Runtimes",
    "Infrastructure": "Multi-Agent Orchestration Runtimes",
    "Distributed Compute": "Multi-Agent Orchestration Runtimes",
    "AI Coding Agent": "Agentic Software Engineering & Sandboxes",
    "Claude Code Skill": "Agentic Software Engineering & Sandboxes",
    "Mesh Client": "Agentic Software Engineering & Sandboxes",
    "LLM Mesh": "Intelligent API Routers & Proxies",
    "LLM Serving": "Local Inference Engines",
    "Persistent Memory": "Decentralized Knowledge & Vector Stores",
    "Memory System": "Decentralized Knowledge & Vector Stores",
    "Cortex Memory": "Decentralized Knowledge & Vector Stores",
    "Chat Frontend": "Human Interface & System Operations",
    "LLM GUI": "Human Interface & System Operations",
    "Metrics": "Human Interface & System Operations",
    "Observability": "Human Interface & System Operations",
}

# The v3.1.1b db_manager (canonical 124-category cascade) carries a
# richer 124-category cascade than the master target's 103-category map.
# These alt-only categories are translated to the 10-layer taxonomy so
# the categorisation cascade keeps its full coverage.
ALT_CATEGORY_TRANSLATIONS: dict[str, str] = {
    "AI Assistant Platform": "Human Interface & System Operations",
    "AI Augmentation": "Multi-Agent Orchestration Runtimes",
    "AI Monitoring": "Human Interface & System Operations",
    "AI Observability": "Human Interface & System Operations",
    "AI Operating System": "Multi-Agent Orchestration Runtimes",
    "Academic References": "Human Interface & System Operations",
    "Agent Network": "Multi-Agent Orchestration Runtimes",
    "Algorithm Toolkit": "Multi-Agent Orchestration Runtimes",
    "Audio Parsing": "Data Extraction & Pipeline Harvest",
    "Chat": "Human Interface & System Operations",
    "Chat Agent Platform": "Human Interface & System Operations",
    "Code Analysis": "Agentic Software Engineering & Sandboxes",
    "Code Generation": "Agentic Software Engineering & Sandboxes",
    "Computer Vision": "Data Extraction & Pipeline Harvest",
    "Config Management": "Human Interface & System Operations",
    "Container Ops": "Host Platform & Infrastructure",
    "Context Manager": "Agentic Software Engineering & Sandboxes",
    "Dashboard": "Human Interface & System Operations",
    "Data Pipeline": "Data Extraction & Pipeline Harvest",
    "Data Sync": "Data Extraction & Pipeline Harvest",
    "Desktop Agent": "Human Interface & System Operations",
    "Dev Automation": "Agentic Software Engineering & Sandboxes",
    "Development": "Agentic Software Engineering & Sandboxes",
    "Document Converter": "Data Extraction & Pipeline Harvest",
    "Document Management": "Human Interface & System Operations",
    "Document Understanding": "Data Extraction & Pipeline Harvest",
    "Ebook Library": "Human Interface & System Operations",
    "Ecosystem Dashboard": "Human Interface & System Operations",
    "Efficient LLM": "Local Inference Engines",
    "File Parsing": "Data Extraction & Pipeline Harvest",
    "Find Tool": "Development Runtime & Environment",
    "GPU": "GPU Acceleration & Optimization",
    "Graph RAG": "Decentralized Knowledge & Vector Stores",
    "Homepage": "Human Interface & System Operations",
    "IaC": "Human Interface & System Operations",
    "IaC Wrapper": "Human Interface & System Operations",
    "Image Generation": "Human Interface & System Operations",
    "Knowledge Graph": "Decentralized Knowledge & Vector Stores",
    "Knowledge Graph Notes": "Human Interface & System Operations",
    "LLM Evaluation": "Human Interface & System Operations",
    "LLM Fine-tuning": "GPU Acceleration & Optimization",
    "LLM Framework": "Multi-Agent Orchestration Runtimes",
    "LLM Router": "Intelligent API Routers & Proxies",
    "LLM Runtime": "Local Inference Engines",
    "MCP Server": "Agentic Software Engineering & Sandboxes",
    "Model Training": "GPU Acceleration & Optimization",
    "Notes": "Human Interface & System Operations",
    "OCI Export": "Host Platform & Infrastructure",
    "Outliner": "Human Interface & System Operations",
    "PDF Pipeline": "Data Extraction & Pipeline Harvest",
    "Parser": "Development Runtime & Environment",
    "Pipeline": "Intelligent API Routers & Proxies",
    "Procfile Runner": "Multi-Agent Orchestration Runtimes",
    "Prompt Tooling": "Agentic Software Engineering & Sandboxes",
    "Provisioning": "Human Interface & System Operations",
    "Proxy": "Intelligent API Routers & Proxies",
    "Sandbox": "Host Platform & Infrastructure",
    "Search Engine": "Decentralized Knowledge & Vector Stores",
    "Search Tool": "Development Runtime & Environment",
    "Serverless Framework": "Development Runtime & Environment",
    "Single-File LLM": "Local Inference Engines",
    "Skill Analysis": "Agentic Software Engineering & Sandboxes",
    "Skill Inspection": "Agentic Software Engineering & Sandboxes",
    "Spaced Repetition": "Human Interface & System Operations",
    "Spec Writer": "Agentic Software Engineering & Sandboxes",
    "Speech Recognition": "Data Extraction & Pipeline Harvest",
    "Task Runner": "Human Interface & System Operations",
    "Telemetry": "Human Interface & System Operations",
    "Text-to-Speech": "Data Extraction & Pipeline Harvest",
    "Uncensored Models": "Local Inference Engines",
    "Vector Store": "Decentralized Knowledge & Vector Stores",
    "Visualization": "Human Interface & System Operations",
    "Web Crawler": "Data Extraction & Pipeline Harvest",
    "Workflow": "Human Interface & System Operations",
}


# ── helpers ───────────────────────────────────────────────────────────

def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def py_str(value: str) -> str:
    """Render a string as a single-quoted Python literal (old-file style)."""
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def render_tool_block(tid: str, entry: dict, indent: str = "    ") -> list[str]:
    """Render one registry entry in the historical defaults.py style."""
    lines = [
        f"{indent}'{tid}': {{",
        f'{indent}"name": {py_str(entry["name"])},',
        f'{indent}"level": {entry["level"]},',
        f'{indent}"layer": {py_str(entry["layer"])},',
        f'{indent}"role": {py_str(entry["role"])},',
        f'{indent}"category": {py_str(entry["category"])},',
        f'{indent}"installer": {{',
    ]
    for key, val in entry["installer"].items():
        if key == "env_overrides":
            lines.append(f'{indent}    "env_overrides": {{')
            for env_k, env_v in val.items():
                lines.append(f'{indent}        {py_str(env_k)}: {py_str(env_v)},')
            lines.append(f'{indent}    }},')
        elif isinstance(val, bool):
            lines.append(f'{indent}    "{key}": {val},')
        elif isinstance(val, (int, float)):
            lines.append(f'{indent}    "{key}": {val},')
        else:
            lines.append(f'{indent}    "{key}": {py_str(val)},')
    lines.append(f'{indent}}},')
    lines.append(f'{indent}"launcher": {{')
    for key, val in entry["launcher"].items():
        if val is None or isinstance(val, bool):
            lines.append(f'{indent}    "{key}": {val},')
        elif isinstance(val, (int, float)):
            lines.append(f'{indent}    "{key}": {val},')
        else:
            lines.append(f'{indent}    "{key}": {py_str(val)},')
    lines.append(f'{indent}}},')
    lines.append(f'{indent}"deps": [')
    lines += [f'{indent}    {py_str(d)},' for d in entry["deps"]]
    lines.append(f"{indent}],")
    if "filesystem" in entry:
        lines.append(f'{indent}"filesystem": {{')
        for key, val in entry["filesystem"].items():
            lines.append(f'{indent}    "{key}": {py_str(val)},')
        lines.append(f'{indent}}},')
    lines.append(f'{indent}"description": {py_str(entry["description"])},')
    lines.append(f'{indent}"license": {py_str(entry["license"])},')
    flags = entry["flags"]
    lines.append(f'{indent}"flags": {{')
    for key in ("has_cli", "has_gui", "has_web", "is_ollama",
                "is_passive", "is_mcp", "is_skills_collection"):
        lines.append(f'{indent}    "{key}": {flags[key]},')
    lines.append(f'{indent}}}')
    lines.append(f"{indent}}},")
    return lines


# ── Stage 1: defaults.py ─────────────────────────────────────────────

DEFAULTS_HEADER = '''"""
AI-LSC — Default tool registry (108 tools, 10-Layer Systems Architecture).

This is the first-boot seed registry.  The canonical source of truth at
runtime is the set of modular per-layer files under
``ai_lsc/registry/layers`` (discovered by :mod:`ai_lsc.registry.loader`);
``RegistryManager`` seeds ``ecosystem.json`` from the merged layer files
and syncs structural fields (layer, level, role, category) from them on
every start while preserving user customisations.

Convention
----------
Every entry has the same top-level shape::

    {
        "name":       <Human-readable display name>,
        "level":      <1–10 taxonomy level (int)>,
        "layer":      <Layer name matching NAV_LAYER_ORDER>,
        "role":       <Functional role within the layer>,
        "category":   <UI grouping category>,
        "installer":  {"type": <pacman|uv|pipx|pip|npm|git|git_node|script|custom>,
                        "pkg": <package name or URL>,
                        "cmd": <only for "script" type>,
                        "post_install" / "update_cmd" / "env_overrides": optional},
        "launcher":  {"type": <systemd|tmux|desktop>,
                        "cmd": <shell command with {placeholders}>,
                        "default_port": <int | None>},
        "deps":       [<tool_ids this tool depends on>],
        "description": <One-line human description>,
        "license":    <SPDX ID from registry/licenses.py>,
        "flags":      {<ToolFlags boolean fields>},
        "filesystem": {optional install/config/cache/logs/models paths},
    }

Launcher command placeholders
-----------------------------
``{port}``, ``{tools_root}``, ``{models_root}``,
``{workspaces_root}``, ``{base_dir}`` are resolved at launch time by
the ``ServiceRow`` dispatcher.

Layer map (10-Layer Systems Architecture Taxonomy)
---------------------------------------------------
L1  Host Platform & Infrastructure          — databases, caches, isolation, edge daemons
L2  Development Runtime & Environment       — runtimes, compilers, build, debug, search, VCS
L3  GPU Acceleration & Optimization          — CUDA, mixed precision, tensor libraries
L4  Local Inference Engines                  — local LLM servers (vLLM, llama.cpp, Ollama)
L5  Intelligent API Routers & Proxies        — LiteLLM, routers, mesh transport
L6  Multi-Agent Orchestration Runtimes       — Swarm, AutoGen, CrewAI, reasoning engines
L7  Agentic Software Engineering & Sandboxes — OpenHands, Aider, Claude Code, code skills
L8  Decentralized Knowledge & Vector Stores  — Chroma, Qdrant, Neo4j, agent memory
L9  Data Extraction & Pipeline Harvest       — Docling, Crawl4AI, Whisper, ETL
L10 Human Interface & System Operations      — chat consoles, telemetry, flow canvases, IaC

Flags
-----
``has_cli`` / ``has_gui`` / ``has_web`` describe the active surface(s) a
user can interact with once the tool is running.

``is_passive`` marks tools that are *consumed* (libraries, model packs,
CLIs without a daemon) rather than launched as long-running services.
``is_mcp`` marks MCP (Model Context Protocol) API tools.
``is_skills_collection`` marks bundled skill / capability definitions.

NOTE: This dict is intentionally kept as a *literal* so that it can be
      round-tripped through JSON without loss.  Do NOT add non-serialisable
      objects (Path, Enum, etc.) here.
"""

# NOTE: This dict is intentionally kept as a *literal* so that it can be
#       round-tripped through JSON without loss.  Do NOT add non-serialisable
#       objects (Path, Enum, etc.) here.

'''


def stage_defaults(new_defaults_path: Path) -> None:
    old_mod = load_module(SRC / "ai_lsc" / "registry" / "defaults.py", "old_defaults")
    new_mod = load_module(new_defaults_path, "new_defaults")
    old, new = old_mod.DEFAULT_REGISTRY, new_mod.DEFAULT_REGISTRY

    merged: dict[str, dict] = {}
    for tid, entry in new.items():
        prev = old.get(tid, {})
        out = dict(entry)  # taxonomy + description from the master target
        # Operational metadata is preserved from the previous registry:
        # the master-target file rewrote installers (placeholder URLs,
        # dropped cmds), launchers (wrong binary names, systemd→tmux),
        # deps (all edges wiped), licenses and flags.
        for field in ("installer", "launcher", "deps", "flags", "license"):
            if field in prev:
                out[field] = prev[field]
        if "filesystem" in prev:
            out["filesystem"] = prev["filesystem"]
        merged[tid] = out

    # sanity: every layer/level pair must be consistent with the taxonomy
    for tid, entry in merged.items():
        assert entry["layer"] in LAYER_LEVEL, f"{tid}: unknown layer {entry['layer']!r}"
        assert entry["level"] == LAYER_LEVEL[entry["layer"]], \
            f"{tid}: level {entry['level']} != taxonomy level for {entry['layer']!r}"

    lines = [DEFAULTS_HEADER, "DEFAULT_REGISTRY: dict = {"]
    order = sorted(merged, key=lambda t: (merged[t]["level"], t))
    current_level = 0
    for tid in order:
        entry = merged[tid]
        if entry["level"] != current_level:
            current_level = entry["level"]
            banner = f"L{current_level}: {entry['layer']}"
            pad = max(4, 62 - len(banner))
            lines.append("")
            lines.append(f"    # ── {banner} {'─' * pad}")
            lines.append("")
        lines += render_tool_block(tid, entry)
    lines.append("}")
    lines.append("")

    out_path = SRC / "ai_lsc" / "registry" / "defaults.py"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[defaults] wrote {out_path} ({len(merged)} tools)")


# ── Stage 2: layer files ─────────────────────────────────────────────

def find_block_span(content: str, tid: str) -> tuple[int, int] | None:
    """Locate `'tid': {` ... matching close brace in a layer file."""
    m = re.search(rf"^(\s*)['\"]{re.escape(tid)}['\"]\s*:\s*\{{", content, re.M)
    if not m:
        return None
    start = m.start()
    depth = 0
    for i in range(m.end() - 1, len(content)):
        ch = content[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
    return None


def set_field(block: str, key: str, value: str) -> str:
    """Replace (or insert) a top-level "key": <value> line in a tool block."""
    pattern = re.compile(rf'^(\s*)"{key}"\s*:\s*[^,\n]+,?$', re.M)
    line = f'"{key}": {value},'
    if pattern.search(block):
        return pattern.sub(lambda m: f"{m.group(1)}{line}", block, count=1)
    # insert after the opening brace line
    return re.sub(r"^(\s*['\"][^'\"]+['\"]\s*:\s*\{)",
                  lambda m: f"{m.group(1)}\n    {line}", block, count=1)


def stage_layers(new_defaults_path: Path) -> None:
    new_mod = load_module(new_defaults_path, "new_defaults")
    new = new_mod.DEFAULT_REGISTRY
    layers_dir = SRC / "ai_lsc" / "registry" / "layers"

    # import merged registry from the tree being migrated
    sys.path.insert(0, str(SRC))
    loader = importlib.import_module("ai_lsc.registry.loader")
    merged = loader.load_merged_registry()
    sys.path.pop(0)

    # resolve the final structural assignment for every registry tool
    final: dict[str, dict[str, str]] = {}
    for tid, entry in merged.items():
        if tid in new:
            src = new[tid]
            final[tid] = {"layer": src["layer"], "level": str(src["level"]),
                          "role": src["role"], "category": src["category"]}
        else:
            layer = TOOL_CLASSIFICATION.get(tid)
            assert layer, f"no 10-layer classification for tool {tid!r}"
            final[tid] = {"layer": layer, "level": str(LAYER_LEVEL[layer]),
                          "role": entry["role"], "category": entry["category"]}

    # kanban exists only in defaults.py — reconcile it into the layer files
    old_mod = load_module(SRC / "ai_lsc" / "registry" / "defaults.py", "old_defaults_l")
    kanban = old_mod.DEFAULT_REGISTRY.get("kanban")
    kanban_target_file = "user_interfaces.py"
    if kanban is not None and "kanban" not in merged:
        kanban_layer = new.get("kanban", {}).get("layer", "Human Interface & System Operations")
        kanban_level = new.get("kanban", {}).get("level", 10)
        kanban_role = new.get("kanban", {}).get("role", kanban["role"])
        kanban_cat = new.get("kanban", {}).get("category", kanban["category"])
        final["kanban"] = {"layer": kanban_layer, "level": str(kanban_level),
                           "role": kanban_role, "category": kanban_cat}

    counts: dict[str, int] = {}
    for path in sorted(layers_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        content = path.read_text(encoding="utf-8")
        touched = 0
        for tid, fields in final.items():
            span = find_block_span(content, tid)
            if span is None:
                continue
            block = content[span[0]:span[1]]
            new_block = block
            new_block = set_field(new_block, "layer", py_str(fields["layer"]))
            new_block = set_field(new_block, "level", fields["level"])
            new_block = set_field(new_block, "role", py_str(fields["role"]))
            new_block = set_field(new_block, "category", py_str(fields["category"]))
            if new_block != block:
                content = content[:span[0]] + new_block + content[span[1]:]
                touched += 1
        if path.name == kanban_target_file and kanban is not None and "kanban" not in merged:
            block = "\n".join(render_tool_block("kanban", {
                **kanban,
                "layer": final["kanban"]["layer"],
                "level": int(final["kanban"]["level"]),
                "role": final["kanban"]["role"],
                "category": final["kanban"]["category"],
            }))
            # insert inside the TOOLS dict, before its closing brace
            body = content.rstrip()
            idx = body.rfind("\n}")
            assert idx != -1, f"TOOLS closing brace not found in {path}"
            content = body[:idx] + "\n\n" + block + "\n}\n"
            touched += 1
        if touched:
            path.write_text(content, encoding="utf-8")
        counts[path.name] = touched
        print(f"[layers] {path.name}: realigned {touched} tools")

    # refresh each layer-file module docstring to reference the new taxonomy
    layer_doc_note = (
        "\nStructural fields (layer, level) follow the 10-Layer Systems\n"
        "Architecture Taxonomy; tools may be regrouped across files in a\n"
        "future pass — the loader merges by tool, not by filename.\n"
    )
    for path in sorted(layers_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        content = path.read_text(encoding="utf-8")
        m = re.match(r'^"""(.*?)"""', content, re.S)
        if m and "10-Layer Systems" not in m.group(1):
            doc = m.group(1).rstrip()
            content = f'"""{doc}\n{layer_doc_note}"""' + content[m.end():]
            path.write_text(content, encoding="utf-8")


# ── Stage 3: connections.py ──────────────────────────────────────────

WIRING_PRELUDE = '''

# ── 10-layer taxonomy resolution ──────────────────────────────────────
# Static wiring entries carry their layer as a literal; loop-based bulk
# allocations resolve the layer dynamically from the registry so the
# wiring graph can never drift from the taxonomy again.
from ai_lsc.registry.defaults import DEFAULT_REGISTRY

# Layer assignments for staged tools that live in the modular layer
# files but are not part of the shipped DEFAULT_REGISTRY seed.
_WIRING_LAYER_SUPPLEMENT: dict[str, str] = {
    "agent_reach": "Multi-Agent Orchestration Runtimes",
    "algory": "Multi-Agent Orchestration Runtimes",
    "atlas_os": "Multi-Agent Orchestration Runtimes",
    "clamav": "Human Interface & System Operations",
    "crossplane": "Human Interface & System Operations",
    "distcc": "Development Runtime & Environment",
    "eagle_eye": "Human Interface & System Operations",
    "everos_memory": "Decentralized Knowledge & Vector Stores",
    "gemini_cli": "Agentic Software Engineering & Sandboxes",
    "glassmind": "Multi-Agent Orchestration Runtimes",
    "goose": "Agentic Software Engineering & Sandboxes",
    "graphify": "Agentic Software Engineering & Sandboxes",
    "headroom": "Multi-Agent Orchestration Runtimes",
    "hermes_webui": "Human Interface & System Operations",
    "honcho": "Multi-Agent Orchestration Runtimes",
    "jan": "Human Interface & System Operations",
    "letta": "Multi-Agent Orchestration Runtimes",
    "mem0": "Decentralized Knowledge & Vector Stores",
    "meshllm": "Intelligent API Routers & Proxies",
    "mnemo_cortex": "Decentralized Knowledge & Vector Stores",
    "n8n": "Human Interface & System Operations",
    "nightshift": "Multi-Agent Orchestration Runtimes",
    "nvidia_agent_skills": "Multi-Agent Orchestration Runtimes",
    "odysseus": "Multi-Agent Orchestration Runtimes",
    "openbrain": "Multi-Agent Orchestration Runtimes",
    "opencode": "Agentic Software Engineering & Sandboxes",
    "picode": "Agentic Software Engineering & Sandboxes",
    "pssh": "Human Interface & System Operations",
    "qwen_code": "Agentic Software Engineering & Sandboxes",
    "sglang": "Local Inference Engines",
    "tinygrad": "GPU Acceleration & Optimization",
    "trivy": "Human Interface & System Operations",
    "turbovec": "Decentralized Knowledge & Vector Stores",
    "zcoder": "Agentic Software Engineering & Sandboxes",
    "dma": "Development Runtime & Environment",
    "opa": "Human Interface & System Operations",
}


def _wiring_layer(tool_id: str) -> str:
    """Resolve a tool's 10-layer taxonomy layer for its wiring entry."""
    entry = DEFAULT_REGISTRY.get(tool_id)
    if entry:
        return entry.get("layer", "")
    return _WIRING_LAYER_SUPPLEMENT.get(tool_id, "")

'''

SECTION_RENAMES = [
    ("# L1: Host Platform",
     "# L1: Host Platform  →  Layer 1: Host Platform & Infrastructure"),
    ("# L2: Development Environment",
     "# L2: Development Environment  →  Layer 2: Development Runtime & Environment"),
    ("# L3: GPU Runtime",
     "# L3: GPU Runtime  →  Layer 3: GPU Acceleration & Optimization"),
    ("# L4: Inference Engines",
     "# L4: Inference Engines  →  Layer 4: Local Inference Engines"),
    ("# L6: AI Endpoints  (→ the L5 \"Routing\" layer in the 11-layer taxonomy)",
     "# L6: AI Endpoints  →  Layer 5: Intelligent API Routers & Proxies (10-layer taxonomy)"),
    ("# L10: Intelligent Routing  (folded into \"Orchestrators\" in the 11-layer taxonomy)",
     "# L10: Intelligent Routing  →  Layer 5: Intelligent API Routers & Proxies (10-layer taxonomy)"),
    ("# L7: Data & Knowledge Pipelines",
     "# L7: Data & Knowledge Pipelines  →  Layer 8/9: Vector Stores + Data Extraction (10-layer taxonomy)"),
    ("# L8: Automation & Execution",
     "# L8: Automation & Execution  →  Layer 6/7: Orchestration + Agentic Engineering (10-layer taxonomy)"),
    ("# L9: Observability",
     "# L9: Observability  →  Layer 10: Human Interface & System Operations (10-layer taxonomy)"),
    ("# L11: User Interfaces",
     "# L11: User Interfaces  →  Layer 10: Human Interface & System Operations (10-layer taxonomy)"),
    ("# L12: DevOps",
     "# L12: DevOps  →  Layer 9/10: Data Extraction + System Operations (10-layer taxonomy)"),
    ("# L13: Knowledge Management",
     "# L13: Knowledge Management  →  Layer 8/10: Vector Stores + System Operations (10-layer taxonomy)"),
    ("# L5: Distributed Runtime",
     "# L5: Distributed Runtime  →  Layer 3/4: GPU + Inference Engines (10-layer taxonomy)"),
]


def stage_wiring(new_defaults_path: Path) -> None:
    new_mod = load_module(new_defaults_path, "new_defaults")
    new = new_mod.DEFAULT_REGISTRY

    layer_of: dict[str, str] = {}
    for tid, entry in new.items():
        layer_of[tid] = entry["layer"]
    for tid, layer in TOOL_CLASSIFICATION.items():
        layer_of.setdefault(tid, layer)

    path = SRC / "ai_lsc" / "stack" / "connections.py"
    content = path.read_text(encoding="utf-8")

    # 1. Insert the taxonomy resolution prelude after the imports.
    if "_wiring_layer" not in content:
        anchor = "from typing import Any\n"
        content = content.replace(anchor, anchor + WIRING_PRELUDE, 1)

    # 2. Static StackWiring entries: replace layer="<old>" with the tool's
    #    new layer.  Iterate over `_reg(StackWiring(` blocks.
    parts = content.split("_reg(StackWiring(")
    rebuilt = [parts[0]]
    static_updated = 0
    for part in parts[1:]:
        tid_m = re.search(r'tool_id\s*=\s*"([A-Za-z0-9_.:\-]+)"', part)
        if tid_m:
            tid = tid_m.group(1)
            new_layer = layer_of.get(tid)
            if new_layer:
                part, n = re.subn(
                    r'layer\s*=\s*"[^"]*"',
                    f'layer="{new_layer}"',
                    part, count=1)
                static_updated += n
        rebuilt.append(part)
    content = "_reg(StackWiring(".join(rebuilt)

    # 3. Loop-based bulk allocations -> dynamic lookups.
    loop_pat = re.compile(
        r'layer\s*=\s*"(?:DevOps|User Interfaces|Knowledge Management|'
        r'Orchestrators|Host Platform|Development Environment|GPU Runtimes|'
        r'Engines|Routing|Security|Observability)"')
    content, loops_updated = loop_pat.subn('layer=_wiring_layer(_tid)', content)

    # 4. Refresh section header comments to the 10-layer taxonomy mapping.
    for old, new_c in SECTION_RENAMES:
        content = content.replace(old, new_c)

    path.write_text(content, encoding="utf-8")
    print(f"[wiring] static layers updated: {static_updated}, "
          f"loop allocations converted: {loops_updated}")


# ── Stage 4: CATEGORY_MAP ────────────────────────────────────────────

def category_map_lines(cmap: dict[str, dict]) -> str:
    lines = ["CATEGORY_MAP: dict[str, dict[str, object]] = {"]
    for cat in sorted(cmap):
        val = cmap[cat]
        lines.append(
            f'    "{cat}": {{"layer": "{val["layer"]}", '
            f'"level": {val["level"]}, "role": "{val["role"]}"'
            '},')
    lines.append("}")
    return "\n".join(lines)


def stage_category_map() -> None:
    # Read the current CATEGORY_MAP from the canonical v3.1.1b db_manager
    # (full 124-category cascade in the old 11-layer taxonomy).
    dbm = SRC / "ai_lsc" / "ui" / "pages" / "db_manager.py"
    content = dbm.read_text(encoding="utf-8")
    m = re.search(
        r'CATEGORY_MAP:\s*dict\[str,\s*dict\[str,\s*object\]\]\s*=\s*\{.*?\n\}',
        content, re.S)
    assert m, "CATEGORY_MAP block not found in db_manager.py"
    alt_map = eval(m.group(0).split("=", 1)[1])  # literal dict, safe to eval

    # the master target's 10-layer map (from apply_taxonomy_migration.py)
    atm_path = REPO / "apply_taxonomy_migration.py"
    atm = load_module(atm_path, "atm_map")
    cmap = {cat: dict(val) for cat, val in atm.NEW_CATEGORY_MAP.items()}

    # extend with the categories introduced by the classified tools
    for cat, layer in EXTRA_CATEGORY_LAYERS.items():
        if cat not in cmap:
            cmap[cat] = {"layer": layer, "level": LAYER_LEVEL[layer],
                         "role": cat}
    if "Project Management" not in cmap:
        cmap["Project Management"] = {
            "layer": "Human Interface & System Operations", "level": 10,
            "role": "Project Management"}

    # preserve the alt cascade's richer coverage: keep its curated roles,
    # translate the layer/level to the 10-layer taxonomy
    for cat, val in alt_map.items():
        if cat in cmap:
            continue
        layer = ALT_CATEGORY_TRANSLATIONS.get(cat)
        assert layer, f"no 10-layer translation for alt category {cat!r}"
        cmap[cat] = {"layer": layer, "level": LAYER_LEVEL[layer],
                     "role": val.get("role", cat)}

    # every layer referenced must be a valid 10-layer name
    for cat, val in cmap.items():
        assert val["layer"] in LAYER_LEVEL, f"{cat}: bad layer {val['layer']!r}"
        assert val["level"] == LAYER_LEVEL[val["layer"]], \
            f"{cat}: level {val['level']} inconsistent with {val['layer']!r}"

    new_block = category_map_lines(cmap)
    content = content[:m.start()] + new_block + content[m.end():]

    # refresh the stale header comment above the map
    content = re.sub(
        r'# ── Category → default Layer / Level / Role mapping ──+\n'
        r'# Derived from the canonical registry \(11-layer taxonomy, v3\.1\.1b:\n'
        r'# Routing=L5, Orchestrators=L6, Security=L7, Observability=L8,\n'
        r'# User Interfaces=L9, DevOps=L10, Knowledge Management=L11\)\.\n'
        r'# When the user picks a category these fields auto-fill; the user can\n'
        r'# still override afterwards\.',
        '# ── Category → default Layer / Level / Role mapping ──────────────────\n'
        '# Derived from the canonical registry (10-Layer Systems Architecture\n'
        '# Taxonomy).  When the user picks a category these fields auto-fill;\n'
        '# the user can still override afterwards.',
        content)

    dbm.write_text(content, encoding="utf-8")
    print(f"[categorymap] db_manager.py CATEGORY_MAP -> {len(cmap)} categories")

    # regenerate the standalone reference file
    ref = SRC / "ai_lsc" / "ui" / "pages" / "db_manager_category_map.py"
    ref.write_text(
        "# This file contains the fully reorganized CATEGORY_MAP for db_manager.py\n"
        "# mapped cleanly to the 10-Layer Systems Architecture.\n\n"
        + new_block + "\n",
        encoding="utf-8")
    print(f"[categorymap] regenerated {ref.name}")


# ── Stage 5: doc fixes ───────────────────────────────────────────────

def stage_docfixes() -> None:
    # validator: enforce the 10-level range of the new taxonomy
    vpath = SRC / "ai_lsc" / "registry" / "validator.py"
    content = vpath.read_text(encoding="utf-8")
    content = content.replace(
        "    # Level must be 1–13\n"
        '    level = entry.get("level")\n'
        "    if isinstance(level, int) and not (1 <= level <= 13):\n"
        '        errors.append(f"{tool_id}: level {level} out of range 1-13")',
        "    # Level must be 1–10 (10-Layer Systems Architecture Taxonomy)\n"
        '    level = entry.get("level")\n'
        "    if isinstance(level, int) and not (1 <= level <= 10):\n"
        '        errors.append(f"{tool_id}: level {level} out of range 1-10 "\n'
        '                      f"(10-layer taxonomy)")')
    vpath.write_text(content, encoding="utf-8")
    print("[docfixes] validator level range 1-13 -> 1-10")

    # README layer table + file-tree note
    rpath = REPO / "README.md"
    readme = rpath.read_text(encoding="utf-8")
    old_table_start = readme.find("| Layer | Tools | Examples |")
    old_table_end = readme.find("![Infrastructure Layers]")
    if old_table_start != -1 and old_table_end != -1:
        new_table = (
            "| Layer | Tools | Examples |\n"
            "|-------|-------|----------|\n"
            "| L1 — Host Platform & Infrastructure | 28 | PostgreSQL, MariaDB, Redis, DuckDB, Podman, Docker, LXC, Firecracker, libvirt, nginx, Tmux, Keycloak, Vault |\n"
            "| L2 — Development Runtime & Environment | 37 | Python, uv, Node.js, Deno, Go, Rust, GCC, make, ripgrep, fd, tree-sitter, git, gdb, valgrind |\n"
            "| L3 — GPU Acceleration & Optimization | 5 | CUDA, CuPy, Apex, Unsloth, tinygrad |\n"
            "| L4 — Local Inference Engines | 10 | vLLM, SGLang, llama.cpp, KoboldCPP, Llamafile, Ollama, TurboLLM, AirLLM |\n"
            "| L5 — Intelligent API Routers & Proxies | 4 | LiteLLM Proxy, 9Router Proxy, MeshLLM, Fabric |\n"
            "| L6 — Multi-Agent Orchestration Runtimes | 22 | Swarm, AutoGen, CrewAI, Agno, LangChain, Letta, OpenBrain, Ray, Glassmind |\n"
            "| L7 — Agentic Software Engineering & Sandboxes | 17 | OpenHands, Aider, Claude Code, Codex, Gemini CLI, OpenCode, goose, spec-kit |\n"
            "| L8 — Decentralized Knowledge & Vector Stores | 11 | ChromaDB, LanceDB, Qdrant, Neo4j, Elasticsearch, Meilisearch, Mem0, TurboVec |\n"
            "| L9 — Data Extraction & Pipeline Harvest | 12 | Crawl4AI, Docling, MarkItDown, Whisper, Parakeet, Airweave, OpenDataloader |\n"
            "| L10 — Human Interface & System Operations | 40 | Open WebUI, AnythingLLM, LibreChat, Flowise, n8n, Dify, Grafana, Prometheus, Terraform, Ansible |\n"
            "\n"
        )
        readme = readme[:old_table_start] + new_table + readme[old_table_end:]
        readme = readme.replace(
            "layers/                    # 10 per-layer tool files",
            "layers/                    # 11 per-layer tool files (10-layer taxonomy)")
        rpath.write_text(readme, encoding="utf-8")
        print("[docfixes] README layer table updated")

    # quickstart stale reference
    qpath = REPO / "quickstart.md"
    quick = qpath.read_text(encoding="utf-8")
    quick = quick.replace(
        "the 13-layer architecture", "the 10-layer architecture")
    qpath.write_text(quick, encoding="utf-8")
    print("[docfixes] quickstart layer reference updated")


# ── main ─────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--new-defaults", required=True,
                    help="path to the master-target 108-tool defaults.py")
    ap.add_argument("stages", nargs="*",
                    default=["defaults", "layers", "wiring",
                             "categorymap", "docfixes"],
                    help="stages to run (default: all)")
    args = ap.parse_args()

    new_defaults = Path(args.new_defaults).resolve()
    stages = args.stages or ["defaults", "layers", "wiring",
                             "categorymap", "docfixes"]
    if "defaults" in stages:
        stage_defaults(new_defaults)
    if "layers" in stages:
        stage_layers(new_defaults)
    if "wiring" in stages:
        stage_wiring(new_defaults)
    if "categorymap" in stages:
        stage_category_map()
    if "docfixes" in stages:
        stage_docfixes()
    print("[done]")


if __name__ == "__main__":
    main()
