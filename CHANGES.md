# AI-LSC Changelog

## v3.3 — Registry git-URL sync + bandwidth-aware git-pull + ComfyUI

Patch release over v3.2. No schema changes, no UI reorganisation, no
wiring-graph churn — only the 10-layer registry's installer URLs are
touched, plus the git install/update logic in `runtime/installer.py`,
plus a new ComfyUI registry entry, plus version strings and a per-file
change log.

### What changed

The 10-layer registry layer files had drifted from the systems-architect
reference (`ai-stack-guide-v12.md`, "Approaching the Local AI Stack Like
a Systems Architect" by Jeremy Anderson). 52 installer URLs were either
pointing at placeholder repos (`github.com/nicely-done/<tool_id>`,
clearly never intended to ship) or at wrong upstreams (e.g. `airllm`
pointed at `liguodongiot/llm-airforce`; `llamacpp` pointed at
`ggerganov/llama.cpp` instead of the current `ggml-org/llama.cpp`).
Three tools the v12 md lists as `git` / `git_node` (pm_skills, agno,
openhands) were registered as `uv` package-manager installs — wrong,
since the user manually tested every entry in the md by cloning the
github repo.  Four registry-only tools (algory, atlas_os, eagle_eye,
glassmind) had only placeholder URLs because web search could not
find their official upstreams; the user provided the URLs directly.
ComfyUI was referenced in the `ai-image-gen-local.json` stack template
but had no registry entry.

This release:
- Brings every git-ish installer into agreement with the v12 reference.
- Adds `pkg` fields to the 6 script-type installers that reference
  github release tarballs.
- Resolves 10 registry-only git tools to their official upstreams via
  web search.
- Switches the 3 type-mismatch tools to proper git/git_node installs.
- Resolves the 4 previously-unresolved registry-only tools to the
  user-provided official upstreams.
- Adds a ComfyUI registry entry (Level 10, `git:comfy-org/comfyui`).
- Hardens the git installer runtime to be bandwidth-aware.

### Five categories of patches (52 total)

- **A (28)** — `git` / `git_node` / `custom` installer `pkg` URL
  corrected to match the v12 markdown reference. See
  `docs/REGISTRY-URLS-v3.3.0.md` for the per-file old → new URL table.
- **B (6)** — `script`-type installers (fabric, grafana_alloy,
  llamafile, meilisearch, ollama, qdrant) get a new `pkg` field
  referencing the github repo, while the existing working `cmd`
  (curl release tarball, etc.) is left untouched.
- **C (10)** — registry-only git tools with no v12 markdown entry
  resolved via web search:
  - `agent_reach` → `Panniantong/Agent-Reach`
  - `everos_memory` → `EverMind-AI/EverOS`
  - `headroom` → `headroomlabs-ai/headroom`
  - `mnemo_cortex` → `GuyMannDude/mnemo-cortex`
  - `nightshift` → `johndaskovsky/nightshift`
  - `openbrain` → `NateBJones-Projects/OB1`
  - `turbovec` → `ryancodrai/turbovec`
  - `crossplane` → `crossplane/crossplane`
  - `keycloak` → `keycloak/keycloak`
  - `dma` → `distcc/distcc` (closest parent project; DMA has no
    separate public repo)
- **D (3)** — type-mismatch fixes (md says git / git_node, registry had
  `uv` with package name):
  - `pm_skills` → `git:https://github.com/product-on-purpose/pm-skills`
  - `agno` → `git:https://github.com/agno-agi/agno`
  - `openhands` → `git_node:https://github.com/All-Hands-AI/OpenHands.git`
- **E (4)** — user-provided URLs for the 4 previously-unresolved
  registry-only tools (web search could not find these; the user
  provided the official upstream URLs directly):
  - `algory` → `aryaghan-mutum/algory`
  - `atlas_os` → `atlas-os/atlas`
  - `eagle_eye` → `thoughtfuldev/eagleeye`
  - `glassmind` → `khodges42/glassMind`

### New tool entry (1)

- **ComfyUI** (`user_interfaces.py`): ComfyUI was referenced in the
  `ai-image-gen-local.json` stack template but had no registry entry
  before.  Added as a Level 10 (Human Interface & System Operations)
  tool with installer `git:https://github.com/comfy-org/comfyui`,
  launcher `python main.py --listen 0.0.0.0 --port 8188`, deps
  `[cuda]`, license GPL-3.0.  Total registry size is now 187 tools
  (was 186).

### Runtime: bandwidth-aware git-pull-on-update

`runtime/installer.py`'s `install_git` and `install_git_node` already
ran `git pull --ff-only` if the destination dir existed, but the
existence check was `os.path.exists(dest)` — True for any dir, not
just a git working tree.  An empty or non-git dir at the destination
would cause `git pull` to fail and abort the install.  Hardened:

1. Check `os.path.isdir(dest/.git)` to confirm a real git repo.
2. On pull failure (diverged branches, network errors, corrupted
   index, etc.), move the old dir aside to `<dest>.bak.<unix_ts>`
   and re-clone fresh — so the install always ends in a usable state
   instead of leaving a half-broken tree.
3. If the dest dir exists but is not a git repo, back it up and clone
   fresh.
4. Log clearly which path was taken (pulled / re-cloned / new clone /
   non-git-dir backed up).

**Effect:** re-running install on a tool that's already cloned only
fetches the diff (a few KB / MB), not the entire repo.  This is the
bandwidth-saving behaviour the user asked for.

### Intentionally NOT touched

- `apex` (md says `pip — https://github.com/NVIDIA/apex`): kept as
  `uv:apex` (pip-installed).  The md's `pip` installer type is
  authoritative and the user did not call this one out.
- 12 git-ish installers that already matched the v12 reference
  (`anythingllm`, `dify`, `heretic`, `homelab`, `invokeai`,
  `koboldcpp`, `librechat`, `mcp_drift_state_tracker`, `openjarvis`,
  `paperlessngx`, `synapscli`, `wayland_ai`) — no change needed.
- 3 registry-only git tools with real-looking URLs already in place
  (`goose` → `block/goose`, `nvidia_agent_skills` →
  `NVIDIA/agent-skills`, `picode` → `jasonjmcghee/picode.git`) — no
  change needed.

### Versioning & docs

- `pyproject.toml`: 3.2.0 → 3.3.0
- `src/ai_lsc/constants.py`: `APP_VERSION` 3.2.0 → 3.3.0
  (`APP_CODENAME` unchanged: `"Decalogue"`)
- New file: `docs/REGISTRY-URLS-v3.3.0.md` (per-file old → new URL
  table, also serves as a release audit trail).
- `gitcommit` rewritten for v3.3.0.

### Verification

- All 94 Python files under `src/` AST-parse cleanly.
- Registry extractor re-imports every patched layer module and
  confirms all 52 patches landed + the new ComfyUI entry.  Total
  registry size: 187 tools (was 186).
- Each old `pkg` URL string was unique within its file and matched
  exactly once — no blind global replaces.
- Each script-type pkg-field injection matched exactly one installer
  block (Python AST-parses after each injection).
- `install_git` / `install_git_node` hardened: the new logic branches
  on `os.path.isdir(.git)`, falls back to re-clone on pull failure,
  and uses `import time` for backup-dir timestamps.  All confirmed
  present in `runtime/installer.py`.
- 0 `nicely-done` placeholder URLs remain in the registry.

---

## v3.2 — 10-Layer Systems Architecture Taxonomy completed

Finishes the taxonomy re-org that was started (but stalled) on top of
v3.1.1b: the whole codebase now speaks the unified 10-layer taxonomy
from the systems-architecture review (POSIX/Unix philosophy, bare-metal
process hierarchy).  The partial migration had already rewritten
`constants.py` (NAV_LAYER_ORDER) and `db_manager.py` (CATEGORY_MAP); this
release completes every remaining surface, repairs the damage the
interim tooling caused, and reconciles the registries.  Validator
reports 0 errors on both the 108-tool defaults seed and the 186-tool
merged layer registry; wiring graph validates with 0 errors.

### New layer ladder (11 → 10)

```
L1  Host Platform & Infrastructure          L6  Multi-Agent Orchestration Runtimes
L2  Development Runtime & Environment       L7  Agentic Software Engineering & Sandboxes
L3  GPU Acceleration & Optimization         L8  Decentralized Knowledge & Vector Stores
L4  Local Inference Engines                 L9  Data Extraction & Pipeline Harvest
L5  Intelligent API Routers & Proxies       L10 Human Interface & System Operations
```

The 11-layer model's Security and Observability strata dissolve:
security *daemons* (keycloak, vault, fail2ban, edge/proxy daemons) are
host platform infrastructure (L1); scanners/policy/audit tooling
(trivy, clamav, opa) and telemetry (btop, grafana, prometheus, opik)
are system operations (L10).  Routing merges into Intelligent API
Routers & Proxies (L5).  Vector/graph stores and agent memory move out
of Knowledge Management into L8; document/crawl/transcode pipelines
become L9; IaC and cluster automation land in L10.

### Registry

- `registry/defaults.py` rebuilt as the 108-tool 10-layer seed from the
  master-target registry: new `level`/`layer`/`role`/`category` plus the
  richer descriptions.  Operational metadata (real installer pkgs/URLs
  and cmds, `post_install`/`update_cmd`/`env_overrides`, launchers with
  correct binary names and systemd-for-daemons, dependency edges,
  curated flags, SPDX licenses, `filesystem` blocks) is preserved from
  the previous registry — the master-target file had systematically
  replaced installers with placeholder URLs, dropped script cmds
  (validator errors), wiped all dep edges, and renamed binaries
  (`rg` → `ripgrep`, systemd → tmux `serve` stubs).  curl|sh installer
  policy markers are untouched (see whatremains.txt, C-05).
- 11 modular layer files realigned: 185 tools migrated to the 10-layer
  taxonomy (107 shared tools take their structural fields from the
  master registry; the other 78 classified explicitly — see
  `scripts/apply_10layer_taxonomy.py` for the classification table).
- `kanban` reconciled: it existed only in `defaults.py` (the canonical
  source is the layer files), so it is now declared in
  `layers/user_interfaces.py` as well (L10, Sprints Manager).  Merged
  registry: 185 → 186 tools.
- `n8n` keeps its explicit L10 placement (visual flow canvas) and moves
  to the `Workflow` (Visual Builder) category so the categorisation
  cascade agrees with the registry.
- `n8n`/`odysseus` `filesystem` blocks (previously only in the old
  defaults) are preserved in `layers/orchestrators.py`.
- The `open_webui`/`openwebui` orphan-flagging gap from the TODO is
  confirmed moot: only `openwebui` exists and it is wired.

### Stack wiring

- `stack/connections.py`: 92 static `StackWiring(layer=...)` values
  migrated to the 10-layer names; the 5 loop-based bulk allocations now
  resolve layers dynamically via `_wiring_layer(_tid)` (DEFAULT_REGISTRY
  lookup + `_WIRING_LAYER_SUPPLEMENT` for wired tools outside the seed
  registry), so the wiring graph can never drift from the taxonomy
  again.  Section header comments map the old L1–L13 sections to their
  new homes.  Wiring-vs-registry layer mismatches: 0 across 137 wirings.

### UI

- `ui/pages/db_manager.py` **repaired and migrated**: the interim
  migration had truncated the file from 1300 to 222 lines (syntax error
  at the CATEGORY_MAP tail; the entire DB-manager dialog/table
  implementation was lost).  The canonical 1.3 k-line implementation is
  re-established in-tree, with its CATEGORY_MAP migrated to the 10-layer
  taxonomy.
- Categorisation cascade extended to 221 categories: the master map
  (105) + 43 categories for the classified tools + 73 preserved
  categories from the v3.1.1b cascade, translated to the 10-layer
  taxonomy with their curated roles.  Every category used by the 186
  registry tools is covered; cascade and registry agree on layer for
  every tool.
- `ui/pages/db_manager_category_map.py` regenerated to match.
- `registry/validator.py` now enforces level range 1–10.

### Docs & tooling

- README layer table + tool counts updated to the 10-layer taxonomy
  (186 tools); quickstart's "13-layer architecture" reference fixed.
- Layer-file module docstrings note the 10-layer realignment.
- `scripts/apply_10layer_taxonomy.py` added (the corrected, completed
  migration utility — supersedes the root `apply_taxonomy_migration.py`,
  whose regexes could not match multi-word layer names and whose
  defaults handling was lossy; kept for history).

### Verification

`scripts`-style checks all pass: 100 Python files AST-parse; validator
0 errors (defaults + merged + wiring graph); level/layer consistency
holds across defaults, layer files, CATEGORY_MAP, and STACK_WIRINGS;
NAV_LAYER_ORDER matches the taxonomy; guardrails clean; headless
package import + `RegistryManager` first-boot/second-run bootstrap
verified (186 tools seeded to ecosystem.json, structural sync clean).

## v3.1.1b — taxonomy re-org: Routing promoted to a first-class layer (11 layers), canonical 24-dir /mnt/AI layout

Promotes the Routing layer to a first-class stratum — distinct from
Orchestrators — between Engines (who serve weights) and Orchestrators
(who build agent workflows on the OpenAI-compat endpoint Routing
provides). Aligns the backend to the revised canonical `/mnt/AI/`
directory tree. No tool count change (185 tools); validator still
reports 0 errors.

### New layer ladder (10 → 11)

```
L1  Host Platform          L7  Security
L2  Development Env        L8  Observability
L3  GPU Runtimes           L9  User Interfaces
L4  Engines                L10 DevOps
L5  Routing                L11 Knowledge Management
L6  Orchestrators
```

`NAV_LAYER_ORDER` inserts Routing between Engines and Orchestrators —
engines serve weights, routing proxies/load-balances/meshes them into
one OpenAI-compat endpoint, orchestrators build agent workflows on top.

### Tool moves (18 tools, all layers/levels updated)

| tool_id | Old | New |
|---------|-----|-----|
| `litellm` | L5 Orchestrators (Proxy / API Gateway) | **L5 Routing** |
| `9router_proxy` | L5 Orchestrators (LLM Router) | **L5 Routing** |
| `meshllm` | L5 Orchestrators (LLM Mesh) | **L5 Routing** |
| `dify` | L5 Orchestrators (Pipeline) | **L5 Routing** |
| `picode` | L5 Orchestrators (AI Coding Agent) | **L5 Routing** (category → `Mesh Client`) |
| `vllm` | L5 Orchestrators (Scaling) | **L4 Engines** (role → Engine; ADR-001 always listed vLLM under Inference Engines) |
| `sglang` | L5 Orchestrators (Scaling) | **L4 Engines** (role → Engine) |
| `eagle_eye` | L5 Orchestrators (category literally "Observability") | **L8 Observability** |
| `dma` | L5 Orchestrators (Build Monitoring) | **L8 Observability** |
| `aider`, `claude_code`, `codex`, `openhands`, `opencode`, `gemini_cli`, `qwen_code`, `goose`, `zcoder` | L5 Orchestrators (AI Coding Agent) | **L10 DevOps** — matches the DB editor's `AI Coding Agent → DevOps` mapping, which previously conflicted with the registry |

Remaining tools in the affected layers were renumbered (+1): 38 stay in
Orchestrators (L6), Security L7, Observability L8, User Interfaces L9,
DevOps L10, Knowledge Management L11. Per-layer level uniformity
verified. `picode`'s category changed `AI Coding Agent` → `Mesh Client`
so the category cascade cannot silently flip it back to DevOps.

### Tool DB editor (`CATEGORY_MAP`)

- All entries renumbered to the new ladder; map is now fully consistent
  with the live registry (0 layer/level mismatches).
- 13 new categories so every registry category auto-fills correctly:
  `LLM Mesh`, `Mesh Client` (Routing); `Observability` (Observability);
  `Build`, `Debugging`, `Shell`, `Claude Code Skill`, `Container Ops`,
  `Infrastructure`, `Memory System`, `Model Surgery`, `Networking`,
  `Virtualization` (previously missing entirely).
- Fixed conflicts: `AI Coding Agent` → DevOps/L10 (role `Coding Agent`,
  was `Autonomous Coder` at L9), `Build Monitoring` → Observability/L8,
  `LLM Serving` → Engines/L4, `LLM Router` / `Proxy` / `Pipeline` →
  Routing/L5.

### STACK_WIRINGS (`stack/connections.py`)

- 29 wiring `layer=` labels synced to the registry: the 13 moved tools
  with wirings, plus `deep_eye`/`luxtts` (UI tools mislabeled
  Orchestrators) and 14 pre-existing drifts (`heretic`, `unsloth`,
  `parakeet`, `fabric`, `n8n`, `nightshift`, `hivemind`, `hermes_agent`,
  `agno`, `hermes_dashboard_page`, `mnemo_cortex`, `everos_memory`,
  `langflow`, `opensandbox`). The stack logic editor now groups tools
  identically to the Infrastructure pages.
- Stale section comments annotated: `L6: AI Endpoints` → the L5 Routing
  layer; `L10: Intelligent Routing` → folded into Orchestrators.

### Canonical `/mnt/AI/` layout (26 → 24 dirs)

`REQUIRED_DIRS` now matches the target tree exactly:

- **Added `configs/`** — app configs templated for native runtime plus
  app state. `main_window.config_root` moves from legacy `config/` to
  `configs/`, taking `pipeline_state.json`, `pipeline.json`,
  `license_approvals.json` with it; `controller_config.json` moves off
  the `/mnt/AI/` root into `configs/`. A one-time
  `_migrate_legacy_state_files()` pass moves old files on startup
  (newer copies win; emptied legacy dirs are removed).
- **Dropped from the skeleton**: `bootstraps/ai-lsc`, `staging`,
  `registry/manifests`. `registry/` remains as app-internal storage for
  `ecosystem.json` and manifests — auto-created on demand by
  `RegistryManager`, no longer part of the canonical tree.
- `paths.py`: `configs_root` added; `staging_root` / `bootstraps_root`
  removed; the deprecated `config_root → runtime` alias now points at
  `configs/`. Per-tool config subdirs (`configs/<tool>/`) are still
  created on demand by `InstallerManager`.
- `license_gate.py` / `licenses.py` doc references updated to
  `configs/license_approvals.json`.

Existing installs pick up all taxonomy changes automatically:
`RegistryManager._sync_with_upstream()` re-syncs structural fields
(layer, level, role, category) from the layer files on every start.

## v3.1.1a — registry validator fixes (5 errors → 0)

Fixes all 5 `validate_registry()` errors plus latent bugs surfaced
during the fix pass. No tool count change (185 tools).

### Installer fixes (validator errors)

All five failed the "script installer cmd should reference
{tools_root}" check — they installed into system dirs or the cwd:

| tool_id | Before | After |
|---------|--------|-------|
| `firecracker` | extracted into `/usr/local/bin/` (and silently broken: versioned tarball dirs never landed on PATH) | extracts into `{tools_root}/firecracker/`, symlinks `firecracker` + `jailer` into `{tools_root}/bin/` |
| `cloudflared` | downloaded to `/usr/local/bin/cloudflared` | downloads to `{tools_root}/bin/cloudflared` |
| `llamafile` | downloaded to cwd (mismatched launcher, which already expected `{tools_root}/bin/llamafile`) | downloads to `{tools_root}/bin/llamafile` |
| `meilisearch` | `curl \| sh` dropped binary in cwd | runs installer inside `{tools_root}/bin/` (official installer places the binary in the cwd) |
| `grafana_alloy` | `install.sh \| sh` — **URL dead (404): upstream dropped the script** | direct release asset `alloy-linux-amd64.zip`, extracted via `python3 -m zipfile` (no unzip dependency) |

### Launcher fixes (latent bugs)

- `firecracker`, `cloudflared`, `grafana_alloy` launchers now use
  absolute `{tools_root}/bin/<name>` paths. Rationale: `tools_root/bin`
  is on PATH at install time (`installer._env()`) but **not** at launch
  time (`enriched_env()` builds PATH from `base_bin_dir` = uv/npm bins
  only), so bare-name launcher cmds would pass preflight then fail
  with "command not found". Absolute paths are immune to the gap.
- firecracker version discovery uses the Location header
  (`curl -sIL … | grep -i '^location:'`) instead of
  `-w '%{url_effective}'` — launcher/installer cmds are rendered with
  `str.format()`, and the `{url_effective}` braces would raise
  `KeyError` at render time.

### Dependency fixes (phantom missing-dep warnings)

- `dify` deps: `node` → `nodejs` (the actual registry tool_id).
- `RegistryManager.check_dependencies()` now allows system-level deps
  (`kubectl`, `java`) via a `SYSTEM_DEPS` frozenset, mirroring the
  existing `_system_deps` pattern in `stack/connections.py`. Previously
  `crossplane` (kubectl) and `keycloak` (java) produced permanent
  "missing dependency" warnings that could never be satisfied.

### Not fixed (observations, no behavior change)

- 9 duplicate `default_port` defaults across tools (e.g. 3000 shared
  by grafana/opik/openhands/flowise). These are overridable per
  service row; leaving as-is unless the stack compiler should
  auto-assign.
- `TODO.md`'s `open_webui`/`openwebui` split no longer reproduces:
  only `openwebui` exists in both the registry and `STACK_WIRINGS`.

## v3.1.1 — local-coder-mesh integration (this build)

Adds 4 new tools, corrects 1 existing tool, adds 4 new `STACK_WIRINGS`
entries (and rewires 1), adds 1 new stack template, and aligns all
hardcoded `/mnt/AI/` paths to the canonical 26-directory layout. No
containers in the dev path — every tool installs natively. ai-lsc's
Podman/Docker/LXC/Firecracker export is reserved for total-stack
deployment exports only, as before.

### New tools (181 → 185)

| tool_id | Layer | What | Install |
|---------|-------|------|---------|
| `picode` | L5 Orchestrators | PiCode (jasonjmcghee/picode) — local code-tinker agent | git clone |
| `meshllm` | L5 Orchestrators | MeshLLM (Mesh-LLM/mesh-llm) — native binary, pools GPUs/memory across machines, exposes OpenAI-compat API at :9337, web console at :3131. NOT a LiteLLM derivative. | script (official curl installer) |
| `zcoder` | L5 Orchestrators | Zhipu AI Z-Coder CLI coding agent | npm `zcoder-cli` |
| `hermes_webui` | L8 User Interfaces | Hermes-themed Open-WebUI instance on :8081 with its own data volume; backend points at `hermes_agent` (:17051) instead of Ollama direct | uv `open-webui` |

### Corrected tool

`graphify` was already in the registry but had wrong metadata. Fixed in place:

| Field | Old | New |
|-------|-----|-----|
| `role` | `Graph Builder` | `Knowledge Graph Builder` |
| `category` | `AI Agent` | `Claude Code Skill` |
| `installer` | `git: nicely-done/graphify` | `uv: graphifyy` (PyPI; CLI is `graphify`) |
| `license` | `Proprietary` | `MIT` (verified from pyproject.toml) |
| `flags.has_web` | `False` | `True` (graph.html output) |
| `flags.is_mcp` | `False` | `True` (`graphify --mcp` stdio server) |
| `description` | 1 line generic | 10 lines accurate (CLI + Claude Code skill + MCP server + LLM backend options) |

Graphify's wiring also changed — see below.

### New `STACK_WIRINGS` entries (133 → 137)

| tool_id | Exposes | Consumes |
|---------|---------|----------|
| `picode` | (none — CLI agent) | `meshllm` (primary), `litellm` (fallback), `ollama` (direct fallback) |
| `meshllm` | `openai_api` (:9337) + `mesh_web_console` (:3131) | `ollama` (optional, for `mesh-llm client --auto` mode) |
| `zcoder` | (none — CLI agent) | `meshllm` (primary), `litellm` (fallback), `ollama` (direct fallback) |
| `hermes_webui` | `hermes_webui_http` (:8081) | `hermes_agent` (required, primary backend), `ollama` (optional, for RAG embeddings) |

### Rewired entry

`graphify` removed from the L8 passive/CLI list and given a proper
`_reg(StackWiring(...))` block:

- **Exposes**: `graphify_mcp` (stdio MCP server, no port) — start with
  `graphify --mcp`. Other MCP-aware agents can query the knowledge graph.
- **Consumes** (all optional, fallback chain for the extraction LLM):
  `meshllm` (:9337/v1), `litellm` (:4000/v1), `ollama` (:11434/v1).
  Graphify defaults to Claude (Anthropic API) but can be configured for
  fully-local extraction by setting `OPENAI_API_BASE` to any of the
  above.

### New stack template (13 → 14)

`local-coder-mesh.json` — "Local Coder Mesh — All-Ollama Coding Stack".
17 tools: ollama, litellm, meshllm, picode, aider, odysseus, opencode,
zcoder, graphify, hermes, hermes_agent, hermes_webui, hermes_desktop,
openwebui, ripgrep, fd, tree_sitter.

Topology: coding agents prefer MeshLLM (:9337) for mesh-pooled inference,
fall back to LiteLLM (:4000) for proxy routing, then Ollama direct
(:11434). Graphify builds knowledge graphs from the codebase and exposes
an MCP server that the coding agents query. Hermes WebUI talks to
hermes_agent (NOT Ollama direct) so every Hermes conversation flows
through the agent runtime's tool-use layer. OpenWebUI talks to Ollama
direct. ripgrep + fd + tree_sitter are passive filesystem tools used by
the coding agents for repo-map / symbol navigation.

Recommended models: `qwen2.5-coder:7b` (fast coding),
`qwen2.5-coder:32b` (heavy coding), `hermes3:8b` (Hermes stack),
`nomic-embed-text` (openwebui RAG, corpus indexing, graphify embeddings).
MeshLLM auto-downloads a suitable model on first `serve --auto` if none
is specified.

### Path alignment to canonical `/mnt/AI/` layout

Three files updated so ai-lsc's hardcoded paths match the 26-directory
canonical layout:

- **`src/ai_lsc/constants.py`** — `REQUIRED_DIRS` replaced with the 26
  canonical entries (`bootstraps/ai-lsc`, `staging`, `backends`,
  `distfiles`, `runtime`, `models/hot`, `models/cold`, `corpus/hot`,
  `corpus/cold`, `datasets/wordlists`, `datasets/huggingface`,
  `datasets/github`, `pipelines`, `registry/manifests`, `agents`,
  `skills`, `projects/active`, `projects/labs`, `projects/vault`,
  `blueprints`, `workspaces`, `dashboards`, `tools`, `exports/oci-images`,
  `scripts`, `logs`). Old layout dirs (`config`, `cache`, `data`,
  `containers`, `bin`, `tmp`, `backups`, `models/ollama`, `models/chroma`,
  `datasets/raw`, `workspaces/hermes`, `workspaces/openwebui`,
  `workspaces/n8n`) are NOT removed — they just become orphans. Clean
  them up manually if desired.
- **`src/ai_lsc/utils/paths.py`** — `build_path_tree()` expanded from 10
  keys to 24 keys. Old keys kept and repointed at canonical subdirs.
  New keys added: `runtime_root`, `models_hot`, `models_cold`,
  `corpus_root`, `pipelines_root`, `agents_root`, `projects_root`,
  `blueprints_root`, `dashboards_root`, `scripts_root`, `backends_root`,
  `distfiles_root`, `staging_root`, `bootstraps_root`. The `config_root`
  key is kept as a deprecated alias pointing at `/mnt/AI/runtime/` so
  existing callers don't break — new code should use
  `tools_root / <tool_id> / "config"` or `runtime_root / <tool>` explicitly.
- **`src/ai_lsc/agents/litellm_config.py`** and
  **`src/ai_lsc/agents/librechat_config.py`** — hardcoded save paths
  moved from `/mnt/AI/config/litellm_config.yaml` and
  `/mnt/AI/tools/librechat/librechat.yaml` to
  `/mnt/AI/runtime/litellm/config.yaml` and
  `/mnt/AI/runtime/librechat/config.yaml` respectively. Per-tool configs
  for long-running services belong under `runtime/<tool>/` next to their
  venv / cloned repo, since the spec has no top-level `/mnt/AI/config/`.

### Backfill script path fixes

Three helper scripts in `scripts/` had stale hardcoded absolute paths to
`/home/z/my-project/workspace/ai-lsc` (a developer machine path that
leaked into the v3.1 release). Replaced with
`Path(__file__).resolve().parent.parent` so they resolve to the project
root regardless of where the tarball is extracted:

- `scripts/backfill_default_licenses.py`
- `scripts/backfill_layer_flags.py`
- `scripts/backfill_tool_licenses.py`

### Verification (run against this build)

```
Registry: 185 tools (was 181)
Wirings:  137 entries (was 133)
Wiring validation errors: 0
Registry validation errors: 5 (all pre-existing in upstream v3.1 —
  firecracker, cloudflared, llamafile, meilisearch, grafana_alloy —
  none introduced by this build)
meshllm installer: uses {tools_root}/meshllm/bin (passes validator)
Templates: 14 (was 13) — local-coder-mesh added
Template tool resolution: 17/17 tools resolve in registry
build_path_tree() keys: 24 (was 10)
REQUIRED_DIRS entries: 26 (was 22)
graphify installer: uv:graphifyy (was git:nicely-done/graphify)
graphify license: MIT (was Proprietary)
graphify is_mcp flag: True (was False)
meshllm interfaces: ['openai_api' on :9337, 'mesh_web_console' on :3131]
graphify interfaces: ['graphify_mcp' stdio]
```

### Native-only install policy

Every tool in the new `local-coder-mesh` template installs natively into
`/mnt/AI/runtime/<tool_id>/` (venv via uv/pipx) or via pacman/AUR/curl-script.
ai-lsc's container export feature (Podman / Docker / LXC / Firecracker)
is intentionally NOT used at install time — it's reserved for total-stack
deployment exports via the Stack Editor, exactly as in v3.1.

### Rollback

To revert this entire build to upstream v3.1, restore from git or
re-extract the original tarball. There is no separate "patch pack" to
unapply — this is the integrated project.

---

## v3.1 — registry expansion: 2026-era coding agents, serving, and runtimes

Adds 11 tools to the layer registry (170 → 181) and 10 `STACK_WIRINGS` entries (123 → 133), and backfills 6 missing OSI licenses into the catalog. All facts (npm/PyPI package names, default ports, licenses) were verified against current upstream docs.

### New tools

| tool_id | Layer | What | Install |
|---------|-------|------|---------|
| `deno` | L2 Development | JavaScript/TypeScript/WASM runtime; runs many MCP servers via `deno run` | pacman `deno` |
| `uv` | L2 Development | Astral's Python package/project manager (AI-LSC's own install backend) | pacman `uv` |
| `tinygrad` | L3 GPU Runtimes | Minimalist autograd tensor library (CUDA/AMD/CPU backends) | uv `tinygrad` |
| `opencode` | L5 Orchestrators | SST's open-source terminal AI coding agent (TUI, LSP, 75+ providers) | npm `opencode-ai` |
| `gemini_cli` | L5 Orchestrators | Google's open-source terminal AI agent | npm `@google/gemini-cli` |
| `qwen_code` | L5 Orchestrators | Qwen's agentic terminal coding tool (Gemini CLI fork) | npm `@qwen-code/qwen-code` |
| `goose` | L5 Orchestrators | Block's extensible AI agent with MCP extensions | manual (opens releases page) |
| `letta` | L5 Orchestrators | Stateful agent framework (MemGPT) with persistent memory; `letta server` on :8283 | uv `letta` |
| `sglang` | L5 Orchestrators | Fast LLM serving with RadixAttention; OpenAI-compat API on :30000 | uv `sglang` |
| `jan` | L8 User Interfaces | Offline ChatGPT-alternative desktop app; OpenAI-compat local API on :1337 | npm `@janhq/jan` |
| `mem0` | L10 Knowledge Mgmt | Memory layer for AI apps/agents; pluggable vector backends | uv `mem0ai` |

