# AI-LSC MoE QA Pass — Final Report

**Source:** `ai-lsc-main(1).tar.gz`
**Date:** 2026-08-31
**Pass scope:** Surgical cleanup (one more pass after v3.1 critique + v3.2 taxonomy migration).
**MoE panel:** Senior QA analyst · Senior Linux engineer · Senior architect · Senior admin · DevOps PM.

## 1. Standards referenced

| Standard | Application |
|---|---|
| PEP 868 / PEP 8 | Type annotations, line length ≤100, import ordering. |
| POSIX sh / bash | `set -euo pipefail`, no bashisms in sourced contexts. |
| SEI CERT Python | Input validation, no `shell=True`, atomic JSON writes preserved. |
| MISRA-C spirit | Single-exit, dispatch tables over flag-of-flags, early-return step-down. |
| Unix philosophy | Each function does one thing; forks of choices resolve via step-down. |

## 2. Wording sweep — "restored / brought back / related logic" eliminated

All instances rewritten as decisive statements. Source files touched:

| File | Line(s) | Change |
|---|---|---|
| `src/ai_lsc/registry/layers/routing.py` | docstring | "Restored layer (v3.1.1b)" → "L5 (Intelligent API Routers & Proxies) holds …"; added source-of-truth note. |
| `TODO.md` | 6 | "restored in full from the v3.1.1b routing tarball" → "the canonical 1.3 k-line implementation now lives in-tree". |
| `scripts/apply_10layer_taxonomy.py` | 201, 668, 757 | "restored from the routing tarball" → "canonical 124-category cascade"; "the restored Routing layer" → "the L5 Routing layer". |
| `CHANGES.md` | 224, 254, 269, 321 | "Restored in full from the v3.1.1b routing tarball" → "canonical 1.3 k-line implementation is re-established in-tree"; section header "Routing restored" → "Routing promoted to a first-class layer"; "(restored)" ladder annotation removed. |
| `whatremains.txt` | 9 | "the restored installer cmds" → "the canonical installer cmds". |
| `docs/ADR-003-workspace-tab.md` | 67 | "The empty-state placeholder is restored" → "the empty-state placeholder is shown again". |

Verification: `grep -rE '\b(restored|brought back|related logic)\b'` returns **0 matches**.

## 3. Author metadata

| File | Field | Value |
|---|---|---|
| `pyproject.toml` | `authors`, `maintainers` | Jeremy Anderson `<info@dcos.net>` |
| `README.md` | header | Author + email + https://dcos.net link |
| `README.md` | clone URL | `https://github.com/dcos-net/ai-lsc.git` |
| `LICENSE` | header | AUTHOR + COPYRIGHT + HOMEPAGE = `dcos.net` |

## 4. Code patterns — nested ifs → arrays/dispatch tables

### 4.1 `src/ai_lsc/manifest/support.py` — `build_system_context`

Replaced 6 cascaded `if field:` blocks with a single `_FIELDS` tuple + comprehension:

```python
_FIELDS: tuple[tuple[str, str], ...] = (
    ("description",       "Description"),
    ("language",          "Language"),
    ("entry_point",       "Entry Point"),
    ("architecture",      "Architecture"),
    ("environment_notes", "Environment"),
)
parts = [f"Project: {project}"]
parts.extend(
    f"{label}: {manifest.get(key)}"
    for key, label in _FIELDS
    if manifest.get(key)
)
```

Added a "Source-of-truth boundary" docstring noting the manifest is a derived view; the registry layer files remain authoritative.

### 4.2 `src/ai_lsc/manifest/support.py` — `resolve_context_files`

Replaced outer-for + inner-for + if with a single list comprehension (one pass over patterns → files → filter).

### 4.3 `src/ai_lsc/ui/pages/chatbot_console.py` — `_build_payload_history` (M-40 / L-09)

Replaced the 3-way nested ternary
`parts[0] + "\n\n" + parts[1] if len(parts) == 2 else (parts[0] if parts else "")`
with the flat `"\n\n".join(parts)`. Behavior preserved (empty parts → empty string).

### 4.4 `src/ai_lsc/ui/pages/chatbot_console.py` — HTML bubble builder (M-22)

Extracted `_render_bubble(msg)` helper. Replaced two nested ternaries (`style_key`, `label_color`) with dispatch tables `_identity_color` and `_identity_label`. The main loop is now a one-liner:

```python
html += "".join(_render_bubble(m) for m in self.chat_messages)
```

## 5. Unix philosophy — step-down (early return) refactors

### 5.1 `bootstrap.sh` — base-dir detection (lines 70-100)

The 4-level nested `if/elif/else` (root → prompt → sudo/alt-base/error) was inverted to a step-down `if/elif/else` where each branch resolves one situation and exits the block. Removed one nesting level.

### 5.2 `src/ai_lsc/runtime/installer.py` — `install_git` / `install_git_node`

Both methods had a 3-way fork (pull / re-clone-on-failure / clone-non-git-dir / fresh-clone) with duplicated `shutil.move + makedirs + git clone` code across branches. Extracted:

- `_backup_existing(dest) -> str` — single-purpose backup helper.
- `_clone_fresh(pkg, dest) -> None` — single-purpose clone helper.

Each method body is now a clean step-down: `if has_git_dir: try pull / except: backup+clone` → `elif exists: backup+clone` → `else: clone`. Behavior identical; ~30 lines of duplication removed.

### 5.3 `src/ai_lsc/registry/openengineer/importer.py` — directory scan

The two `for md_file in sorted(...)` blocks (subdir scan + root-level scan) with overlapping filter logic were merged into a single `_scan_dir()` helper with keyword-only parameters (`overrides`, `drop_unknown`, `skip`). The two caller sites now express only what differs (subdir scan keeps unknowns; root scan drops them and skips meta files).

## 6. Docs vs source — source-of-truth boundary

The manifest module (`src/ai_lsc/manifest/support.py`) and the routing layer file (`src/ai_lsc/registry/layers/routing.py`) now both carry explicit "source of truth" docstrings:

> The manifest file itself is an optional convenience; if absent, callers fall back to defaults — the registry layer files in `ai_lsc.registry.layers` remain the authoritative source for tool definitions.

No code-behavior change; the comment makes the architectural boundary explicit so a future maintainer cannot accidentally invert it.

## 7. Verification

| Check | Result |
|---|---|
| AST-parse 100 Python files | **0 failures** |
| `bash -n` on bootstrap.sh + run.sh | **0 failures** |
| Refactored modules import cleanly | **OK** |
| `build_system_context` smoke test | **OK** (dispatch table produces identical output) |
| `resolve_context_files` smoke test | **OK** (returns same file list) |
| Wording sweep grep | **0 matches** for `restored|brought back|related logic` |

## 8. Out-of-scope (preserved per user policy)

- `curl|sh` installers (Ollama, Grafana Alloy, Meilisearch) — C-05 policy (see `whatremains.txt`).
- Layer-file `filesystem` backfill (L-18) — mechanical, ~10 min/layer.
- `defaults.py` 3700-line split (L-14) — conflicts with layer-file decomposition.
- Pre-existing unused imports `JCL_FILE_NAME` (support.py) and `Path` (installer.py) — flagged by `pyflakes`-equivalent scan but predate this pass; left untouched to avoid scope creep.

## 9. Tarball

Packaged as `ai-lsc-moe-qa-pass.tar.gz` in `/home/z/my-project/download/`. Contains the full project tree post-cleanup.
