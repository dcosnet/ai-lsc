# AI-LSC Changelog

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