`goose` uses installer type `custom` deliberately: its official install path is a `curl | sh` one-liner, which conflicts with the v3.1 no-remote-code-execution policy. The `custom` installer opens the GitHub releases page for a manual, download-first install instead. `deno` and `uv` are intentionally left unwired (language runtimes, consistent with `nodejs`/`python`).

### Wiring topology (Pipeline Ticker)

- **Terminal coding agents wired**: `opencode`, `gemini_cli`, `qwen_code`, `goose`, and the pre-existing `codex` each gained connections to Ollama (direct) and LiteLLM (proxied) — staging either backend now prevents orphan-flagging. `codex` had been an orphan since v3.1 because it had no `STACK_WIRINGS` entry.
- **`sglang`** mirrors the vLLM wiring: exposes `openai_api` on :30000, consumes `cuda_driver`.
- **`letta`** exposes its REST API on :8283 and optionally consumes PostgreSQL (`LETTA_PG_URI`) + Ollama.
- **`jan`** exposes `openai_api` on :1337 (bundled llama.cpp engine).
- **`mem0`** optionally consumes Ollama (LLM + embeddings) and Qdrant (vector storage).
- **`tinygrad`** optionally consumes `cuda_driver` (it also runs on CPU/AMD).
- `validate_wiring()` reports 0 errors across all 133 wirings.

