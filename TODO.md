# AI-LSC TODO

## Recent progress (v3.2 — 10-Layer Systems Architecture)

- ✅ Completed the 10-layer taxonomy migration that was started on top of v3.1.1b: `defaults.py` (108-tool seed), all 11 modular layer files (186 tools), `stack/connections.py` (92 static layers + 5 dynamic loop lookups), CATEGORY_MAP cascade (221 categories), validator level range, README/quickstart/docs. See [CHANGES.md](CHANGES.md) → v3.2.
- ✅ Repaired `ui/pages/db_manager.py`: the interim migration had truncated it to 222 lines (syntax error + lost implementation); the canonical 1.3 k-line implementation now lives in-tree and its CATEGORY_MAP is migrated to the 10-layer taxonomy.
- ✅ Reconciled `kanban` into the layer files (was defaults-only) — merged registry is now 186 tools.
- ✅ Preserved all operational registry metadata (installers, launchers, deps, flags, licenses, filesystem blocks) that the master-target defaults rewrite had stripped; curl|sh policy markers untouched (C-05).
- ✅ `open_webui` vs `openwebui` orphan gap: confirmed moot — only `openwebui` exists in the registry and it has a STACK_WIRINGS entry.

## Recent progress (v3.1 — 2026-07-07)

- ✅ Applied the full master code critique: 91 of 93 findings addressed (CRITICAL × 6, HIGH × 24, MEDIUM × 42, LOW × 19). The 2 intentionally skipped items (curl|sh remote installers) are documented in [whatremains.txt](whatremains.txt).
- ✅ Added the Pipeline Ticker: scrolling wiring-topology status bar at the top of every workspace tab. Color-coded arrows by interface type, orphans flagged red, click-to-jump to Tools tab.
- ✅ Added the Workspace Tab: peek-style orchestration surface with one sub-tab per active tool. Web tools embed via QWebEngineView, CLI tools attach to tmux via `capture-pane` polling. Feels like virt-manager / aqemu for your AI stack.
- ✅ Strengthened the registry validator to enforce the full 8-key flags schema; backfilled 123 layer-file flag blocks (one-shot migration script retired post-apply).
- ✅ Reconciled tool count: 124 tools in `defaults.py` + 123 tools across the 13 layer files (merged).

## Open work

The 10-layer taxonomy is now in place; classification quality is the next
frontier. The 78 layer-file tools absent from the master registry were
classified by hand for v3.2 — review those assignments if any feel
wrong: `layer`/`level` sync from layer files makes corrections a
one-file edit. If you're reading this file, first of all thanks for
trying it out — help by testing the UI, tools, configs, and pipelines.
It's a lot.

### Follow-ups worth doing

- Regroup the 11 legacy layer files (still named after the old taxonomy:
  `security.py`, `observability.py`, `devops.py`, ...) into 10 files that
  match the new layer names. The loader merges by tool, not by filename,
  so this is pure file-shuffling — deferred as churn in v3.2.
- `llama-swap` and `mesh-llm` are listed as Layer 5 exemplars in the
  architecture docs but only `meshllm` exists in the registry; consider
  adding a `llama_swap` entry (VRAM swapper) to complete the story.
- The 74 preserved-but-unused cascade categories (from the v3.1.1b map)
  could be pruned if the category combobox feels crowded.

### Deferred from the critique pass

See [whatremains.txt](whatremains.txt) for the full list. Highlights:

- `curl|sh` remote installers (Ollama, Grafana Alloy, Meilisearch) — left in place per user instruction. Apply the critique's download-first pattern when the remote-code-execution policy is revisited.
- L-17: `registry/openengineer/parser.py` still has commented-out code blocks — confirm with the OE importer maintainer before deleting.
- L-18: registry layer files declare tools without `filesystem` blocks; backfilling `install/config/cache/logs` paths across the layer-file tools is a mechanical but sizable job (v3.2 preserved the 24 defaults.py blocks + n8n/odysseus).
- M-22 / M-40: `chatbot_console.py` HTML bubble builder + nested ternary — addressed in the MoE QA pass (`_render_bubble` helper extracted, nested ternary flattened to `"\n\n".join`).
- M-10 / M-15 / M-16: `registry/openengineer/importer.py` nested-if flattening + dedup — addressed in the MoE QA pass (two scan loops merged into single `_scan_dir` helper).

### UX polish still on the wishlist

- The Monitor page flow is 80% organized; the layout is still being decided.
- More `STACK_WIRINGS` entries — the ticker's value scales with how complete the wiring data is. Currently 137 wirings for 186 tools; gaps surface as orphans when staged.
- Screenshots: the `docs/screenshots/` directory still reflects v3.0. A refresh pass to capture the 10-layer sidebar + Pipeline Ticker + Workspace Tab is overdue.
