"""PipelineTicker — horizontally scrolling status bar that visualizes
the wiring topology of the currently-staged tool set.

Sits at the top of every workspace tab.  Reads the active_tools set
from the main window's pipeline state, queries
``ai_lsc.stack.connections.STACK_WIRINGS`` for the edges between them,
and renders the result as a single scrolling line of
``provider ──interface──▶ consumer`` chips.  Orphans (active tools
with no wiring to any other active tool) are flagged in red with an
"❗" prefix so the user can immediately see which tools in their
staged flow are disconnected.

Click a tool name to jump to the Tools tab and highlight that row.
Hover to pause the scroll.

Visual encoding
---------------
* Tool names: black-on-white pill, blue when running, dimmed when
  active-but-stopped.
* Arrows: colored by interface type — openai_api=blue, vector=green,
  redis_pubsub=orange, postgresql=purple, http_api=teal, default=gray.
* Orphan indicator: red "❗" before the tool name.
* Direction: ``provider ──interface──▶ consumer`` (left to right means
  "consumer pulls from provider").  The interface label is small caps
  on the arrow itself.

Implementation notes
--------------------
* The ticker is a single ``QWidget`` subclass that paints itself via
  ``paintEvent``.  We do NOT use a row of QLabel widgets because
  Qt's layout system would fight the horizontal scroll animation.
* Scroll is driven by a ``QTimer`` firing every 33 ms (~30 FPS);
  each tick advances ``self._scroll_offset`` by ``_SCROLL_PX_PER_TICK``
  pixels.  When the offset exceeds the rendered content width plus a
  gap, it wraps back to 0.
* Hover-pause is implemented via ``enterEvent`` / ``leaveEvent``.
* Click-to-jump is implemented via ``mousePressEvent`` — we hit-test
  the click X coordinate against the cached list of tool-name rects
  and emit ``tool_clicked(str)``.
"""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import (
    QEvent,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPalette,
    QPen,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

# ── Visual constants ──────────────────────────────────────────────────

_SCROLL_PX_PER_TICK = 1
_TICK_INTERVAL_MS = 33  # ~30 FPS
_TICKER_HEIGHT_PX = 34
_GAP_BETWEEN_CHIPS_PX = 18
_GAP_BETWEEN_EDGES_PX = 36
_ORPHAN_GAP_PX = 24
_H_PADDING_PX = 12
_WRAP_GAP_PX = 80  # blank space before the content repeats

# Interface type → arrow color.  Keep this in sync with the registry's
# interface_id conventions in stack/connections.py.
_INTERFACE_COLORS: dict[str, str] = {
    "openai_api": "#2563eb",       # blue
    "ollama_api": "#2563eb",
    "anthropic_api": "#7c3aed",
    "vector": "#16a34a",           # green
    "vector_search": "#16a34a",
    "embedding": "#16a34a",
    "redis_pubsub": "#ea580c",     # orange
    "redis_cache": "#ea580c",
    "postgresql": "#9333ea",       # purple
    "mariadb": "#9333ea",
    "mysql": "#9333ea",
    "sqlite": "#9333ea",
    "http_api": "#0d9488",         # teal
    "websocket": "#0d9488",
    "grpc": "#0d9488",
    "filesystem": "#64748b",       # slate
    "cuda_driver": "#dc2626",      # red
    "tmux_socket": "#475569",
    "systemd_unit": "#475569",
}
_DEFAULT_ARROW_COLOR = "#64748b"  # slate


def _arrow_color(interface_id: str) -> QColor:
    """Return the arrow color for an interface_id, falling back to slate."""
    # Try exact match first, then a prefix match (e.g. "openai_api:11434"
    # → "openai_api").
    if interface_id in _INTERFACE_COLORS:
        return QColor(_INTERFACE_COLORS[interface_id])
    prefix = interface_id.split(":")[0]
    return QColor(_INTERFACE_COLORS.get(prefix, _DEFAULT_ARROW_COLOR))


# ── Edge data structure ───────────────────────────────────────────────


class _Edge:
    """One directed edge in the ticker: provider ──interface──▶ consumer.

    Both endpoints are tool_ids; ``running_provider`` / ``running_consumer``
    are bools that drive the dim/bright rendering of the pill labels.
    """

    __slots__ = (
        "provider", "consumer", "interface_id", "purpose",
        "running_provider", "running_consumer", "is_orphan",
    )

    def __init__(
        self,
        provider: str,
        consumer: str,
        interface_id: str,
        purpose: str = "",
        running_provider: bool = False,
        running_consumer: bool = False,
        is_orphan: bool = False,
    ) -> None:
        self.provider = provider
        self.consumer = consumer
        self.interface_id = interface_id
        self.purpose = purpose
        self.running_provider = running_provider
        self.running_consumer = running_consumer
        self.is_orphan = is_orphan


# ── The widget ────────────────────────────────────────────────────────


class PipelineTicker(QWidget):
    """Horizontally scrolling ticker showing wirings between active tools.

    Signals
    -------
    tool_clicked(str)
        Emitted when the user clicks a tool-name pill.  Payload is the
        tool_id.  The main window connects this to its Tools-tab jump
        handler.
    """

    tool_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(_TICKER_HEIGHT_PX)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)

        # State
        self._edges: list[_Edge] = []
        self._orphan_tool_ids: list[str] = []
        self._scroll_offset: int = 0
        self._content_width: int = 0
        self._hovered: bool = False
        self._pill_rects: list[tuple[QRect, str]] = []  # (rect, tool_id)
        self._empty_message: str = "No active tools — stage tools in the Stack Editor to see the pipeline flow."

        # Fonts
        self._pill_font = QFont("Sans", 9)
        self._pill_font.setBold(True)
        self._arrow_font = QFont("Sans", 8)
        self._orphan_font = QFont("Sans", 9)
        self._orphan_font.setBold(True)

        # Scroll timer
        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_INTERVAL_MS)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

        # Palette — light theme by default; matches the rest of the UI.
        self._bg_color = QColor("#f1f5f9")        # slate-100
        self._border_color = QColor("#cbd5e1")    # slate-300
        self._pill_bg = QColor("#ffffff")
        self._pill_bg_running = QColor("#dbeafe")  # blue-100
        self._pill_bg_orphan = QColor("#fee2e2")  # red-100
        self._pill_text = QColor("#0f172a")       # slate-900
        self._pill_text_dim = QColor("#64748b")   # slate-500
        self._orphan_text = QColor("#b91c1c")     # red-700
        self._empty_text_color = QColor("#64748b")

    # ── Public API ───────────────────────────────────────────────────

    def set_edges(
        self,
        edges: Iterable[_Edge],
        orphan_tool_ids: Iterable[str] = (),
    ) -> None:
        """Replace the ticker's contents.

        Call this whenever the active_tools set or any tool's running
        state changes (e.g. from ``_populate_services`` /
        ``poll_services``).
        """
        self._edges = list(edges)
        self._orphan_tool_ids = list(orphan_tool_ids)
        self._scroll_offset = 0
        self._recompute_content_width()
        self.update()

    def set_empty_message(self, message: str) -> None:
        """Override the "no active tools" placeholder text."""
        self._empty_message = message
        self.update()

    def clear(self) -> None:
        """Convenience: empty the ticker."""
        self.set_edges([], [])

    # ── Painting ─────────────────────────────────────────────────────

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt API
        return QSize(400, _TICKER_HEIGHT_PX)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt API
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()

        # Background
        p.fillRect(rect, self._bg_color)
        # Bottom border (visual separator from the page below)
        p.setPen(QPen(self._border_color, 1))
        p.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        # Empty state
        if not self._edges and not self._orphan_tool_ids:
            p.setPen(self._empty_text_color)
            p.setFont(self._arrow_font)
            p.drawText(
                rect.adjusted(_H_PADDING_PX, 0, -_H_PADDING_PX, 0),
                Qt.AlignVCenter | Qt.AlignLeft,
                self._empty_message,
            )
            return

        # Reset pill hit-test cache (rebuilt during paint)
        self._pill_rects = []

        # Render content with the current scroll offset.  Content
        # repeats horizontally so the scroll looks infinite.
        y_center = rect.height() // 2
        content_w = self._content_width
        if content_w <= 0:
            return

        # Compute the effective offset (wrap modulo content_w + wrap gap)
        effective = self._scroll_offset % (content_w + _WRAP_GAP_PX)

        # Draw the content twice (one full copy + one wrap-ahead copy)
        # so the scroll visually never has a gap.
        for base_x in (-effective, -effective + content_w + _WRAP_GAP_PX):
            x = base_x + _H_PADDING_PX
            # Edges first (provider ──▶ consumer)
            for edge in self._edges:
                x = self._draw_edge(p, x, y_center, edge)
                x += _GAP_BETWEEN_EDGES_PX
            # Orphan pills at the end
            for tid in self._orphan_tool_ids:
                x = self._draw_orphan(p, x, y_center, tid)
                x += _ORPHAN_GAP_PX

        p.end()

    def _draw_edge(
        self, p: QPainter, x: int, y_center: int, edge: _Edge,
    ) -> int:
        """Draw one ``provider ──interface──▶ consumer`` chip.

        Returns the new x cursor (just past the consumer pill).
        """
        # Provider pill
        x = self._draw_pill(
            p, x, y_center, edge.provider,
            running=edge.running_provider,
            register_hit=True,
        )
        # Arrow with interface label
        x = self._draw_arrow(p, x, y_center, edge.interface_id)
        # Consumer pill
        x = self._draw_pill(
            p, x, y_center, edge.consumer,
            running=edge.running_consumer,
            register_hit=True,
        )
        return x

    def _draw_pill(
        self,
        p: QPainter,
        x: int,
        y_center: int,
        tool_id: str,
        *,
        running: bool = False,
        register_hit: bool = True,
    ) -> int:
        """Draw a single tool-name pill.  Returns the new x cursor."""
        p.setFont(self._pill_font)
        fm = QFontMetrics(self._pill_font)
        text = tool_id
        text_w = fm.horizontalAdvance(text)
        text_h = fm.height()
        pill_w = text_w + 12
        pill_h = min(text_h + 6, _TICKER_HEIGHT_PX - 8)
        pill_rect = QRect(x, y_center - pill_h // 2, pill_w, pill_h)

        # Background
        bg = self._pill_bg_running if running else self._pill_bg
        p.setPen(QPen(self._border_color, 1))
        p.setBrush(bg)
        p.drawRoundedRect(pill_rect, 6, 6)

        # Text
        p.setPen(self._pill_text if running else self._pill_text_dim)
        p.drawText(
            pill_rect, Qt.AlignCenter, text,
        )

        if register_hit:
            self._pill_rects.append((pill_rect, tool_id))
        return x + pill_w

    def _draw_arrow(
        self, p: QPainter, x: int, y_center: int, interface_id: str,
    ) -> int:
        """Draw a colored arrow with the interface_id as a label."""
        color = _arrow_color(interface_id)
        # Truncate the interface label for readability
        label = interface_id
        if len(label) > 18:
            label = label[:15] + "…"

        p.setFont(self._arrow_font)
        fm = QFontMetrics(self._arrow_font)
        label_w = fm.horizontalAdvance(label)
        arrow_w = 24  # the ──▶ glyph space
        total_w = label_w + arrow_w + 8

        # Draw the line
        p.setPen(QPen(color, 2))
        line_y = y_center
        p.drawLine(x, line_y, x + total_w - 6, line_y)
        # Arrowhead
        head = [
            QPoint(x + total_w - 6, line_y),
            QPoint(x + total_w - 12, line_y - 4),
            QPoint(x + total_w - 12, line_y + 4),
        ]
        p.setBrush(color)
        p.drawPolygon(head)

        # Label above the line, centered
        p.setPen(color)
        label_rect = QRect(x, line_y - 16, total_w, 14)
        p.drawText(label_rect, Qt.AlignCenter, label)

        return x + total_w

    def _draw_orphan(
        self, p: QPainter, x: int, y_center: int, tool_id: str,
    ) -> int:
        """Draw a red ❗ prefixed orphan pill."""
        p.setFont(self._orphan_font)
        fm = QFontMetrics(self._orphan_font)
        marker = "❗"
        marker_w = fm.horizontalAdvance(marker)
        p.setPen(self._orphan_text)
        p.drawText(
            QRect(x, y_center - 10, marker_w + 4, 14),
            Qt.AlignCenter, marker,
        )
        x += marker_w + 4
        # The pill itself uses the orphan background
        text = tool_id
        text_w = fm.horizontalAdvance(text)
        pill_w = text_w + 12
        pill_h = min(fm.height() + 6, _TICKER_HEIGHT_PX - 8)
        pill_rect = QRect(x, y_center - pill_h // 2, pill_w, pill_h)
        p.setPen(QPen(self._orphan_text, 1))
        p.setBrush(self._pill_bg_orphan)
        p.drawRoundedRect(pill_rect, 6, 6)
        p.setPen(self._orphan_text)
        p.drawText(pill_rect, Qt.AlignCenter, text)
        self._pill_rects.append((pill_rect, tool_id))
        return x + pill_w

    # ── Layout / scroll math ─────────────────────────────────────────

    def _recompute_content_width(self) -> None:
        """Pre-compute the total width of one full copy of the content."""
        fm_pill = QFontMetrics(self._pill_font)
        fm_arrow = QFontMetrics(self._arrow_font)
        fm_orphan = QFontMetrics(self._orphan_font)
        total = 0
        for edge in self._edges:
            total += fm_pill.horizontalAdvance(edge.provider) + 12
            label = edge.interface_id
            if len(label) > 18:
                label = label[:15] + "…"
            total += fm_arrow.horizontalAdvance(label) + 24 + 8
            total += fm_pill.horizontalAdvance(edge.consumer) + 12
            total += _GAP_BETWEEN_EDGES_PX
        for tid in self._orphan_tool_ids:
            total += fm_orphan.horizontalAdvance("❗") + 4
            total += fm_orphan.horizontalAdvance(tid) + 12
            total += _ORPHAN_GAP_PX
        self._content_width = total

    # ── Scroll timer ─────────────────────────────────────────────────

    def _on_tick(self) -> None:
        if self._hovered or not self._edges and not self._orphan_tool_ids:
            return
        self._scroll_offset += _SCROLL_PX_PER_TICK
        self.update()

    # ── Interaction ──────────────────────────────────────────────────

    def enterEvent(self, event: QEvent) -> None:  # noqa: N802 - Qt API
        self._hovered = True
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:  # noqa: N802 - Qt API
        self._hovered = False
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API
        if event.button() != Qt.LeftButton:
            return
        # Hit-test against the cached pill rects.  The cache is rebuilt
        # on every paint, so this is only accurate for the most recent
        # render — acceptable for a ticker.
        pt = event.position().toPoint() if hasattr(event, "position") else event.pos()
        for rect, tool_id in self._pill_rects:
            if rect.contains(pt):
                self.tool_clicked.emit(tool_id)
                return
        super().mousePressEvent(event)


__all__ = ["PipelineTicker"]