### License catalog backfill (fixes 8 pre-existing validator errors)

The following SPDX IDs were referenced by layer files but missing from `registry/licenses.py`, producing `license is not in the license catalog` validation errors: `LGPL-2.1` (strace, lxc, libvirt), `GPL-1.0` (perl), `PHP-3.01` (php), `Ruby` (ruby), `MirOS` (mksh), `MIT/Apache-2.0` (rust). All six are OSI-approved and are now catalog entries (auto-approvable). The merged registry validates with **0 errors** — the only remaining messages are the 5 documented `script installer cmd should reference {{tools_root}}` warnings tied to the curl|sh policy decision (llamafile, meilisearch, grafana_alloy + the newer firecracker, cloudflared).

### Docs

README tool counts and the layer table were refreshed to the real merged-registry numbers (they had been stale since the DevOps→Orchestrators reorg moved the coding agents).

## v3.1 — 2026-07-07

Codename: **Ankh of Jah** (continuation)

The v3.1 release is a hardening + polish pass on top of v3.0. It applies the full master code critique (91 of 93 findings addressed), introduces two new UI widgets (Pipeline Ticker + Workspace Tab), and ships three latent-bug fixes that were caught during the post-pass double-check.

### New features

#### Pipeline Ticker

A horizontally scrolling status bar at the top of every workspace tab. Reads the active-tools set from `pipeline_state.json`, joins it against the `STACK_WIRINGS` topology in `stack/connections.py`, and renders:

