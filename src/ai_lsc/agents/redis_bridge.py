"""
AI-LSC — Redis hot-path bridge.

Provides the Redis integration for the Agentic OS memory layer,
handling the hot-path concerns that need sub-millisecond latency:

    - **Task Queue**: FIFO queue for agent task dispatch and coordination.
    - **Pub/Sub**: Real-time event broadcasting for inter-agent communication.
    - **Status Cache**: TTL-based caching of service status and health checks.
    - **Lock Management**: Distributed locks for preventing concurrent conflicts.

Redis serves as the **hot path** (real-time, volatile), while MariaDB handles
the **cold path** (persistent audit logs, task memory, config) and Qdrant
handles the **semantic path** (vector search, RAG).

Usage
-----
    bridge = RedisBridge(port=6379)
    bridge.enqueue_task("rag-pipeline", {"query": " quarterly report"})
    bridge.publish_event("service_started", {"tool_id": "qdrant"})
    bridge.cache_status("qdrant", {"running": True, "port": 6333}, ttl=30)
"""

from __future__ import annotations

import json
import time
from typing import Any

from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)

# Channel names for pub/sub
_CHANNELS = {
    "service_events": "ai_lsc:events:service",
    "agent_events": "ai_lsc:events:agent",
    "task_events": "ai_lsc:events:task",
    "model_events": "ai_lsc:events:model",
    "skill_events": "ai_lsc:events:skill",
}

# Key prefixes for organized data
_KEY_PREFIXES = {
    "task_queue": "ai_lsc:queue:",
    "task_payload": "ai_lsc:payload:",
    "status_cache": "ai_lsc:status:",
    "task_result": "ai_lsc:result:",
    "lock": "ai_lsc:lock:",
    "agent_state": "ai_lsc:agent:",
    "model_pool": "ai_lsc:pool:",
}


