# Registry installer-URL sync — v3.3.0

Source reference: `ai-stack-guide-v12.md` (systems-architect guide).
Patched files: `src/ai_lsc/registry/layers/*.py`.
Total installer URL corrections: **51** across 8 layer files.

Five categories of patches:
- **A** (28): git / git_node / custom installer `pkg` URL corrected to match the v12 markdown reference.
- **B** (6): script-type installer gets a new `pkg` field added (the github repo), while the existing working `cmd` is left untouched.
- **C** (10): registry-only git tools with no v12 markdown entry — official upstream repos found via web search.
- **D** (3): type-mismatch fixes — md says git / git_node, registry had `uv` with a package name. Switched to git / git_node with the github URL from the v12 markdown reference.
- **E** (4): user-provided URLs for the 4 previously-unresolved registry-only tools (web search could not find these; the user provided the official upstream URLs directly).

Plus 1 new tool entry (ComfyUI) and a runtime hardening of `install_git` / `install_git_node` in `runtime/installer.py`.

## `devops.py` (3 A/B/C patches)

| Tool ID | Cat | Old `pkg` | New `pkg` |
|---|---|---|---|
| `opentofu` | A | `https://opentofu.org/docs/intro/install/` | `https://github.com/opentofu/opentofu` |
| `terragrunt` | A | `https://terragrunt.gruntwork.io/docs/getting-started/install/` | `https://github.com/gruntwork-io/terragrunt` |
| `crossplane` | C | `https://docs.crossplane.io/v2/getting-started/install/` | `https://github.com/crossplane/crossplane` |

## `inference.py` (6 A/B/C patches)

| Tool ID | Cat | Old `pkg` | New `pkg` |
|---|---|---|---|
| `airllm` | A | `https://github.com/liguodongiot/llm-airforce` | `https://github.com/lyogavin/airllm` |
| `llamacpp` | A | `https://github.com/ggerganov/llama.cpp` | `https://github.com/ggml-org/llama.cpp` |
| `locally_uncensored` | A | `https://github.com/nicely-done/locally-uncensored` | `https://github.com/PurpleDoubleD/locally-uncensored` |
| `turbollm` | A | `https://github.com/nicely-done/turbollm` | `https://github.com/mohitsoni48/TurboLLM` |
| `llamafile` | B | `(none)` | `https://github.com/Mozilla-Ocho/llamafile` |
| `ollama` | B | `(none)` | `https://github.com/ollama/ollama` |

## `knowledge_management.py` (10 A/B/C patches)

| Tool ID | Cat | Old `pkg` | New `pkg` |
|---|---|---|---|
| `airweave` | A | `https://github.com/nicely-done/airweave` | `https://github.com/airweave-ai/airweave` |
| `mirofish` | A | `https://github.com/nicely-done/mirofish` | `https://github.com/666ghj/MiroFish` |
| `opendataloader` | A | `https://github.com/nicely-done/opendataloader` | `https://github.com/opendataloader-project/opendataloader-pdf` |
| `opendataloader_pdf` | A | `https://github.com/nicely-done/opendataloader-pdf` | `https://github.com/opendataloader-project/opendataloader-pdf` |
| `understand_anything` | A | `https://github.com/nicely-done/understand-anything` | `https://github.com/Egonex-AI/Understand-Anything` |
| `meilisearch` | B | `(none)` | `https://github.com/meilisearch/meilisearch` |
| `qdrant` | B | `(none)` | `https://github.com/qdrant/qdrant` |
| `everos_memory` | C | `https://github.com/nicely-done/everos-memory` | `https://github.com/EverMind-AI/EverOS` |
| `mnemo_cortex` | C | `https://github.com/nicely-done/mnemo-cortex` | `https://github.com/GuyMannDude/mnemo-cortex` |
| `turbovec` | C | `https://github.com/nicely-done/turbovec` | `https://github.com/ryancodrai/turbovec` |

## `observability.py` (4 A/B/C patches)

