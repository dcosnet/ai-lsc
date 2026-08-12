"""
AI-LSC — Chat API thread-pool worker.

Isolates all network I/O (Ollama ``/api/chat`` endpoint) from the GUI
main loop using Qt's ``QThreadPool`` + ``QRunnable`` pattern.

Architecture
------------
``ApiRunnable`` is submitted to the thread pool.  When the HTTP call
completes (or fails), results are delivered back to the main thread
via ``WorkerSignals.result`` — a Qt Signal that the UI connects to
with a slot running on the main thread.

No UI widgets are imported here; only ``PySide6.QtCore`` for the
Signal / Runnable machinery.

Availability
-------------
If PySide6 is not installed this module still imports successfully but
``WorkerSignals`` and ``ApiRunnable`` will be ``None``.  The top-level
``__init__.py`` handles this gracefully.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)

try:
    from PySide6.QtCore import QObject, QRunnable, Signal
    _HAS_QT = True
except ImportError:
    _HAS_QT = False


# ── Signal emitter (thread-safe bridge to main loop) ───────────────────

if _HAS_QT:
    class WorkerSignals(QObject):
        """Emits results from a background thread back to the main thread.

        ``result`` carries three values:
            1. ``identity`` (str) — display name for the response source.
            2. ``reply``    (str) — the assistant's response or error message.
            3. ``history_append`` (str | None) — text to append to the chat
               history, or *None* if the response was an error.
        """
        result = Signal(str, str, object)


# ── API runnable ─────────────────────────────────────────────────────

if _HAS_QT:
    class ApiRunnable(QRunnable):
        """Background task that calls the Ollama ``/api/chat`` endpoint.

        Parameters
        ----------
        model_id :
            Model identifier string passed to the Ollama API (e.g.
            ``"llama3:8b"``).
        port_id :
            Port number of the running Ollama server.
        history_snapshot :
            List of ``{"role": …, "content": …}`` message dicts sent as
            the conversation history.
        temperature :
            Sampling temperature (0.0–2.0).
        max_tokens :
            Maximum tokens to generate (``num_predict`` in Ollama API).
        timeout :
            HTTP request timeout in seconds.
        """

        def __init__(
            self,
            model_id: str,
            port_id: int,
            history_snapshot: list[dict],
            temperature: float = 0.7,
            max_tokens: int = 4096,
            timeout: float = 120.0,
        ) -> None:
            super().__init__()
            # L-06: validate port range up-front so an invalid port
            # surfaces a clean ValueError instead of a cryptic URLError
            # when we try to construct the URL below.
            if not isinstance(port_id, int) or not 1 <= port_id <= 65535:
                raise ValueError(f"invalid port_id: {port_id!r}")
            self.model_id = model_id
            self.port_id = port_id
            self.history_snapshot = history_snapshot
            self.temperature = temperature
            self.max_tokens = max_tokens
            self.timeout = timeout
            self.signals = WorkerSignals()
            self.setAutoDelete(True)

        def run(self) -> None:
            identity, reply, history_append = self.model_id, "", None
            try:
                url = f"http://127.0.0.1:{self.port_id}/api/chat"
                payload = json.dumps({
                    "model": self.model_id,
                    "messages": self.history_snapshot,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    },
                }).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    reply = data.get("message", {}).get("content", "").strip()

                if not reply:
                    identity, reply = "? System Guard", (
                        "Received empty execution token from model. "
                        "Core might lack system context space allocation."
                    )
                else:
                    history_append = reply

            except urllib.error.HTTPError as he:
                identity = "? Ollama Stack Exception"
                err_body = self._safe_read_error(he)
                # H-10: surface only a short, generic reason to the user;
                # log the full body server-side instead of echoing it back.
                logger.warning(
                    "Ollama HTTP %s on /api/chat (model=%s): %s",
                    he.code, self.model_id, err_body,
                )
                reply = (
                    f"Ollama Engine rejected execution layout "
                    f"(Code {he.code}).\n\n"
                    f"[Reason]: {self._short_reason(err_body)}\n\n"
                    "*Troubleshooting:*\n"
                    "1. Did you click 'Build/Register Selected Skills' first?\n"
                    "2. Ensure the base model has been pulled."
                )

            except urllib.error.URLError as ue:
                identity = "? Cluster Port Offline"
                # H-10: do not echo connection details; categorize instead.
                reason = self._categorize_url_error(ue)
                logger.warning(
                    "Ollama unreachable on port %s: %s",
                    self.port_id, ue.reason,
                )
                reply = (
                    f"Failed to connect to Ollama API on port "
                    f"[{self.port_id}].\n\n"
                    f"[Details]: {reason}\n\n"
                    "*Action Required*: Verify Ollama is [ LIVE ] on Dashboard."
                )

            except (OSError, ValueError, json.JSONDecodeError) as e:
                identity = "? Exception Tracker"
                logger.warning("Background chat interruption: %s", e)
                reply = (
                    "Unhandled background interruption in chat worker. "
                    "Check the application log for details."
                )

            self.signals.result.emit(identity, reply, history_append)

        @staticmethod
        def _safe_read_error(http_error) -> str:
            """Best-effort extraction of the error body from an HTTP error."""
            try:
                body = json.loads(
                    http_error.read().decode("utf-8", errors="ignore")
                )
                return body.get("error", str(body))
            except (OSError, ValueError, json.JSONDecodeError):
                return "Internal structural parser issue."

        @staticmethod
        def _short_reason(err_body: str) -> str:
            """Return a short, user-safe summary of an Ollama error body."""
            if not err_body:
                return "no detail available"
            # Trim to first line and 120 chars; drop any URLs / paths.
            first_line = str(err_body).splitlines()[0]
            return first_line[:120]

        @staticmethod
        def _categorize_url_error(ue: urllib.error.URLError) -> str:
            """Map a URLError reason to a generic user-safe category."""
            reason = str(ue.reason).lower()
            if "refused" in reason or "connection" in reason:
                return "connection refused (is the service running?)"
            if "timeout" in reason or "timed out" in reason:
                return "request timed out"
            if "name" in reason or "resolve" in reason:
                return "DNS resolution failed"
            return "network error"
else:
    WorkerSignals = None  # type: ignore[assignment, misc]
    ApiRunnable = None    # type: ignore[assignment, misc]