class RedisBridge:
    """Bridge to Redis for hot-path agentic operations.

    Uses raw ``redis-py`` for direct Redis protocol access.
    Falls back to a no-op stub when redis-py is not installed.

    Parameters
    ----------
    host :
        Redis server hostname.
    port :
        Redis server port.
    db :
        Redis database number (default 0).
    """
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        db: int = 0,
    ) -> None:
        self.host = host
        self.port = port
        self.db = db
        self._client = None
        self._pubsub = None
        self._connected = False
        self._try_connect()

    def _try_connect(self) -> None:
        """Attempt to connect to Redis. Graceful degradation if unavailable."""
        try:
            import redis as redis_lib
            self._client = redis_lib.Redis(
                host=self.host, port=self.port, db=self.db,
                decode_responses=True, socket_timeout=5,
            )
            self._client.ping()
            self._connected = True
            logger.info("Redis connected at %s:%d", self.host, self.port)
        except ImportError:
            logger.warning("redis-py not installed — Redis features disabled")
        except Exception as exc:
            logger.warning("Redis not available at %s:%d: %s", self.host, self.port, exc)

    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None

    # ── Task Queue ─────────────────────────────────────────────────────

    def enqueue_task(
        self,
        queue_name: str,
        task_data: dict[str, Any],
        priority: int = 0,
    ) -> str | None:
        """Add a task to a named queue.

        Parameters
        ----------
        queue_name :
            Logical queue name (e.g. "rag-pipeline", "code-review").
        task_data :
            Task payload dict.
        priority :
            Higher priority tasks are processed first.

        Returns
        -------
        Task ID string, or None if Redis is unavailable.
        """
        if not self.is_connected:
            return None

        task_id = f"{queue_name}:{int(time.time() * 1000)}"
        task_data["_task_id"] = task_id
        task_data["_enqueued_at"] = time.time()
        task_data["_priority"] = priority

        key = f"{_KEY_PREFIXES['task_queue']}{queue_name}"
        payload = json.dumps(task_data)

        try:
            # M-29: use task_id as the sorted-set member (not the full
            # payload) so two tasks with identical JSON don't collide.
            # The payload lives in a separate hash keyed by task_id.
            self._client.zadd(key, {task_id: -priority})
            self._client.hset(
                f"{_KEY_PREFIXES['task_payload']}{queue_name}",
                task_id,
                payload,
            )
            logger.info("Enqueued task %s to queue '%s' (priority=%d)", task_id, queue_name, priority)
            return task_id
        except Exception as exc:
            logger.error("Failed to enqueue task: %s", exc)
            return None

    def dequeue_task(self, queue_name: str) -> dict[str, Any] | None:
        """Pop the highest-priority task from a queue."""
        if not self.is_connected:
            return None

        key = f"{_KEY_PREFIXES['task_queue']}{queue_name}"
        try:
            # Get highest priority (lowest negative score)
            result = self._client.zpopmin(key, count=1)
            if not result:
                return None
            task_id, _ = result[0]
            # M-29: pull the payload out of the side hash.
            payload = self._client.hget(
                f"{_KEY_PREFIXES['task_payload']}{queue_name}",
                task_id,
            )
            if not payload:
                return None
            self._client.hdel(
                f"{_KEY_PREFIXES['task_payload']}{queue_name}",
                task_id,
            )
            return json.loads(payload)
        except Exception as exc:
            logger.error("Failed to dequeue task: %s", exc)
            return None

    def queue_length(self, queue_name: str) -> int:
        """Return the number of pending tasks in a queue."""
        if not self.is_connected:
            return 0
        key = f"{_KEY_PREFIXES['task_queue']}{queue_name}"
        try:
            return self._client.zcard(key)
        except Exception:
            return 0

    # ── Pub/Sub ────────────────────────────────────────────────────────

    def publish_event(
        self,
        event_type: str,
        data: dict[str, Any],
    ) -> bool:
        """Publish an event to the appropriate channel.

        Parameters
        ----------
        event_type :
            One of the channel types (service_events, agent_events, etc.)
        data :
            Event payload.
        """
        if not self.is_connected:
            return False

        channel = _CHANNELS.get(event_type, _CHANNELS["service_events"])
        data["_timestamp"] = time.time()
        data["_event_type"] = event_type

        try:
            self._client.publish(channel, json.dumps(data))
            logger.debug("Published %s event", event_type)
            return True
        except Exception as exc:
            logger.error("Failed to publish event: %s", exc)
            return False

    # ── Status Cache ────────────────────────────────────────────────────

    def _cache_set(self, key: str, value: Any, ttl: int) -> bool:
        """M-17: shared setex + json.dumps helper."""
        if not self.is_connected:
            return False
        try:
            self._client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as exc:
            logger.error("Failed to set cache key %s: %s", key, exc)
            return False

    def _cache_get(self, key: str) -> Any | None:
        """M-17: shared get + json.loads helper."""
        if not self.is_connected:
            return None
        try:
            data = self._client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None

    def cache_status(
        self,
        tool_id: str,
        status_data: dict[str, Any],
        ttl: int = 30,
    ) -> bool:
        """Cache a tool's status with an expiration time.

        Parameters
        ----------
        tool_id :
            The tool identifier.
        status_data :
            Status payload (running, port, cpu, etc.).
        ttl :
            Time-to-live in seconds.
        """
        return self._cache_set(
            f"{_KEY_PREFIXES['status_cache']}{tool_id}",
            status_data,
            ttl,
        )

    def get_cached_status(self, tool_id: str) -> dict[str, Any] | None:
        """Retrieve cached status for a tool."""
        return self._cache_get(
            f"{_KEY_PREFIXES['status_cache']}{tool_id}"
        )

    # ── Task Results ───────────────────────────────────────────────────

    def store_result(
        self,
        task_id: str,
        result: dict[str, Any],
        ttl: int = 300,
    ) -> bool:
        """Store a task result for retrieval by other agents."""
        return self._cache_set(
            f"{_KEY_PREFIXES['task_result']}{task_id}",
            result,
            ttl,
        )

    def get_result(self, task_id: str) -> dict[str, Any] | None:
        """Retrieve a stored task result."""
        return self._cache_get(
            f"{_KEY_PREFIXES['task_result']}{task_id}"
        )

    # ── Lock Management ────────────────────────────────────────────────

    def acquire_lock(
        self,
        resource: str,
        ttl: int = 60,
    ) -> bool:
        """Try to acquire a distributed lock.

        Parameters
        ----------
        resource :
            Resource identifier to lock.
        ttl :
            Lock expiration in seconds.

        Returns
        -------
        True if the lock was acquired, False if already held.
        """
        if not self.is_connected:
            # H-13: do not silently bypass the lock when Redis is down.
            # Log a warning so operators know two agents could race, and
            # return True only so a single-host deployment stays usable.
            logger.warning(
                "Redis lock bypassed for %r — concurrent agents may race",
                resource,
            )
            return True

        key = f"{_KEY_PREFIXES['lock']}{resource}"
        try:
            return bool(self._client.set(key, "1", nx=True, ex=ttl))
        except Exception as exc:
            logger.error("Lock acquire failed: %s", exc)
            return True

    def release_lock(self, resource: str) -> bool:
        """Release a distributed lock."""
        if not self.is_connected:
            logger.warning(
                "Redis lock release skipped for %r — Redis is down",
                resource,
            )
            return True

        key = f"{_KEY_PREFIXES['lock']}{resource}"
        try:
            return bool(self._client.delete(key))
        except Exception:
            return False

    # ── Agent State ────────────────────────────────────────────────────

    def save_agent_state(
        self,
        agent_id: str,
        state: dict[str, Any],
    ) -> bool:
        """Persist an agent's working state to Redis."""
        if not self.is_connected:
            return False

        key = f"{_KEY_PREFIXES['agent_state']}{agent_id}"
        try:
            self._client.hset(key, mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in state.items()
            })
            return True
        except Exception as exc:
            logger.error("Failed to save agent state: %s", exc)
            return False

    def load_agent_state(self, agent_id: str) -> dict[str, Any]:
        """Load an agent's working state from Redis."""
        if not self.is_connected:
            return {}

        key = f"{_KEY_PREFIXES['agent_state']}{agent_id}"
        try:
            raw = self._client.hgetall(key)
            state: dict[str, Any] = {}
            for k, v in raw.items():
                try:
                    state[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    state[k] = v
            return state
        except Exception:
            return {}

    # ── Health Check ───────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        """Return Redis connection health status."""
        return {
            "connected": self.is_connected,
            "host": self.host,
            "port": self.port,
        }