| Tool ID | Cat | Old `pkg` | New `pkg` |
|---|---|---|---|
| `latitude` | A | `https://github.com/nicely-done/latitude` | `https://github.com/latitude-dev/latitude-llm` |
| `pulse_ai` | A | `https://github.com/nicely-done/pulse-ai` | `https://github.com/glieai/pulse-ai` |
| `grafana_alloy` | B | `(none)` | `https://github.com/grafana/alloy` |
| `dma` | C | `https://github.com/distcc/dma` | `https://github.com/distcc/distcc` |

## `orchestrators.py` (15 A/B/C patches)

| Tool ID | Cat | Old `pkg` | New `pkg` |
|---|---|---|---|
| `agentic_os` | A | `https://github.com/nicely-done/agentic-os` | `https://github.com/aporb/agentic-os` |
| `career_ops` | A | `https://github.com/nicely-done/career_ops` | `https://github.com/santifer/career-ops` |
| `container_tool` | A | `https://github.com/nicely-done/container_tool` | `https://github.com/NVIDIA/nvidia-container-toolkit` |
| `hivemind` | A | `https://github.com/nicely-done/hivemind` | `https://github.com/hivementality-ai/hivemind` |
| `loop_engineering` | A | `https://github.com/nicely-done/loop_engineering` | `https://github.com/lcajigasm/loop-engineering` |
| `opensandbox` | A | `https://github.com/nicely-done/opensandbox` | `https://github.com/opensandbox-group/OpenSandbox` |
| `ponytail` | A | `https://github.com/nicely-done/ponytail` | `https://github.com/DietrichGebert/ponytail` |
| `promptops` | A | `https://github.com/nicely-done/promptops` | `https://github.com/llmhq-hub/promptops` |
| `skillspector` | A | `https://github.com/nicely-done/skillspector` | `https://github.com/NVIDIA/skillspector` |
| `spec_kit` | A | `https://github.com/nicely-done/spec_kit` | `https://github.com/github/spec-kit` |
| `fabric` | B | `(none)` | `https://github.com/danielmiessler/fabric` |
| `agent_reach` | C | `https://github.com/nicely-done/agent_reach` | `https://github.com/Panniantong/Agent-Reach` |
| `headroom` | C | `https://github.com/nicely-done/headroom` | `https://github.com/headroomlabs-ai/headroom` |
| `nightshift` | C | `https://github.com/nicely-done/nightshift` | `https://github.com/johndaskovsky/nightshift` |
| `openbrain` | C | `https://github.com/nicely-done/openbrain` | `https://github.com/NateBJones-Projects/OB1` |

## `routing.py` (1 A/B/C patches)

| Tool ID | Cat | Old `pkg` | New `pkg` |
|---|---|---|---|
| `9router_proxy` | A | `https://github.com/nicely-done/9router` | `https://github.com/decolua/9router` |

## `security.py` (1 A/B/C patches)

| Tool ID | Cat | Old `pkg` | New `pkg` |
|---|---|---|---|
| `keycloak` | C | `keycloak` | `https://github.com/keycloak/keycloak` |

## `user_interfaces.py` (4 A/B/C patches)

| Tool ID | Cat | Old `pkg` | New `pkg` |
|---|---|---|---|
| `deep_eye` | A | `https://github.com/nicely-done/deep-eye` | `https://github.com/zakirkun/deep-eye` |
| `forge` | A | `https://github.com/AUTOMATIC1111/stable-diffusion-webui-forge` | `https://github.com/lllyasviel/stable-diffusion-webui-forge` |
| `local_llm_launcher` | A | `https://github.com/nicely-done/local-llm-launcher-gui` | `https://github.com/jimdawdy-hub/Local-LLM-Launcher-GUI` |
| `parakeet` | A | `https://github.com/nicely-done/parakeet.cpp` | `https://github.com/mudler/parakeet.cpp` |

## Category D — type-mismatch fixes (3 patches)

These tools were registered as `uv` package-manager installs but the v12 markdown reference (which the user manually tested) lists them as `git` or `git_node`. Switched to git / git_node type with the github URL.

