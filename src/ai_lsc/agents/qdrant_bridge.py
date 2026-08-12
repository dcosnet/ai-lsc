"""
AI-LSC — Qdrant vector memory bridge.

Provides the Qdrant vector database integration for the Agentic OS
semantic memory layer, handling:

    - **Collection management**: Create, list, and delete vector collections.
    - **Point operations**: Upsert, search, and delete vectors with payloads.
    - **Embedding generation**: Use Ollama embedding models for vectorization.
    - **Skill matching**: Semantic search over skill descriptions.
    - **RAG pipeline**: Retrieve relevant context for document analysis.

Qdrant serves as the **semantic path** (vector search, RAG), while Redis
handles the hot path and MariaDB handles cold persistence.

Usage
-----
    bridge = QdrantBridge(qdrant_port=6333, ollama_port=11434)
    bridge.create_collection("documents", dimension=384)
    bridge.upsert_points("documents", points)
    results = bridge.search("documents", query="quarterly report", limit=5)
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from ai_lsc.utils.logging import get_logger

logger = get_logger(__name__)


class QdrantBridge:
    """Bridge to Qdrant for semantic vector operations.

    Uses Qdrant's REST API directly via urllib to maintain the same
    zero-hard-dependency pattern as the rest of the agents package.
    Falls back gracefully when Qdrant is not running.

    Parameters
    ----------
    qdrant_host :
        Qdrant server hostname.
    qdrant_port :
        Qdrant HTTP API port.
    ollama_port :
        Ollama port for embedding generation.
    default_embedding_model :
        Ollama model to use for embeddings.
    timeout :
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        qdrant_host: str = "127.0.0.1",
        qdrant_port: int = 6333,
        ollama_port: int = 11434,
        default_embedding_model: str = "nomic-embed-text",
        timeout: float = 30.0,
    ) -> None:
        self.qdrant_url = f"http://{qdrant_host}:{qdrant_port}"
        self.ollama_url = f"http://127.0.0.1:{ollama_port}"
        self.embedding_model = default_embedding_model
        self.timeout = timeout

    def _qdrant_request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Make a request to the Qdrant REST API."""
        url = f"{self.qdrant_url}{path}"
        payload = json.dumps(data).encode("utf-8") if data else None
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method=method,
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status in (200, 201):
                    content = resp.read().decode("utf-8")
                    return json.loads(content) if content else {}
                logger.warning("Qdrant %s %s returned %d", method, path, resp.status)
                return None
        except urllib.error.URLError as exc:
            logger.debug("Qdrant not reachable: %s", exc)
            return None
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.error("Qdrant request failed: %s %s: %s", method, path, exc)
            return None

    # ── Collection Management ──────────────────────────────────────────

    def _probe_embedding_dimension(self) -> int | None:
        """H-24: probe the live embedding model's dimension by embedding a
        short sentinel string.  Returns ``None`` if the model is not
        reachable.
        """
        sentinel = self._embed("dimension-probe")
        if sentinel:
            return len(sentinel)
        return None

    def create_collection(
        self,
        name: str,
        dimension: int | None = None,
        distance: str = "cosine",
    ) -> bool:
        """Create a new vector collection.

        Parameters
        ----------
        name :
            Collection name.
        dimension :
            Vector dimensionality (depends on embedding model).  If
            ``None``, the dimension is probed dynamically from the
            configured embedding model (H-24).
        distance :
            Distance metric: "cosine", "euclid", or "dot".

        L-08: if the collection already exists, this method returns
        ``False`` and logs the existing collection's actual dimension
        so a dimension mismatch is never silently hidden.
        """
        if dimension is None:
            dimension = self._probe_embedding_dimension()
        if not dimension:
            logger.error(
                "Cannot create collection %s: no embedding dimension "
                "available (is Ollama running with model %s?)",
                name, self.embedding_model,
            )
            return False
        # L-08: check if the collection already exists and surface the
        # existing dimension; do NOT silently return success.
        if name in self.list_collections():
            info = self.collection_info(name) or {}
            existing_dim = (
                info.get("result", {})
                .get("config", {})
                .get("params", {})
                .get("vectors", {})
                .get("size")
            )
            if existing_dim and existing_dim != dimension:
                logger.error(
                    "Collection %s already exists with dim=%d, "
                    "requested dim=%d — delete and recreate to change "
                    "the dimension.",
                    name, existing_dim, dimension,
                )
                return False
            logger.info(
                "Collection %s already exists (dim=%d); not recreated.",
                name, existing_dim or dimension,
            )
            return True
        result = self._qdrant_request("PUT", f"/collections/{name}", {
            "vectors": {
                "size": dimension,
                "distance": distance,
            },
        })
        if result is not None:
            logger.info("Created collection: %s (dim=%d, dist=%s)", name, dimension, distance)
            return True
        return False

    def list_collections(self) -> list[str]:
        """Return names of all collections."""
        result = self._qdrant_request("GET", "/collections")
        if result:
            return [c["name"] for c in result.get("collections", [])]
        return []

    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        result = self._qdrant_request("DELETE", f"/collections/{name}")
        return result is not None

    def collection_info(self, name: str) -> dict[str, Any] | None:
        """Get detailed info about a collection."""
        return self._qdrant_request("GET", f"/collections/{name}")

    # ── Point Operations ───────────────────────────────────────────────

    def upsert_points(
        self,
        collection: str,
        points: list[dict[str, Any]],
    ) -> bool:
        """Upsert points (vectors + payloads) into a collection.

        Each point dict should have:
            - "id": str or int — unique point ID
            - "vector": list[float] — the embedding
            - "payload": dict — arbitrary metadata
        """
        result = self._qdrant_request("PUT", f"/collections/{collection}/points", {
            "points": points,
        })
        return result is not None

    def search(
        self,
        collection: str,
        query_vector: list[float] | None = None,
        query_text: str = "",
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors in a collection.

        Parameters
        ----------
        collection :
            Collection to search in.
        query_vector :
            Pre-computed embedding vector. If None, query_text is embedded.
        query_text :
            Text to embed and search with (used if query_vector is None).
        limit :
            Maximum results to return.
        filters :
            Optional Qdrant filter payload.
        """
        if query_vector is None and query_text:
            query_vector = self._embed(query_text)
        if query_vector is None:
            return []

        search_body: dict[str, Any] = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": True,
        }
        if filters:
            search_body["filter"] = filters

        result = self._qdrant_request(
            "POST", f"/collections/{collection}/points/search", search_body
        )
        if result:
            return result.get("result", [])
        return []

    def delete_points(
        self,
        collection: str,
        point_ids: list[str | int],
    ) -> bool:
        """Delete specific points from a collection."""
        result = self._qdrant_request(
            "POST",
            f"/collections/{collection}/points/delete",
            {"points": [{"id": pid} for pid in point_ids]},
        )
        return result is not None

    def count_points(self, collection: str) -> int:
        """Return the number of points in a collection."""
        result = self._qdrant_request(
            "POST", f"/collections/{collection}/points/count", {}
        )
        if result:
            return result.get("result", {}).get("count", 0)
        return 0

    # ── Embedding Generation ───────────────────────────────────────────

    def _embed(self, text: str) -> list[float] | None:
        """Generate an embedding vector using Ollama's embedding API."""
        payload = json.dumps({
            "model": self.embedding_model,
            "prompt": text,
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                f"{self.ollama_url}/api/embeddings",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("embedding")
        except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as exc:
            logger.error("Embedding generation failed: %s", exc)
            return None

    def embed_batch(self, texts: list[str]) -> list[list[float] | None]:
        """Generate embeddings for multiple texts.

        Returns a list aligned with the input texts.  M-38: uses a
        thread pool so independent HTTP requests run concurrently.
        """
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(8, max(1, len(texts)))) as pool:
            return list(pool.map(self._embed, texts))

    # ── Skill Matching (semantic) ───────────────────────────────────────

    def index_skills(
        self,
        skills: list[dict[str, Any]],
        collection: str = "skills",
    ) -> bool:
        """Index skill descriptions for semantic matching.

        Parameters
        ----------
        skills :
            List of skill dicts with "name", "description", and optional "triggers".
        collection :
            Collection to store skill vectors.
        """
        # Create collection if it doesn't exist
        if collection not in self.list_collections():
            # H-24: probe the embedding dimension dynamically rather
            # than hardcoding 768.
            if not self.create_collection(collection, dimension=None):
                return False

        points = []
        for skill in skills:
            # Combine name, description, and triggers for embedding
            text_parts = [skill.get("name", ""), skill.get("description", "")]
            triggers = skill.get("triggers", [])
            if triggers:
                text_parts.append(" ".join(triggers))
            text = " ".join(text_parts)

            vector = self._embed(text)
            if vector is None:
                continue

            points.append({
                "id": skill.get("name", ""),
                "vector": vector,
                "payload": {
                    "name": skill.get("name", ""),
                    "description": skill.get("description", ""),
                    "category": skill.get("category", ""),
                    "required_tools": skill.get("required_tools", []),
                    "triggers": triggers,
                },
            })

        if points:
            return self.upsert_points(collection, points)
        return False

    def find_similar_skills(
        self,
        query: str,
        collection: str = "skills",
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Find skills semantically similar to a query."""
        results = self.search(collection, query_text=query, limit=limit)
        return [
            {
                "name": r.get("payload", {}).get("name", ""),
                "description": r.get("payload", {}).get("description", ""),
                "score": r.get("score", 0.0),
                "category": r.get("payload", {}).get("category", ""),
                "required_tools": r.get("payload", {}).get("required_tools", []),
            }
            for r in results
        ]

    # ── Health Check ───────────────────────────────────────────────────

    def health_check(self) -> dict[str, Any]:
        """Return Qdrant connection health status."""
        result = self._qdrant_request("GET", "/collections")
        connected = result is not None
        collections = []
        if result:
            collections = [c["name"] for c in result.get("collections", [])]
        return {
            "connected": connected,
            "collections": collections,
            "embedding_model": self.embedding_model,
        }
