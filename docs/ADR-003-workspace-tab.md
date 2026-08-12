# ADR-003: Workspace Tab (Peek-Style Orchestration)

**Date:** 2026-07-07
**Status:** Accepted

## Context

The v3.0 workflow for interacting with a running tool required context-switching out of the AI-LSC app:

- Web-interface tools (OpenWebUI, Hermes, Odysseus, ComfyUI, etc.) required opening a browser tab and navigating to `http://127.0.0.1:{port}`.
- CLI tools (Aider, Claude Code, OpenHands, etc.) required opening a terminal and `tmux attach -t ai_lsc_<uid>::<tool_id>`.

When debugging a stack of 8+ tools, this meant 8+ browser tabs + 8+ terminal windows — exactly the juggling the app was supposed to eliminate.

The user asked for a "peek orchestration" surface that "feels like managing VMs from virt-manager or aqemu" — every staged tool reachable from a single window, no context-switch to a browser or terminal app required. The user also raised the option of using servo (Mozilla's Rust web engine) to embed web tools directly, calling it a "workspace" that "can have multiple tabs for various tools like openwebui, hermes dashboard, or odysseus even."

## Decision

Add a new `WorkspaceTab` widget with one sub-tab per active tool. The sub-tab type is chosen by the tool's feature flags:

- `has_web=True` → `_WebToolPage` — embeds the tool's web UI via `QWebEngineView`
- `has_cli=True` (and no web) → `_CliToolPage` — embeds the tool's tmux session via `tmux capture-pane` polling
- otherwise → `_PlaceholderPage` — explains the tool is passive / library

### Web embedding: QWebEngineView (with servo-swap path documented)

The web embedding uses `PySide6.QtWebEngineWidgets.QWebEngineView` by default. Servo's Python bindings are not yet production-ready and have no first-class PySide6 integration, so servo is not the default. However, the module is structured so swapping in servo later is a one-line change: replace `_make_web_view()` with a servo-backed widget that exposes the same `setUrl()` / `url()` / `load()` API. The rest of `_WebToolPage` only depends on that API.

The `_WebToolPage` includes:

- A URL bar at the top showing the loaded URL (monospace, slate-50 background)
- A ⟳ reload button
- A ↗ "open in external browser" button (fallback for when QtWebEngine is not installed)
- The `QWebEngineView` itself, stretched to fill the remaining space

When `QtWebEngine` is not installed (some minimal PySide6 installs skip it), the page falls back to a `_PlaceholderPage` explaining the situation and offering the ↗ button to open the URL externally.

### CLI embedding: tmux capture-pane polling

The `_CliToolPage` is a `QTextEdit` (read-only, dark theme, monospace font) that polls `tmux capture-pane -t <session>::<tool_id> -p -S -200` every 250 ms (4 Hz) and renders the captured output. The poll is driven by a `QTimer`; the captured content is compared to the current `toPlainText()` and only written if it changed (avoids flicker). The cursor is auto-scrolled to the bottom on each refresh.

The terminal is **read-only** — input is not supported. This is a deliberate scope limit: building a full PTY emulator is a separate project, and the user's stated use case ("peek orchestration") is read-only monitoring. For interactive input, the user should use a real terminal app and `tmux attach -t <session>::<tool_id>`.

The page exposes a `stop_polling()` method that the parent `WorkspaceTab` calls when the sub-tab is closed — this prevents the `QTimer` from outliving the page widget.

### Placeholder for passive / library tools

The `_PlaceholderPage` is shown for tools that have no interactive surface (no web + no CLI). It explains that the tool "is a passive/library tool with no interactive surface. It runs in the background and is consumed by other tools." This is informational only — there is no Start button because the tool's launcher type is `passive` (no `systemd` / `tmux` / `desktop` / `lxc`).

### Placeholder for not-yet-running tools

When a web or CLI tool is staged but not running, the sub-tab shows a `_PlaceholderPage` with a **Start tool** button. The button emits `start_tool_requested(str)`, which the main window connects to a handler that finds the matching `ServiceRow` and calls `start_service()`. After 1.5 s the workspace tab auto-refreshes so the placeholder → live view switch happens automatically.

### Sub-tab labels

Each sub-tab is labeled with an emoji prefix + tool_id:

- 🌐 — web-interface tool
- ⌨ — CLI tool
- 📦 — passive / library tool
- ⏸ suffix — tool is staged but not yet running

The emoji encoding lets the user scan the tab bar at a glance and see what kind of surface each sub-tab provides.

### Sub-tab closing

Sub-tabs are closable via the standard × button. Closing a sub-tab calls `stop_polling()` on the page (for CLI tools) but does **NOT** stop the underlying tool — that's the user's call from the Stack Editor. The empty-state placeholder is restored when all sub-tabs are closed.

## Refresh model

`WorkspaceTab.refresh()` is called from:

1. `_populate_services` (after the Stack Editor recompiles the active set)
2. Nav-click on the Workspace entry in the sidebar
3. 1.5 s after a "Start tool" click (so the placeholder → live view switch happens)

The refresh is **destructive** — all sub-tabs are torn down and rebuilt. This is simpler than diffing the active set, and the user's mental model is "refresh = rebuild." A future improvement would be to preserve sub-tab order and only add/remove the delta.

## Consequences

### Positive

- Every active tool is reachable from a single window — no context-switch to a browser or terminal app.
- Web tools embed directly via QWebEngineView, which is the standard PySide6 solution and ships with most PySide6 installs.
- CLI tools attach to the existing tmux session that the runtime executor already manages — no new process lifecycle to worry about.
- The "Start tool" button on placeholder pages bridges the gap between staging and running without requiring the user to switch to the Stack Editor.
- The servo-swap path is documented so a future servo migration is a one-line change.

### Negative

- The CLI embedding is read-only. Users who want interactive input must still use a real terminal app. This is a deliberate scope limit, not a bug.
- The `tmux capture-pane` poll runs every 250 ms per CLI sub-tab. With 10 CLI tools open, that's 40 Hz of subprocess calls — measurable but not heavy. A future improvement would be to pause polling when the sub-tab is not visible.
- The web embedding depends on `QtWebEngine`, which is a separate package on some Linux distros. The fallback placeholder handles the missing-package case gracefully.
- The destructive refresh model means sub-tab order is not preserved across refreshes. A future improvement would be to preserve order.

### Neutral

- The emoji prefixes (🌐 ⌨ 📦 ⏸) are not accessible to screen readers. A future improvement would be to add `setAccessibleName` on each sub-tab.

## Alternatives considered

### Open tools in an external browser / terminal

Rejected — this is the v3.0 behavior the user explicitly asked to replace. The whole point of the Workspace tab is to eliminate the context-switch.

### Use servo instead of QWebEngineView

Rejected as the default because servo's Python bindings are not production-ready and have no first-class PySide6 integration. The module is structured so servo can be swapped in later as a one-line change to `_make_web_view()`.

### Build a full PTY emulator for CLI tools

Rejected as scope creep. The user's stated use case is "peek orchestration" — read-only monitoring. A full PTY emulator is a separate project. For interactive input, the user should `tmux attach` from a real terminal.

### One workspace per tool (separate windows)

Rejected — this would re-create the multi-window juggling the app is supposed to eliminate. The single-window, multi-tab model matches the virt-manager / aqemu reference the user cited.

## Future work

- Preserve sub-tab order across refreshes.
- Pause `tmux capture-pane` polling when the sub-tab is not visible.
- Add `setAccessibleName` to each sub-tab for screen-reader support.
- Add a "Detach" button on each sub-tab that opens the tool in an external browser / terminal (for when the user does want a separate window).
- Swap in servo for web embedding once servo's Python bindings are production-ready.
- Add interactive input to the CLI embedding (would require a real PTY, e.g. via `QProcess` + `QTerminal` or a third-party widget).