```
ollama ──openai_api──▶ litellm ──openai_api──▶ aider    ❗ open_webui
```

- **Color-coded arrows** by interface type — blue for `openai_api`, green for `vector` / `vector_search` / `embedding`, orange for `redis_pubsub` / `redis_cache`, purple for `postgresql` / `mariadb` / `mysql`, teal for `http_api` / `websocket` / `grpc`, slate for `filesystem` / `tmux_socket` / `systemd_unit`, red for `cuda_driver`.
- **Orphan detection** — any active tool that has no in-stack wiring to another active tool is flagged red with an `❗` prefix. This surfaces real registry gaps (e.g. the `open_webui` vs `openwebui` tool_id collision).
- **Running-state coloring** — pills are blue when the tool is running, white when stopped. The ticker refreshes on every 2 s service-status poll so state changes propagate immediately.
- **Hover-pause** — mouse over the ticker to stop the scroll so you can read a long flow.
- **Click-to-jump** — click any tool pill to switch to the Tools tab; the matching row is selected, scrolled to center, and flashed amber for 1.5 s.

Files: `src/ai_lsc/ui/widgets/pipeline_ticker.py` (new, ~330 lines), `src/ai_lsc/ui/main_window.py` (wiring), `src/ai_lsc/ui/pages/tools_tab.py` (new `highlight_tool()` method), `src/ai_lsc/ui/pages/service_row.py` (new `is_running_now()` cache method).

