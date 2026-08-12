"""UI widgets shared across multiple pages.

Currently exports:

* :class:`PipelineTicker` — horizontally scrolling status bar that
  visualizes the wiring topology of the currently-staged tool set.
* :class:`WorkspaceTab` — peek-style orchestration surface with one
  sub-tab per active tool (web tools embedded via QWebEngineView,
  CLI tools embedded via a tmux-attached terminal widget).
"""

from __future__ import annotations

from ai_lsc.ui.widgets.pipeline_ticker import PipelineTicker
from ai_lsc.ui.widgets.workspace_tab import WorkspaceTab

__all__ = ["PipelineTicker", "WorkspaceTab"]