| Tool ID | Source file | Old type / pkg | New type / pkg |
|---|---|---|---|
| `pm_skills` | `orchestrators.py` | `uv` / (package name) | `git` / `https://github.com/product-on-purpose/pm-skills` |
| `agno` | `orchestrators.py` | `uv` / (package name) | `git` / `https://github.com/agno-agi/agno` |
| `openhands` | `devops.py` | `uv` / (package name) | `git_node` / `https://github.com/All-Hands-AI/OpenHands.git` |

## Category E — user-provided URLs (4 patches)

These 4 registry-only tools had placeholder `github.com/nicely-done/...` URLs because web search could not find their official upstreams.  The user provided the official URLs directly:

| Tool ID | Source file | Old `pkg` (placeholder) | New `pkg` (user-provided) |
|---|---|---|---|
| `algory` | `orchestrators.py` | `https://github.com/nicely-done/algory` | `https://github.com/aryaghan-mutum/algory` |
| `atlas_os` | `orchestrators.py` | `https://github.com/nicely-done/atlas_os` | `https://github.com/atlas-os/atlas` |
| `eagle_eye` | `observability.py` | `https://github.com/nicely-done/eagle_eye` | `https://github.com/thoughtfuldev/eagleeye` |
| `glassmind` | `orchestrators.py` | `https://github.com/nicely-done/glassmind` | `https://github.com/khodges42/glassMind` |

## New tool entry — ComfyUI

ComfyUI was referenced in `registry/stack_templates/ai-image-gen-local.json` but had no registry entry before.  Added as a Level 10 tool in `user_interfaces.py`:

| Field | Value |
|---|---|
| `tool_id` | `comfyui` |
| `name` | `ComfyUI` |
| `level` | 10 |
| `layer` | `Human Interface & System Operations` |
| `role` / `category` | `Node-Based Image Gen` |
| `installer.type` | `git` |
| `installer.pkg` | `https://github.com/comfy-org/comfyui` |
| `launcher.cmd` | `cd {tools_root}/comfyui && python main.py --listen 0.0.0.0 --port {port}` |
| `launcher.default_port` | `8188` |
| `deps` | `[cuda]` |
| `license` | `GPL-3.0` |

Total registry size: 187 tools (was 186).

## Runtime hardening — `runtime/installer.py`

`install_git` and `install_git_node` were hardened so that re-running install on an already-cloned tool fetches only the diff:

1. **Check `.git` dir, not just `dest` dir.** Previously the existence check was `os.path.exists(dest)`, which is True for any dir — including non-git dirs.  Now checks `os.path.isdir(dest/.git)`, so a non-git dir doesn't cause `git pull` to fail.
2. **Fall back to re-clone on pull failure.** If `git pull --ff-only` fails (diverged branches, network errors, corrupted index, etc.), the old dir is moved aside to `<dest>.bak.<unix_ts>` and a fresh clone is made.  The install always ends in a usable state.
3. **Back up existing non-git dir.** If `dest` exists but isn't a git repo, it's backed up to `<dest>.bak.<unix_ts>` and a fresh clone is made.
4. **Log which path was taken.** The return message says whether the tool was pulled, re-cloned (with backup path), or freshly cloned — so the user can see what happened.

Effect: re-running install on a tool that's already cloned only fetches the diff (a few KB / MB), not the entire repo.  This is the bandwidth-saving behaviour the user asked for.

## Verification

All 51 patches applied successfully:
- 28 git-ish pkg URL replacements (each old `pkg` string was unique within its file and matched exactly once).
- 6 script-type pkg-field injections (each matched exactly one installer block).
- 10 missing-repo lookups via web search.
- 3 type-mismatch fixes (uv → git / git_node).
- 4 user-provided URLs for previously-unresolved tools.
- 1 new ComfyUI tool entry added to `user_interfaces.py`.

All 94 Python files under `src/` AST-parse cleanly after the patches. The registry extractor re-imports every layer module and confirms all 51 patches landed + the new ComfyUI entry.  Total registry size: 187 tools (was 186).

0 `nicely-done` placeholder URLs remain in the registry.