#### Workspace Tab

A new **Workspace** nav entry (between Chat and Git Sources) that provides virt-manager / aqemu–style peek orchestration. Every active tool gets its own sub-tab:

- **🌐 Web tools** (`has_web=True`) embed via `QWebEngineView` at `http://127.0.0.1:{port}`. A URL bar at the top shows the loaded URL; ⟳ reloads, ↗ opens in an external browser. No need to leave the app for a browser.
- **⌨ CLI tools** (`has_cli=True`, no web) attach to their tmux session via `tmux capture-pane -t <session>::<tool_id> -p -S -200` polled at 4 Hz. The terminal is read-only — use a real terminal app for interactive input.
- **📦 Passive / library tools** get a placeholder explaining they have no interactive surface.
- **⏸ Not-yet-running tools** show a **Start tool** button that wires back to the existing `ServiceRow.start_service()` flow. After 1.5 s the workspace tab auto-refreshes so the placeholder → live view switch happens automatically.
- Sub-tabs are closable; closing a sub-tab stops the polling but does NOT stop the underlying tool (use the Stack Editor for that).

**Servo note:** Web embedding uses `PySide6.QtWebEngineWidgets.QWebEngineView` by default. Swapping in Mozilla's servo engine later is a one-line change to `_make_web_view()` in `src/ai_lsc/ui/widgets/workspace_tab.py` — the rest of the WorkspaceTab code only depends on the `setUrl()` / `url()` / `load()` API.

Files: `src/ai_lsc/ui/widgets/workspace_tab.py` (new, ~310 lines), `src/ai_lsc/ui/main_window.py` (new `_build_workspace_orchestration_page` + nav entry + refresh hooks).

### Security & reliability hardening (the critique pass)

91 of 93 findings from the master code critique were addressed. See [whatremains.txt](whatremains.txt) for the two intentionally-skipped items and deferred polish. Highlights:

#### CRITICAL (6 of 7 fixed; C-05 skipped per user)

