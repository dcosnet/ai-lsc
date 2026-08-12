# ADR-002: Pipeline Ticker

**Date:** 2026-07-07
**Status:** Accepted

## Context

When a user stages a flow of tools in the Stack Editor, the only way to verify the wiring topology is to switch to the IPC Stack tab and read the connections table. There is no at-a-glance visualization of which tools talk to which other tools, in which direction, over what interface. Debugging a misconfigured stack requires the user to mentally join the active-tools list against the registry's `deps` field and the `STACK_WIRINGS` topology — a task the tool is supposed to do for them.

The user asked for a "ticker-style scrolling status" that shows "pipeline connection and direction information per workspace view at the top" so they can "visualize what they are doing as they debug the logic for their stack."

## Decision

Add a new `PipelineTicker` widget at the top of every workspace tab (above the `QStackedWidget` so it persists across all 13+ pages).

### Data source

The ticker reads the active-tools set from `pipeline_state.json` and joins it against `STACK_WIRINGS` in `stack/connections.py`. Only edges where **both endpoints are in the active set** are rendered. Any active tool that does not appear in any edge is flagged as an orphan.

This was chosen over the alternatives (active+deps, all 124 tools, layer-filtered) because:

- **Active-only** matches the user's mental model — "what is my staged flow doing right now?"
- **Active-only** keeps the ticker readable when 20+ tools are staged; the alternatives would either drown the user in dimmed inactive edges or require an extra filter UI.
- Orphan detection is the killer feature — it surfaces real registry gaps (e.g. the `open_webui` vs `openwebui` tool_id collision) that no other view in the app exposes.

### Visual encoding

Each edge renders as `provider ──interface──▶ consumer` on a single line. The arrow color encodes the interface type via a static map (`_INTERFACE_COLORS`):

| Interface | Color | Hex |
|-----------|-------|-----|
| `openai_api` / `ollama_api` | blue | `#2563eb` |
| `vector` / `vector_search` / `embedding` | green | `#16a34a` |
| `redis_pubsub` / `redis_cache` | orange | `#ea580c` |
| `postgresql` / `mariadb` / `mysql` | purple | `#9333ea` |
| `http_api` / `websocket` / `grpc` | teal | `#0d9488` |
| `filesystem` / `tmux_socket` / `systemd_unit` | slate | `#64748b` |
| `cuda_driver` | red | `#dc2626` |
| (default) | slate | `#64748b` |

Tool pills are white when stopped, blue-100 when running. Orphan pills are red-100 with a `❗` prefix.

### Rendering approach

The ticker is a single `QWidget` subclass that paints itself via `paintEvent`. We deliberately avoided a row of `QLabel` widgets because Qt's layout system would fight the horizontal scroll animation. The scroll is driven by a `QTimer` firing every 33 ms (~30 FPS); each tick advances `self._scroll_offset` by 1 pixel. The content is drawn twice (one full copy + one wrap-ahead copy) so the scroll visually never has a gap.

### Interaction

- **Hover-pause** — `enterEvent` sets `self._hovered = True`, which short-circuits the scroll-tick handler. The user can read a long flow without it scrolling away.
- **Click-to-jump** — `mousePressEvent` hit-tests the click X coordinate against a cached list of pill rects (rebuilt during every paint). On hit, emits `tool_clicked(str)`. The main window connects this to a handler that switches to the Tools tab and calls `ToolsTab.highlight_tool(tool_id)`.

### Refresh cadence

The ticker refreshes on two events:

1. `_populate_services` (after the Stack Editor recompiles the active set)
2. `poll_services` (every 2 s service-status poll — so running-state color changes propagate immediately)

The refresh is cheap (one pass over the active set + one pass over `STACK_WIRINGS` for in-stack edges), so we did not bother with diffing — the whole edge list is rebuilt and passed to `set_edges()`.

## Consequences

### Positive

- Users can immediately see whether their staged flow is wired correctly without leaving the current tab.
- Orphan detection surfaces real registry gaps — the `open_webui` vs `openwebui` collision was found within minutes of the first simulation.
- Click-to-jump makes the ticker an active debugging aid, not just a passive display.
- The widget is self-contained (no dependencies on the rest of the UI), so it can be unit-tested in isolation once a Qt test harness is in place.

### Negative

- The ticker's value scales with how complete the `STACK_WIRINGS` data is. Currently 60 wirings for 124 tools — gaps surface as orphans, which can be noisy until the wiring data is backfilled.
- The `paintEvent`-driven rendering is more code than a QLabel row would have been, but the trade-off was necessary for smooth scrolling.
- The pill-rect hit-test cache is rebuilt on every paint, so click accuracy depends on the most recent render. Acceptable for a ticker (the user clicks what they see).

### Neutral

- The `_INTERFACE_COLORS` map is a static dict in the widget module. If the registry's interface_id conventions evolve, the map needs to be updated. A future improvement would be to derive the colors from the `ToolInterface` dataclass itself.

## Alternatives considered

### A row of QLabel widgets in a QHBoxLayout

Rejected because Qt's layout system would fight the horizontal scroll animation. We would have to either disable the layout and manually position labels (which is what `paintEvent` does, but with more code), or use a `QScrollArea` (which adds scroll bars the user didn't ask for).

### A graph view (nodes + edges) instead of a linear ticker

Rejected for the primary use case — the user explicitly asked for a "ticker-style scrolling status." A graph view is harder to fit at the top of every tab and harder to read at a glance. A larger graph view could be added as a separate "Pipeline Flow" tab in a future pass (the original ask included this as an option).

### Active+deps as the data source

Rejected because deps are a build-time concept (what the installer needs to fetch) while wirings are a runtime concept (what the running tool connects to). Mixing them would conflate two different views of the stack.

## Future work

- Backfill `STACK_WIRINGS` entries for the tools currently flagged as orphans (open_webui, qdrant, redis when staged without consumers, etc.).
- Add a "Pipeline Flow" tab with a larger graph view (nodes + edges, draggable) for users who want more detail than the ticker provides.
- Unit tests with a Qt test harness (`pytest-qt`) once the project adopts one.
- Derive arrow colors from the `ToolInterface` dataclass instead of the static `_INTERFACE_COLORS` map.
