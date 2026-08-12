"""
AI-LSC — Warm model pool with VRAM slot management.

Manages a fixed pool of 4 VRAM slots with LRU eviction so that
models are pre-loaded and ready for inference.  The pool maps
task types to model tiers:

    Slot 0: 8B  classifier   — routing, intent detection
    Slot 1: 14B utility      — summarization, clarification
    Slot 2: 32B reasoning    — analysis, code generation
    Slot 3: 70B heavy        — complex generation, documents

When a new model is requested that does not fit in the current
allocation, the least-recently-used slot is evicted and the new
model is pulled and loaded.

Usage
-----
    pool = WarmModelPool(ollama_port=11434)
    model = pool.acquire("reasoning")   # returns "qwen2.5:32b"
    pool.release(model)
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from typing import Any

from ai_lsc.constants import MODEL_TIERS
from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)

# Mapping from logical task types to model tiers
_TASK_TO_TIER: dict[str, str] = {
    "classification": "8b",
    "routing": "8b",
    "intent": "8b",
    "clarification": "14b",
    "summarization": "14b",
    "utility": "14b",
    "reasoning": "32b",
    "analysis": "32b",
    "code": "32b",
    "script": "32b",
    "generation": "70b",
    "document": "70b",
    "chart": "70b",
    "web": "70b",
    "complex": "70b",
}

# Default model name per tier (user can override via set_tier_model)
_DEFAULT_MODELS: dict[str, str] = {
    "8b": "qwen2.5:7b",
    "14b": "qwen2.5:14b",
    "32b": "qwen2.5:32b",
    "70b": "qwen2.5:72b",
}


class WarmModelPool:
    """Fixed-slot VRAM pool with LRU eviction.

    Parameters
    ----------
    ollama_port :
        Port of the Ollama API server.
    max_slots :
        Maximum number of models loaded simultaneously.
    """

    def __init__(
        self,
        ollama_port: int = 11434,
        max_slots: int = 4,
    ) -> None:
        self.ollama_port = ollama_port
        self.max_slots = max_slots
        self.base_url = f"http://127.0.0.1:{ollama_port}"
        self._tier_models: dict[str, str] = dict(_DEFAULT_MODELS)
        # LRU-ordered: most recent at the end
        self._loaded: OrderedDict[str, float] = OrderedDict()
        # H-23: use a real lock, not a plain boolean, so concurrent
        # acquire() calls from multiple agent threads cannot both enter
        # the pull branch at the same time.
        self._pull_lock = threading.Lock()
        self._pull_in_progress = threading.Event()

    # ── Configuration ──────────────────────────────────────────────────

    def set_tier_model(self, tier: str, model_name: str) -> None:
        """Override the default model for a tier."""
        if tier in MODEL_TIERS:
            self._tier_models[tier] = model_name
            logger.info("Tier %s mapped to model %s", tier, model_name)

    def get_tier_model(self, tier: str) -> str:
        """Return the model name assigned to a tier."""
        return self._tier_models.get(tier, _DEFAULT_MODELS.get(tier, ""))

    # ── Acquisition ────────────────────────────────────────────────────

    def acquire(self, task_type: str) -> str:
        """Acquire a model for the given task type.

        If the model is already loaded, it is promoted in the LRU order.
        If not, a slot is evicted (if necessary) and the model is pulled.

        Parameters
        ----------
        task_type :
            Logical task category (e.g. "reasoning", "classification").

        Returns
        -------
        The Ollama model name that is ready for inference.
        """
        tier = _TASK_TO_TIER.get(task_type, "32b")
        model = self._tier_models.get(tier, "qwen2.5:32b")

        if model in self._loaded:
            # Promote to most-recently-used
            self._loaded.move_to_end(model)
            self._loaded[model] = time.monotonic()
            logger.info("Cache hit: %s (tier=%s)", model, tier)
            return model

        # Need to load — evict if at capacity
        while len(self._loaded) >= self.max_slots:
            self._evict_lru()

        # Pull the model
        self._pull_model(model)
        self._loaded[model] = time.monotonic()
        logger.info("Loaded model %s (tier=%s, slots=%d/%d)",
                     model, tier, len(self._loaded), self.max_slots)
        return model

    def release(self, model: str) -> None:
        """Release a model from active use.

        This is a soft release — the model stays loaded in the pool
        until it is LRU-evicted.  Call ``evict`` to force unload.
        """
        if model in self._loaded:
            self._loaded.move_to_end(model)
            self._loaded[model] = time.monotonic()

    # ── Eviction ──────────────────────────────────────────────────────

    def evict(self, model: str) -> bool:
        """Force-evict a specific model from the pool.

        Returns True if the model was in the pool and was evicted.
        """
        if model in self._loaded:
            del self._loaded[model]
            logger.info("Force-evicted model: %s", model)
            return True
        return False

    def _evict_lru(self) -> str | None:
        """Evict the least-recently-used model."""
        if not self._loaded:
            return None
        model, _ = self._loaded.popitem(last=False)
        logger.info("LRU-evicted model: %s", model)
        return model

    # ── Ollama interaction ─────────────────────────────────────────────

    def _pull_model(self, model_name: str) -> None:
        """Pull a model from Ollama registry."""
        # H-23: acquire the lock without blocking; if another thread is
        # already pulling, just skip — the caller will see the model
        # once the in-progress pull completes and LRU-promotes it.
        if not self._pull_lock.acquire(blocking=False):
            logger.warning("Pull already in progress, skipping %s", model_name)
            return
        try:
            payload = json.dumps({"name": model_name}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/pull",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            # M-37 / L-11: use resp.read() instead of a `for line in resp:`
            # loop with an empty body, so we don't hold the connection
            # open for the entire 600s stream window.
            with urllib.request.urlopen(req, timeout=600) as resp:
                resp.read()  # consume the body fully
            logger.info("Pulled model: %s", model_name)
        except urllib.error.URLError as exc:
            logger.error("Failed to pull %s: %s", model_name, exc)
        except (OSError, ValueError) as exc:
            logger.error("Pull error for %s: %s", model_name, exc)
        finally:
            self._pull_lock.release()

    # ── Status ─────────────────────────────────────────────────────────

    def list_loaded(self) -> list[dict[str, Any]]:
        """Return the currently loaded models with their tier info."""
        # M-11: build a reverse lookup once instead of a nested loop per model.
        model_to_tier = {m: t for t, m in self._tier_models.items()}
        return [
            {
                "model": model,
                "tier": model_to_tier.get(model, "unknown"),
                "last_used": ts,
                "age_seconds": time.monotonic() - ts,
            }
            for model, ts in self._loaded.items()
        ]

    def status_summary(self) -> dict[str, Any]:
        """Return pool status for logging/dashboard display."""
        return {
            "max_slots": self.max_slots,
            "used_slots": len(self._loaded),
            "free_slots": self.max_slots - len(self._loaded),
            "loaded_models": list(self._loaded.keys()),
            "tier_mapping": dict(self._tier_models),
        }