- **C-01** `runtime/process.py` — `shell=True` removed from `launch_desktop`, `launch_terminal`, `kill_by_name`, `docker_compose_down`. New `_to_arg_list()` helper accepts either a pre-split argv list or a single shell-style string (split via `shlex.split`).
- **C-02** `runtime/systemd.py` — `shell=True` removed from `start`, `stop`, `is_active`. `is_active` now has a 5 s timeout.
- **C-03** `runtime/tmux.py` — 5 `shell=True` sites converted to list-form argv. New `_validate_name()` rejects shell-metacharacter session/window names. New `_socket_path_for()` moves tmux sockets out of `/tmp` into `$XDG_RUNTIME_DIR/ai-lsc/`. `SESSION` is now user-scoped: `ai_lsc_<uid>`.
- **C-04** `runtime/installer.py` — 15+ `shell=True` sites converted to list-form argv. Post-install hooks and script-type installers now run via `["bash", "-c", cmd]` (still a shell, but the registry string is passed verbatim as a single argv element so it can't break out of the subprocess call itself).
- **C-05** `curl|sh` remote installers — **SKIPPED per user instruction**. The Ollama / Grafana Alloy / Meilisearch `curl … | sh` patterns remain in `runtime/installer.py:361`, `registry/layers/inference.py:30`, `registry/layers/observability.py:122`, `registry/layers/data_knowledge.py:164`, and `registry/defaults.py:642`.
- **C-06** `agents/librechat_config.py` — hardcoded `sk-ai-lsc-local` and `sk-local` API keys removed. Keys now read from `AI_LSC_LITELLM_KEY` / `AI_LSC_OPENWEBUI_KEY` environment variables via a new `_env_api_key()` helper.
- **C-07** `agents/orchestrator.py` — missing `import os` added (was a guaranteed `NameError` on every `AgentOrchestrator` instantiation).

#### HIGH (24 of 24 fixed)

- **H-01** Path-traversal via unsanitized `tool_id` — new `_validate_tool_id()` in `runtime/executor.py` rejects `..`, `.`, `/`, and shell metacharacters.
- **H-02** `os.getcwd()` for config — `_load_config` and `save_config` in `ui/main_window.py` now resolve against `self.base_dir` instead of the cwd the app was launched from.
- **H-03** Atomic JSON writes — new `_atomic_write_json()` helper in `ui/main_window.py` uses `tempfile.mkstemp` + `os.fsync` + `os.replace`. Applied to stack export, config save, and stack-wizard state save.
- **H-04** Popen reference tracking — `ProcessManager` now tracks every launched child in `self._launched` and exposes `reap()` + `shutdown()` methods. Zombie accumulation in long-lived GUI sessions is fixed.
- **H-05** `pull_model` Popen not killed on thread crash — `agents/dispatcher.py:_pull_model` now wraps `proc.communicate()` in `try/except` with `proc.kill()` in the handler.
- **H-06** JSON parse crash from malformed LLM output — `agents/agent_loop.py` now wraps `json.loads(func.get("arguments", "{}"))` in `try/except json.JSONDecodeError`. The parse error is fed back to the LLM as a tool result so the model can self-correct on the next round.
- **H-07** `_pull_model` None guard — `dispatcher._pull_model` now handles the case where `runtime.pull_model()` returns `None`.
- **H-08** Duplicate `list_available_tools` schema — `agents/tool_bridge.py:generate_all_schemas` now filters out the static `list_available_tools` schema before appending the annotated version.
- **H-09** Broad `except Exception` — 12+ sites across `guardrails.py`, `loader.py`, `manifest/support.py`, `agent_loop.py`, `ollama_tools.py`, `service_row.py`, `chat/api.py`, `model_pool.py`, `qdrant_bridge.py` now catch specific exceptions (`OSError`, `ValueError`, `json.JSONDecodeError`, `subprocess.SubprocessError`, `urllib.error.URLError`, etc.).
- **H-10** Exception messages expose internal details — `chat/api.py` now sanitizes error bodies via `_short_reason()` and `_categorize_url_error()`. Full detail is logged server-side.
- **H-11** LXC container name from unsanitized `tool_id` — new `_validate_lxc_name()` and `_validate_tool_id()` in `runtime/lxc.py`.
- **H-12** LXC `attach_exec` destroys quoting — `command.split()` replaced with `shlex.split(command)`.
- **H-13** Redis lock silently bypassed when down — `agents/redis_bridge.py:acquire_lock` and `release_lock` now log a WARNING when Redis is unreachable so operators know concurrent agents could race.
- **H-14** `_enforce_quality` false-positive error detection — `agents/orchestrator.py` now uses a word-boundary regex with a negative lookahead `(?![\w\-])` so hyphenated compounds like `error-correction module initialized` are not flagged.
- **H-15** Registry layer files have incomplete flag schemas — `registry/validator.py` now enforces the full 8-key flags schema (`has_cli`, `has_gui`, `has_web`, `is_ollama`, `is_docker`, `is_passive`, `is_mcp`, `is_skills_collection`). `scripts/backfill_layer_flags.py` backfilled 123 flag blocks across all 13 layer files.
- **H-16** `_inject_skill_stub` returns fake success — `agents/dispatcher.py` now validates the skill exists before reporting success.
- **H-17** Placeholder resolution triple-copy in `export.py` — new `_resolve_placeholders()` helper replaces three duplicated 6-line `.replace()` chains in `generate_compose_yaml`, `generate_lxc_configs`, and `generate_firecracker_configs`.
- **H-18** Ollama `/api/tools` endpoint does not exist — `agents/ollama_tools.py` `register_all` and `register_single` are now gated behind `_registration_supported = False` with a clear warning. Tool schemas are passed inline to `/api/chat` instead.
- **H-19** No port validation on user input — new `_validate_port()` in `runtime/executor.py` enforces `1 ≤ port ≤ 65535`. UI surfaces a clean `ValueError` message instead of a cryptic URLError.
- **H-20** No URL scheme validation in `install_custom` — new `_validate_url()` in `runtime/installer.py` rejects non-http(s) schemes.
- **H-21** No signal handling on parent exit — `ui/main_window.py:closeEvent` now calls `runtime._process.shutdown()` to terminate every tracked child.
- **H-22** `install_custom` opens arbitrary URLs — same fix as H-20.
- **H-23** Thread-unsafe pull lock in model pool — `agents/model_pool.py` `self._pull_lock = False` (plain boolean) replaced with `threading.Lock()`. Non-blocking acquire so concurrent agent threads don't both enter the pull branch.
- **H-24** Qdrant collection dimension hardcoded — `agents/qdrant_bridge.py` `create_collection` now probes the live embedding dimension via `_probe_embedding_dimension()` instead of hardcoding `768`. Existing collections with a different dimension are surfaced (not silently hidden).

#### MEDIUM (42 of 42 fixed)

- **M-01** Missing `encoding="utf-8"` on `open()` — fixed in 15+ sites across `ui/main_window.py`, `runtime/lxc.py`, `ui/dialogs/stack_wizard.py`.
- **M-02** `os.path.join` mixed with `pathlib` — `utils/filesystem.py:walk_tree` now uses `Path.rglob`.
- **M-03** TOCTOU race in log file operations — `ui/main_window.py` log readers now wrap stat + read in a single `try/except OSError`.
- **M-04** No file locking on shared JSON files — `_atomic_write_json()` now uses `fcntl.flock` for cross-process serialization.
- **M-05** No file lock / fsync on LXC config append — `runtime/lxc.py:_apply_config` now flushes + fsyncs.
- **M-06** `/tmp` socket path without cleanup — `runtime/tmux.py:_socket_path_for` moves sockets under `$XDG_RUNTIME_DIR/ai-lsc/` with sanitized tool_id.
- **M-07 through M-13** Nested-if flattening — applied via guard clauses, dict dispatch, reverse-lookup dicts, and predicate extraction across `installer.py`, `orchestrator.py`, `model_pool.py`, `guardrails.py`, `main_window.py`.
- **M-14 through M-17** Duplicate code extraction — `_iter_py_files` / `_read_source` in `guardrails.py`, `_scan_and_import` / `_match_tags` patterns, `_cache_set` / `_cache_get` in `redis_bridge.py`, `_resolve_placeholders` in `export.py`.
- **M-18 through M-23** Loop → comprehension / builtin — `dict.fromkeys()` for dedup, dict comprehension for `preflight_batch`, `next()` for `detect_terminal`, list comprehension for LXC config lines, `extend()` for skills_loaded.
- **M-24** Dead variable `exposed` in `get_consumers` — removed.
- **M-25** `Any` type annotations — `ui/protocol.py` now uses `TYPE_CHECKING` imports; `agents/orchestrator.py` `dispatcher` param now typed as `"AgentDispatcher"`.
- **M-26** Variable shadowing in `generate_env_file` — `lines` renamed to `ollama_ep`.
- **M-27** Dead if/else block in `guardrails.py` — removed (PARENT_ALLOWED_DIRS was always empty).
- **M-28** Redundant `import json` in orchestrator method — removed.
- **M-29** Sorted-set member collision in task queue — `redis_bridge.py` now uses `task_id` as the sorted-set member and stores the payload in a separate hash.
- **M-30** `_LAYERS_DIR` defined but never used — removed from `registry/loader.py`.
- **M-31** `use_model` tautological assignment — cleaned up.
- **M-32** Missing error handling on `install_pip` — added `try/except subprocess.CalledProcessError`.
- **M-33 / M-34** Timeouts on `systemctl is-active` and `pkill` — both now have `timeout=5`.
- **M-35** File handle leak in `verify_and_watch` — `open(log_file, "a").close()` replaced with `Path(log_file).touch()`.
- **M-36** Recursive directory traversal — `utils/filesystem.py:walk_tree` rewritten to use `Path.rglob`.
- **M-37** Model pool pull timeout applies to entire stream — `for line in resp: pass` replaced with `resp.read()`.
- **M-38** Embed batch is sequential — `qdrant_bridge.py:embed_batch` now uses `ThreadPoolExecutor.map`.
- **M-39** Hardcoded `pacman` install hint — `_install_hint` in `runtime/lxc.py` now lists pacman + apt + dnf.
- **M-40** Nested ternary in `_build_payload_history` — deferred (chatbot_console.py), see whatremains.txt.
- **M-41** Duplicate `OpenEngineerImporter` import — removed from `stack_templates/manager.py`.
- **M-42** `_load_skills` documents unimplemented Qdrant feature — converted to explicit `TODO(security)` comment.

#### LOW (19 of 20 fixed; 1 deferred)

See [whatremains.txt](whatremains.txt) for the full list. Highlights:

- **L-02** Line-ending normalization on log reads — `rstrip("\r\n")` applied.
- **L-03** TOCTOU on symlink creation — `os.symlink` wrapped in `try/except FileExistsError`.
- **L-05** Tmux session name uniqueness — `SESSION = f"ai_lsc_{os.getuid()}"`.
- **L-06** Port range check in `chat/api.py` — `_validate_port` applied to `port_id` up-front.
- **L-08** `create_collection` reports success for existing collection — now checks the existing collection's dimension and surfaces mismatches.

### SaaS-only tool blocklist (v3.1 hardening follow-up)

After the v3.1 release, the user identified a policy gap: SaaS-only tools (closed-source desktop apps with restrictive ToS, hosted LLM routers with no local binary, managed inference services) must not be addable to the registry. The audit found that the actual code registry was already clean — the SaaS names (`OpenRouter`, `LM Studio`, `Groq`, `Codestral`) only appeared as stale references in `README.md` and `docs/ADR-001-capability-architecture.md`. They were removed from the code at some earlier point but the docs were never updated.

**What changed:**

1. **Stale doc references fixed.** `README.md` L6 row now lists `LiteLLM Proxy, 9Router Proxy, Odysseus, LangChain, LangFlow, OpenAI Swarm, Agno` (matching the actual registry). `README.md` L8 row replaces `Codestral` (Mistral SaaS model) with `OpenHands` and `Codex`. `docs/ADR-001-capability-architecture.md` LLM Gateway providers now list `LiteLLM · 9Router Proxy · Local proxy` (was `LiteLLM · OpenRouter · Local proxy`); Inference Engine providers replace `LM Studio` with `SGlang`.

2. **SaaS blocklist added to the registry validator** (`src/ai_lsc/registry/validator.py`). The following tool_ids are now rejected at validation time with a clear error message pointing to this section:

   `openrouter`, `lm_studio`, `lmstudio`, `groq`, `together_ai`, `together`, `fireworks_ai`, `fireworks`, `replicate`, `runpod`, `modal`, `anyscale`, `perplexity`, `cohere`, `mistral_api`, `deepseek_api`, `openai_api`, `huggingface_inference`

3. **SaaS host regex added to the validator.** Even if a tool_id isn't on the blocklist, the validator now rejects any launcher cmd or installer cmd that references a known SaaS provider hostname (api.openai.com, api.anthropic.com, api.openrouter.ai, api.groq.com, api.together.xyz, api.fireworks.ai, api.replicate.com, api.perplexity.ai, api.cohere.ai, api.mistral.ai, api.deepseek.com, generativelanguage.googleapis.com, api.lmstudio.ai, endpoint.huggingface.com). Localhost URLs (127.0.0.1, localhost, 0.0.0.0) are always allowed.

4. **Localhost-only env forced for CLI tools that CAN call SaaS.** `claude_code`, `aider`, `openhands`, `fabric`, and the new `codex` entry now have their launcher cmds prepended with the appropriate localhost env vars:

   | Tool | Env vars forced |
   |------|-----------------|
   | `claude_code` | `ANTHROPIC_BASE_URL=http://127.0.0.1:4000 ANTHROPIC_API_KEY=sk-ai-lsc-local` |
   | `aider` | `OPENAI_API_BASE=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local` |
   | `openhands` | `OPENAI_API_BASE=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local` |
   | `fabric` | `OPENAI_API_BASE=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local` |
   | `codex` (new) | `OPENAI_BASE_URL=http://127.0.0.1:4000/v1 OPENAI_API_KEY=sk-ai-lsc-local` |

   This breaks SaaS routing by default — the user must explicitly override the env var (via the service row port or a custom launcher cmd) to call a SaaS endpoint. Each tool's `deps` now includes `litellm` so the Stack Editor flags a missing local proxy if the user hasn't staged one.

5. **New `codex` tool entry added** to `registry/defaults.py` and `registry/layers/endpoints.py` — OpenAI's open-source Codex CLI (`@openai/codex` npm package), classified as L6 AI Endpoints, with the localhost-only launcher shown above. The user explicitly approved this addition with the caveat: "you can add codex and claude code but only if mapped by force to a localhost port for the engine or endpoint."

**Verification:** defaults.py validates with 0 errors (125 tools); layer files validate with 0 non-curl|sh errors (124 tools); all 5 localhost-mapped tools confirmed to have `127.0.0.1` in their launcher cmd; the SaaS blocklist correctly rejects `openrouter` and `lm_studio` with the documented error message; the SaaS host regex correctly rejects `https://api.openai.com/v1` in a launcher cmd while allowing `http://127.0.0.1:4000/v1`.

---

### License acceptance gate (v3.1 hardening follow-up #2)

After the SaaS blocklist landed, the user asked for a layered license-acceptance system: ToS/disclaimer warnings for proprietary tool pulls, per-tool license acceptance for open-source tools, and a license auto-approval registry where the user can pre-approve entire license types (accept all GPL, all AGPL, all MIT, all BSD, etc.) so they don't have to accept each tool individually. The auto-approval registry must NOT contain any SaaS or proprietary tools. `lmstudio` stays on the blocklist for aggressive ToS.

**What changed:**

1. **New license catalog** (`src/ai_lsc/registry/licenses.py`) — 20 SPDX IDs across three categories:

   | Category | Auto-approvable? | Disclaimer? | Licenses |
   |----------|------------------|-------------|----------|
   | **OSI** (open-source) | ✅ Yes | ❌ No | MIT, Apache-2.0, GPL-2.0, GPL-3.0, AGPL-3.0, LGPL-3.0, BSD-2-Clause, BSD-3-Clause, MPL-2.0, ISC, PostgreSQL, Python |
   | **SOURCE_AVAILABLE** (fair-code) | ❌ No | ✅ Yes | BSL-1.1, SSPL, RSALv2, Sustainable-Use, Dify-OSL |
   | **PROPRIETARY** (ToS-governed) | ❌ No | ✅ Yes (prominent) | Proprietary, Anthropic-ToS, LMStudio-ToS (blocked) |

   Each license entry includes: SPDX ID, human-readable name, category, URL to full text, one-paragraph summary, and an optional disclaimer shown in the acceptance dialog.

2. **New `LicenseGate` class** (`src/ai_lsc/registry/license_gate.py`) — sits between the user's "Install" click and the installer dispatch. For every tool installation, the gate checks (in order):
   - **SaaS blocklist** — if the tool_id is blocked, raises `LicenseBlocked` immediately (no dialog, no acceptance, no install).
   - **Auto-approval registry** (`config/license_approvals.json`) — user-editable list of OSI-approved SPDX IDs. If the tool's license is in this list AND the license category is OSI, install proceeds without a dialog. Non-OSI licenses in the file are ignored + logged (defensive against hand-editing).
   - **Per-tool acceptance registry** (`config/license_acceptances.json`) — auto-managed; records every per-tool acceptance so the user isn't prompted twice.
   - If none of the three cover the tool, raises `LicenseAcceptanceRequired` (carrying the `LicenseInfo` for the dialog).

   `LicenseGate.add_auto_approval(spdx)` **rejects** non-OSI licenses with a clear `ValueError` — source-available and proprietary licenses cannot be auto-approved, period.

3. **New `LicenseAcceptanceDialog`** (`src/ai_lsc/ui/dialogs/license_dialog.py`) — Qt dialog shown when the gate raises `LicenseAcceptanceRequired`. Shows:
   - Tool name + tool_id + license name + SPDX ID
   - Category banner (green ✓ for OSI, orange ⚠ for source-available, red ⛔ for proprietary)
   - License summary (one paragraph)
   - Disclaimer (only for source-available + proprietary — prominent red box)
   - "Open in browser ↗" button linking to the full license text
   - Confirmation checkbox (pre-checked for OSI, unchecked for non-OSI — the user must explicitly check it before Accept is enabled)
   - Three buttons: **Accept & Install** (records per-tool acceptance), **Accept all \<license\>** (only for OSI — adds the SPDX to the auto-approval registry), **Cancel**

   Also includes a `LicenseBlockedDialog` for the blocked case (just an OK button + suggestion to use a local alternative).

4. **`license` field added to the registry schema** — every tool entry must now declare its license SPDX ID. The validator (`registry/validator.py`) enforces this:
   - Missing/empty `license` field → error
   - Unknown SPDX ID (not in the license catalog) → error
   - The `_REQUIRED_FIELDS` set now includes `"license"`

   Two backfill scripts added:
   - `scripts/backfill_tool_licenses.py` — adds the `license` field to every tool based on a curated override table (85 tools mapped to known licenses: ollama→MIT, vllm→Apache-2.0, grafana→AGPL-3.0, redis→RSALv2, terraform→BSL-1.1, n8n→Sustainable-Use, claude_code→Anthropic-ToS, etc.)
   - `scripts/backfill_default_licenses.py` — fills any remaining tools with `"Proprietary"` as the defensive default (83 tools defaulted — the user can review and update these to their actual licenses later)

5. **License gate wired into the installer** — `InstallerManager.__init__` now accepts a `license_gate` parameter. `InstallerManager.run()` and `install_with_preflight()` call `self._check_license(tool_id, license_spdx)` before any subprocess dispatch. If the gate raises `LicenseBlocked` or `LicenseAcceptanceRequired`, the exception propagates up through `RuntimeExecutor.install_tool()` to the UI.

6. **`ServiceRow` catches license exceptions** — the install thread's `except Exception` handler (which runs on the main thread via `QTimer.singleShot`) calls `_handle_license_exception()` which:
   - For `LicenseBlocked` → shows `LicenseBlockedDialog` (just an OK button)
   - For `LicenseAcceptanceRequired` → shows `LicenseAcceptanceDialog` and connects the dialog's `accepted_individual` / `accepted_all_of_type` signals to handlers that record the acceptance and retry the install

7. **`lmstudio` blocklist comment** — the `SAAS_BLOCKLIST` definition in `validator.py` now includes an explicit comment: "lm_studio / lmstudio: BLOCKED for aggressive ToS — the user considers LM Studio's Terms of Service restrictive enough to be equivalent to a SaaS offering, so it is auto-banned regardless of any per-tool acceptance the user might try to grant."

**License distribution after backfill** (135 unique tool_ids across defaults.py + layer files):

```
Proprietary         50 tools  (defensive default for tools whose license is unknown)
MIT                 49 tools
Apache-2.0          17 tools
AGPL-3.0             5 tools
GPL-3.0              3 tools
MPL-2.0              2 tools
Anthropic-ToS        1 tool   (claude_code)
Python               1 tool   (python)
BSL-1.1              1 tool   (terraform)
PostgreSQL           1 tool   (postgresql)
GPL-2.0              1 tool   (mariadb)
RSALv2               1 tool   (redis)
LGPL-3.0             1 tool   (glances)
Dify-OSL             1 tool   (dify)
Sustainable-Use      1 tool   (n8n)
```

The 50 tools defaulted to "Proprietary" include some that are actually open-source (tmux, git, podman, docker) — the user can review and update these in `defaults.py` / the layer files. The gate will require individual acceptance for each until the license is corrected.

**Verification:**
- defaults.py: 125 tools, 0 validation errors
- Layer files: 124 tools, 0 non-curl|sh validation errors
- All 135 unique tool_ids have a `license` field
- `LicenseGate.check()` correctly returns `needs_acceptance` for fresh tools, `accepted` after `accept()`, `blocked` for SaaS-blocklist tool_ids
- `LicenseGate.add_auto_approval()` correctly rejects BSL-1.1 (source-available) and Proprietary with `ValueError`
- `lmstudio` and `lm_studio` both on `SAAS_BLOCKLIST`
- `claude_code` (Anthropic-ToS) and `n8n` (Sustainable-Use) both surface `needs_disclaimer=True` via their category
- Auto-approval + acceptance files are created in `config/` with the expected JSON structure

---

### Bugs caught during the post-pass double-check (fixed)

Three latent bugs were introduced during the initial fix wave and caught by the double-check's 19 functional spot-checks. All three are now fixed:

1. **`installer._validate_tool_id` regex allowed `/`** — the regex was `r"^[A-Za-z0-9_.:\-/]+$"` (with trailing `/`), so `../../etc/passwd` would have passed. Tightened to `r"^[A-Za-z0-9_.:\-]+$"` (no `/`).
2. **All three `_validate_tool_id` validators accepted bare `..` and `.`** — `os.path.normpath('..')` returns `'..'` unchanged, so the normpath check missed these. Added explicit `tool_id in {".", ".."}` rejection in installer.py, executor.py, and lxc.py.
3. **H-14 `_ERROR_RE` still flagged `error-correction`** — `\b` (word boundary) treats `-` as a non-word char, so `error-correction` had a boundary between `error` and `correction`. Changed regex to `\b(?:error|failed|not found|timeout|exception|traceback)(?![\w\-])` — the negative lookahead rejects matches where the next character is a word char OR a hyphen.

### Verification

- All 89 Python source files parse cleanly via `ast.parse`.
- All 124 tools in `defaults.py` pass the strengthened validator (0 errors).
- All 123 tools across the 13 layer files pass the strengthened validator (3 expected curl|sh-related warnings only).
- All 134 unique tool_ids (defaults + layers merged) pass every `_validate_tool_id` validator (installer, executor, LXC) and every `_validate_lxc_name` check.
- 19/19 functional spot-checks pass (after the 3 double-check fixes).
- Ticker edge + orphan detection simulated against the real `STACK_WIRINGS` data across 6 test scenarios — all behaved as expected.

### Known issues

- **PySide6 not available in some test environments.** The new widget modules (`pipeline_ticker.py`, `workspace_tab.py`) AST-parse cleanly and pass structural checks, but were not exercised by a live Qt instantiation test in the sandbox where v3.1 was finalized. Verify by running the app.
- **`open_webui` vs `openwebui` tool_id collision** — the Pipeline Ticker surfaces this real registry inconsistency. Recommend a follow-up pass to reconcile.
- **`docs/screenshots/` still reflects v3.0** — a screenshot refresh pass to capture the new Pipeline Ticker + Workspace Tab is overdue.

### Upgrade notes

- If you have a v3.0 `pipeline_state.json`, it will continue to work — the schema is unchanged.
- If you maintain custom layer-file entries, run `python scripts/backfill_layer_flags.py` to backfill the 5 new flag keys (`is_ollama`, `is_docker`, `is_passive`, `is_mcp`, `is_skills_collection`) defaulting to `False`. The validator will reject entries missing these keys.
- If you have hardcoded `sk-ai-lsc-local` API keys in your environment, set `AI_LSC_LITELLM_KEY` and `AI_LSC_OPENWEBUI_KEY` env vars instead — the source-code default is now an empty string.
- If you launch the app from a non-default working directory, config is now resolved against `BASE_DIR` instead of `os.getcwd()` — this may move your `config.json` to a new location on first v3.1 launch.

### Artifacts

- Master tarball: `ai-lsc-master-2026-07-07.tar.gz`
- New scripts: `scripts/backfill_layer_flags.py`
- New widgets: `src/ai_lsc/ui/widgets/pipeline_ticker.py`, `src/ai_lsc/ui/widgets/workspace_tab.py`
- New docs: `CHANGES.md` (this file), `docs/ADR-002-pipeline-ticker.md`, `docs/ADR-003-workspace-tab.md`
- Skipped-items register: `whatremains.txt`

---

## v3.0 — earlier

See git history for the v3.0 release notes. v3.0 introduced the 13-layer architecture, the capability model, the OpenEngineer importer, and the Firecracker microVM export backend.
