"""
AI-LSC — Stack Wiring Topology.

Static definitions of how each tool in the stack connects to other tools
at the API/protocol level.  This is the *authoritative source of truth* for
the actual network topology: which tool exposes which interface (protocol,
port, API format, auth mechanism) and which tools consume that interface.

Design follows the Open Engineering template method (OE-0003):
each ``ToolInterface`` and ``Connection`` carries engineering context fields
(decision, observation, reasoning, etc.) so every wiring choice is traceable
to a documented rationale.

The companion ``StackWiring`` dataclass aggregates a tool's full wiring
surface — every interface it exposes and every external interface it consumes.

See Also
--------
registry.openengineer.schema.StandardTemplate : OE template pattern reference.
registry.defaults.DEFAULT_REGISTRY      : tool metadata (ports, deps, flags).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ── Schema version ──────────────────────────────────────────────────

CONNECTIONS_SCHEMA_VERSION: str = "1.0.0"


# ── Engineering Context mixin ──────────────────────────────────────

@dataclass
class EngineeringContext:
    """OE-0003 engineering context fields attached to every wiring element.

    These fields make every connection decision auditable and traceable.
    They follow the same nine-field pattern used in
    :class:`registry.openengineer.schema.StandardTemplate`.
    """

    decision: str = ""
    observation: str = ""
    alternatives: str = ""
    constraints: str = ""
    reasoning: str = ""
    verification: str = ""
    lineage: str = ""
    assumptions: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "decision": self.decision,
            "observation": self.observation,
            "alternatives": self.alternatives,
            "constraints": self.constraints,
            "reasoning": self.reasoning,
            "verification": self.verification,
            "lineage": self.lineage,
            "assumptions": self.assumptions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> EngineeringContext:
        return cls(**{k: data.get(k, "") for k in cls.__dataclass_fields__})


# ── ToolInterface ──────────────────────────────────────────────────

@dataclass
class ToolInterface:
    """Describes a single API surface that a tool exposes.

    Parameters
    ----------
    interface_id :
        Unique slug for this interface within the tool
        (e.g. ``"openai_api"``, ``"http_api"``).
    protocol :
        Network protocol: ``"HTTP"``, ``"HTTPS"``, ``"gRPC"``, ``"WebSocket"``,
        ``"RESP"``, ``"PostgreSQL"``, ``"TCP"``.
    api_format :
        API specification or format: ``"OpenAI"``, ``"REST"``, ``"OTLP"``,
        ``"native"``, ``"SQL"``, ``"RESP"``.
    port :
        Default TCP port number (may be overridden at launch time).
    base_path :
        URL path prefix for the API root, if applicable.
    auth :
        Authentication mechanism description (e.g. ``"Bearer token"``,
        ``"None"``).
    description :
        Human-readable summary of what this interface provides.
    context :
        OE-0003 engineering context for *why* this interface is configured
        this way.
    """

    interface_id: str
    protocol: str = "HTTP"
    api_format: str = "REST"
    port: int | None = None
    base_path: str = ""
    auth: str = "None"
    description: str = ""
    context: EngineeringContext = field(default_factory=EngineeringContext)

    def to_dict(self) -> dict[str, Any]:
        return {
            "interface_id": self.interface_id,
            "protocol": self.protocol,
            "api_format": self.api_format,
            "port": self.port,
            "base_path": self.base_path,
            "auth": self.auth,
            "description": self.description,
            "context": self.context.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolInterface:
        ctx = data.get("context", {})
        return cls(
            interface_id=data["interface_id"],
            protocol=data.get("protocol", "HTTP"),
            api_format=data.get("api_format", "REST"),
            port=data.get("port"),
            base_path=data.get("base_path", ""),
            auth=data.get("auth", "None"),
            description=data.get("description", ""),
            context=EngineeringContext.from_dict(ctx),
        )


# ── Connection ─────────────────────────────────────────────────────

@dataclass
class Connection:
    """Describes a consumer-to-provider wiring.

    Represents the fact that *this* tool (the consumer) connects to an
    interface exposed by ``target_tool``.  The consumer is implicit
    (it is the tool that owns this ``Connection`` in its ``StackWiring``).

    Parameters
    ----------
    target_tool :
        Tool ID of the provider (e.g. ``"ollama"``, ``"redis"``).
    interface_id :
        Which interface of the target tool is consumed
        (must match a ``ToolInterface.interface_id`` on the provider).
    purpose :
        What the consumer uses this connection for.
    config_key :
        The environment variable or config path the consumer uses to
        configure the connection (e.g. ``"OLLAMA_BASE_URL"``,
        ``"DATABASE_URL"``).
    required :
        Whether this connection is required for the tool to function.
    context :
        OE-0003 engineering context for *why* this connection exists.
    """

    target_tool: str
    interface_id: str
    purpose: str = ""
    config_key: str = ""
    required: bool = True
    context: EngineeringContext = field(default_factory=EngineeringContext)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_tool": self.target_tool,
            "interface_id": self.interface_id,
            "purpose": self.purpose,
            "config_key": self.config_key,
            "required": self.required,
            "context": self.context.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Connection:
        ctx = data.get("context", {})
        return cls(
            target_tool=data["target_tool"],
            interface_id=data["interface_id"],
            purpose=data.get("purpose", ""),
            config_key=data.get("config_key", ""),
            required=data.get("required", True),
            context=EngineeringContext.from_dict(ctx),
        )


# ── StackWiring ────────────────────────────────────────────────────

@dataclass
class StackWiring:
    """Complete wiring for a single tool.

    Aggregates every interface the tool exposes and every connection
    it makes to other tools.

    Parameters
    ----------
    tool_id :
        Tool identifier (matches the key in ``DEFAULT_REGISTRY``).
    layer :
        Registry layer name (e.g. ``"Engines"``).
    interfaces :
        All API surfaces this tool exposes to other tools.
    connections :
        All connections from this tool to other tools.
    context :
        OE-0003 engineering context for the tool's overall wiring design.
    """

    tool_id: str
    layer: str = ""
    interfaces: list[ToolInterface] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    context: EngineeringContext = field(default_factory=EngineeringContext)

    # ── Query helpers ───────────────────────────────────────────

    def get_interface(self, interface_id: str) -> ToolInterface | None:
        """Look up an exposed interface by ID."""
        for iface in self.interfaces:
            if iface.interface_id == interface_id:
                return iface
        return None

    def get_connections_to(self, target_tool: str) -> list[Connection]:
        """Return all connections to a specific provider tool."""
        return [c for c in self.connections if c.target_tool == target_tool]

    def required_connections(self) -> list[Connection]:
        """Return only required (non-optional) connections."""
        return [c for c in self.connections if c.required]

    # ── Serialization ───────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "layer": self.layer,
            "interfaces": [i.to_dict() for i in self.interfaces],
            "connections": [c.to_dict() for c in self.connections],
            "context": self.context.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StackWiring:
        ctx = data.get("context", {})
        return cls(
            tool_id=data["tool_id"],
            layer=data.get("layer", ""),
            interfaces=[ToolInterface.from_dict(i) for i in data.get("interfaces", [])],
            connections=[Connection.from_dict(c) for c in data.get("connections", [])],
            context=EngineeringContext.from_dict(ctx),
        )


# ── Shared engineering context presets ─────────────────────────────

# Reusable context for tools that proxy Ollama's OpenAI-compatible API.
_OLLAMA_CONSUMER_CTX = EngineeringContext(
    decision="Connect to Ollama via its OpenAI-compatible HTTP API.",
    observation="Ollama exposes /v1/chat/completions and /v1/models endpoints "
                "that are wire-compatible with the OpenAI SDK.",
    alternatives="Could use Ollama's native /api/chat and /api/generate "
                 "endpoints, but the OpenAI-compat layer provides SDK reuse.",
    constraints="Ollama must be running and have at least one model loaded.",
    reasoning="The OpenAI-compatible API is the de-facto standard for LLM "
              "serving.  Using it lets consumers reuse OpenAI client libraries "
              "with zero code changes.",
    verification="Ollama docs: https://github.com/ollama/ollama/blob/main/docs/openai.md",
    lineage="Mirrors the OpenAI API spec; adopted by Ollama, vLLM, llama.cpp.",
    assumptions="Ollama is listening on port 11434 and the consumer's "
                "network can reach it.",
)

# Context for tools that proxy through LiteLLM.
_LITELLM_CONSUMER_CTX = EngineeringContext(
    decision="Route LLM requests through LiteLLM's unified proxy.",
    observation="LiteLLM normalises the OpenAI API format across multiple "
                "backends (Ollama, vLLM, Azure, Anthropic, etc.).",
    alternatives="Direct connection to a specific inference backend, or a "
                 "custom proxy.",
    constraints="LiteLLM must be configured with at least one model route.",
    reasoning="LiteLLM provides model routing, fallback, load balancing, "
              "and cost tracking in a single proxy layer.",
    verification="LiteLLM docs: https://docs.litellm.ai/",
    lineage="LiteLLM is the standard LLM proxy for multi-provider stacks.",
    assumptions="LiteLLM is running on port 4000 with model routes configured.",
)

# Context for tools consuming vector store HTTP APIs.
_VECTOR_STORE_CONSUMER_CTX = EngineeringContext(
    decision="Connect to vector store via its native HTTP REST API.",
    observation="ChromaDB, Qdrant, and LanceDB all expose REST APIs for "
                "collection management and similarity search.",
    alternatives="Could use the Python client SDKs directly (in-process), "
                 "but the HTTP API is the standard for service-to-service.",
    constraints="The vector store must be running and have collections created.",
    reasoning="HTTP API allows the consumer to run as a separate service "
              "and scales independently of the vector store.",
    verification="Each vector store's official documentation confirms "
                 "the REST API endpoints and payload formats.",
    lineage="Standard REST API patterns; each store follows its own spec.",
    assumptions="Vector store is reachable on its default port.",
)


# ── Shared CUDA/acceleration interface ────────────────────────────
# CUDA is not a network service — it's a shared library / driver.
# We represent it as a virtual "interface" so that tools depending on it
# can express the dependency in the same wiring framework.

_CUDA_INTERFACE = ToolInterface(
    interface_id="cuda_driver",
    protocol="Native",
    api_format="CUDA",
    port=None,
    base_path="",
    auth="None",
    description="NVIDIA CUDA driver and runtime libraries. Not a network "
                "service — consumed as shared libraries (libcudart.so, "
                "libcublas.so, etc.). Tools link against CUDA at build time "
                "or load it via dlopen at runtime.",
    context=EngineeringContext(
        decision="Represent CUDA as a virtual interface for wiring consistency.",
        observation="CUDA is a driver/library dependency, not a service, "
                    "but many tools depend on it.",
        alternatives="Exclude CUDA from the wiring graph entirely.",
        constraints="NVIDIA GPU + driver must be present on the host.",
        reasoning="Including CUDA in the wiring graph lets us query "
                  "\"which tools need GPU?\" uniformly.",
        verification="nvidia-smi confirms driver and GPU availability.",
        lineage="NVIDIA CUDA Toolkit — https://developer.nvidia.com/cuda-toolkit",
        assumptions="GPU is present and CUDA toolkit is installed.",
    ),
)


# ══════════════════════════════════════════════════════════════════
# STACK WIRINGS — the static wiring topology
# ══════════════════════════════════════════════════════════════════

STACK_WIRINGS: dict[str, StackWiring] = {}


def _reg(w: StackWiring) -> StackWiring:
    """Register a StackWiring into the global dict and return it."""
    STACK_WIRINGS[w.tool_id] = w
    return w


# ──────────────────────────────────────────────────────────────────
# L1: Host Platform
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="postgresql",
    layer="Host Platform",
    interfaces=[
        ToolInterface(
            interface_id="postgresql",
            protocol="PostgreSQL",
            api_format="SQL",
            port=5432,
            auth="Username/password + optional TLS",
            description="PostgreSQL relational database server accepting "
                        "SQL queries over the PostgreSQL wire protocol.",
            context=EngineeringContext(
                decision="PostgreSQL as the primary relational store for "
                         "stack components that need persistent structured data.",
                observation="Dify, Paperless-ngx, and other tools require "
                            "a relational database for metadata, user "
                            "accounts, and document indices.",
                alternatives="MariaDB (port 3306) or SQLite (in-process).",
                constraints="Must be started before consumers.  A database "
                            "and user must be created for each consumer.",
                reasoning="PostgreSQL offers the best compatibility — Dify "
                          "and Paperless-ngx document PostgreSQL as their "
                          "preferred/required backend.",
                verification="psql -h localhost -p 5432 -U <user> -d <db>",
                lineage="PostgreSQL — https://www.postgresql.org/docs/",
                assumptions="Default postgres user and database exist.",
            ),
        ),
    ],
    connections=[],
    context=EngineeringContext(
        decision="PostgreSQL is a foundational L1 service with no upstream "
                 "dependencies.",
        observation="It is a leaf node in the wiring graph — nothing depends "
                    "on it being a consumer.",
        reasoning="Databases are data sinks; they don't initiate connections.",
    ),
))

_reg(StackWiring(
    tool_id="redis",
    layer="Host Platform",
    interfaces=[
        ToolInterface(
            interface_id="redis",
            protocol="RESP",
            api_format="RESP",
            port=6379,
            auth="Optional password (requirepass)",
            description="Redis in-memory data store accepting commands "
                        "over the RESP (REdis Serialization Protocol). "
                        "Used as a cache, message broker, and session store.",
            context=EngineeringContext(
                decision="Redis as the primary cache and message broker for "
                         "the stack.",
                observation="Dify, n8n, and Paperless-ngx use Redis for "
                            "caching, queue management, and pub/sub messaging.",
                alternatives="KeyDB (Redis-compatible fork), or in-process "
                             "caching within each tool.",
                constraints="Must be started before consumers.",
                reasoning="Redis is the most widely adopted cache/message "
                          "broker in the AI/ML ecosystem and has first-class "
                          "support in Dify and n8n.",
                verification="redis-cli ping returns PONG.",
                lineage="Redis — https://redis.io/docs/",
                assumptions="No password by default on local development.",
            ),
        ),
    ],
    connections=[],
    context=EngineeringContext(
        decision="Redis is a foundational L1 service with no upstream "
                 "dependencies.",
        observation="It is a leaf provider — tools consume it but it "
                    "consumes nothing.",
        reasoning="Caches and message brokers are infrastructure services.",
    ),
))

_reg(StackWiring(
    tool_id="mariadb",
    layer="Host Platform",
    interfaces=[
        ToolInterface(
            interface_id="mariadb",
            protocol="MySQL",
            api_format="SQL",
            port=3306,
            auth="Username/password",
            description="MariaDB relational database (MySQL-compatible wire protocol).",
            context=EngineeringContext(
                decision="MariaDB as an alternative relational database for "
                         "tools that support MySQL-family backends.",
                observation="No current stack tools have MariaDB in their "
                            "deps, but it is available as a drop-in MySQL "
                            "replacement.",
                alternatives="PostgreSQL (preferred), SQLite.",
                constraints="None currently — reserved for future use.",
                reasoning="Included for completeness as a Host Platform "
                          "foundation service.",
                verification="mariadb -h localhost -P 3306 -u <user> -p",
                lineage="MariaDB — https://mariadb.com/kb/en/",
                assumptions="Default installation with no custom config.",
            ),
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="duckdb",
    layer="Host Platform",
    interfaces=[
        ToolInterface(
            interface_id="duckdb_in_process",
            protocol="Native",
            api_format="SQL",
            port=None,
            description="In-process analytical database. No network interface — "
                        "consumed as a Python library via duckdb.connect().",
            context=EngineeringContext(
                decision="DuckDB as an in-process analytical engine.",
                observation="No stack tools currently depend on DuckDB at "
                            "the wiring level.",
                alternatives="SQLite for embedded SQL, PostgreSQL for "
                             "client-server.",
                reasoning="DuckDB excels at OLAP workloads and is available "
                          "as a Python package.",
                verification="python3 -c 'import duckdb; print(duckdb.__version__)'",
                lineage="DuckDB — https://duckdb.org/docs/",
                assumptions="Used in-process only, no network exposure.",
            ),
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="sqlite3",
    layer="Host Platform",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="SQLite3 is a CLI tool and in-process library. No network "
                 "interface to wire.",
        observation="Used as a local database for lightweight storage needs.",
        reasoning="No tool in the current stack depends on SQLite3 as a "
                  "networked service.",
    ),
))


# ──────────────────────────────────────────────────────────────────
# L2: Development Environment
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="cuda",
    layer="GPU Runtimes",
    interfaces=[_CUDA_INTERFACE],
    connections=[],
    context=EngineeringContext(
        decision="CUDA is a system-level driver/library, not a service. "
                 "Exposed as a virtual interface for wiring graph consistency.",
        observation="Many tools (vllm, unsloth, apex, cupy, heretic, turbollm, "
                    "turbovec, parakeet, forge, invokeai, nvidia_agent_skills) "
                    "depend on CUDA being installed.",
        reasoning="Including CUDA lets us track GPU dependencies in the "
                  "same framework as network services.",
    ),
))

_reg(StackWiring(
    tool_id="cupy",
    layer="Development Environment",
    interfaces=[],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU-accelerated NumPy-compatible array operations.",
            config_key="CUDA_PATH",
            required=True,
            context=EngineeringContext(
                decision="CuPy links against CUDA runtime libraries.",
                observation="CuPy requires CUDA toolkit for GPU kernel compilation.",
                reasoning="CuPy is a drop-in NumPy replacement that offloads "
                          "computation to NVIDIA GPUs.",
                lineage="CuPy — https://cupy.dev/",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="python",
    layer="Development Environment",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="Python is the runtime environment. No network wiring.",
        observation="Python is a passive dependency — tools use it as their "
                    "execution runtime.",
        reasoning="Not a service, so no interfaces or connections to define.",
    ),
))

_reg(StackWiring(
    tool_id="tree_sitter",
    layer="Development Environment",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="tree-sitter is a passive parsing library. No network wiring.",
        reasoning="Consumed as a Python library for source code parsing.",
    ),
))

_reg(StackWiring(
    tool_id="ripgrep",
    layer="Development Environment",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="ripgrep is a CLI search tool. No network wiring.",
        reasoning="Used for fast file search, not a service.",
    ),
))

_reg(StackWiring(
    tool_id="fd",
    layer="Development Environment",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="fd is a CLI file-finding tool. No network wiring.",
        reasoning="Used for fast file discovery, not a service.",
    ),
))


# ──────────────────────────────────────────────────────────────────
# L3: GPU Runtime
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="apex",
    layer="GPU Runtimes",
    interfaces=[],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="Mixed-precision training primitives (FusedAdam, FusedLayerNorm, etc.).",
            config_key="CUDA_HOME",
            required=True,
            context=EngineeringContext(
                decision="Apex links against CUDA for fused GPU kernels.",
                observation="NVIDIA Apex provides optimised training ops that "
                            "require CUDA compilation.",
                reasoning="Apex reduces memory usage and speeds up training "
                          "via custom CUDA kernels.",
                lineage="Apex — https://github.com/NVIDIA/apex",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="heretic",
    layer="Engines",
    interfaces=[],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU-accelerated abliteration (safety alignment removal).",
            config_key="CUDA_HOME",
            required=True,
            context=EngineeringContext(
                decision="Heretic uses CUDA for efficient model weight manipulation.",
                observation="Abliteration modifies transformer attention weights "
                            "to remove refusal directions — computationally "
                            "intensive, benefits greatly from GPU.",
                reasoning="Heretic processes large model weight matrices; "
                          "CUDA acceleration is essential for practical runtimes.",
                lineage="Heretic — https://github.com/p-e-w/heretic",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="unsloth",
    layer="Development Environment",
    interfaces=[],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU-accelerated LLM fine-tuning with reduced memory.",
            config_key="CUDA_VISIBLE_DEVICES",
            required=True,
            context=EngineeringContext(
                decision="Unsloth requires CUDA for custom Triton/CUDA kernels.",
                observation="Unsloth achieves 2x speed and 80% memory reduction "
                            "via hand-optimised CUDA kernels.",
                reasoning="Fine-tuning LLMs on CPU is impractical; CUDA is "
                          "mandatory for Unsloth's value proposition.",
                lineage="Unsloth — https://github.com/unslothai/unsloth",
            ),
        ),
    ],
))


# ──────────────────────────────────────────────────────────────────
# L4: Inference Engines
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="ollama",
    layer="Engines",
    interfaces=[
        ToolInterface(
            interface_id="openai_api",
            protocol="HTTP",
            api_format="OpenAI",
            port=11434,
            base_path="/v1",
            auth="None (local only)",
            description="OpenAI-compatible API: /v1/chat/completions, "
                        "/v1/models, /v1/embeddings.  Also exposes native "
                        "/api/chat, /api/generate, /api/embed endpoints.",
            context=EngineeringContext(
                decision="Expose Ollama's OpenAI-compatible API as the primary "
                         "wiring interface.",
                observation="Ollama's /v1/* endpoints mirror the OpenAI API "
                            "spec, enabling drop-in replacement for any tool "
                            "that uses the OpenAI SDK.",
                alternatives="Could use Ollama's native /api/* endpoints, but "
                             "that would require tool-specific adapters.",
                constraints="At least one model must be pulled before inference "
                            "requests can be served.",
                reasoning="The OpenAI-compatible API is the universal interface "
                          "for LLM consumers.  Maximises compatibility across "
                          "the entire stack.",
                verification="curl http://localhost:11434/v1/models",
                lineage="Ollama OpenAI compat — https://github.com/ollama/ollama/blob/main/docs/openai.md",
                assumptions="Ollama running on localhost:11434.",
            ),
        ),
        ToolInterface(
            interface_id="native_api",
            protocol="HTTP",
            api_format="Ollama Native",
            port=11434,
            base_path="/api",
            auth="None (local only)",
            description="Ollama-native API: /api/chat, /api/generate, "
                        "/api/embed, /api/pull, /api/push, /api/copy, "
                        "/api/delete, /api/tags.",
        ),
    ],
    connections=[],
    context=EngineeringContext(
        decision="Ollama is the primary LLM inference engine for the stack. "
                 "It has no upstream network dependencies (models are loaded "
                 "from local storage).",
        observation="Ollama is the most widely consumed tool in the stack — "
                    "over 15 tools connect to its OpenAI-compatible API.",
        reasoning="Ollama provides the simplest local LLM serving experience: "
                  "one binary, pull-and-run model management, and OpenAI API "
                  "compatibility.",
    ),
))

_reg(StackWiring(
    tool_id="llamacpp",
    layer="Engines",
    interfaces=[
        ToolInterface(
            interface_id="openai_api",
            protocol="HTTP",
            api_format="OpenAI",
            port=8080,
            base_path="/v1",
            auth="None",
            description="OpenAI-compatible server API: /v1/chat/completions, "
                        "/v1/models, /v1/completions.",
            context=EngineeringContext(
                decision="Expose llama.cpp's built-in OpenAI-compatible server.",
                observation="llama.cpp ships with an HTTP server that implements "
                            "the OpenAI API spec for chat completions.",
                alternatives="Could use llama.cpp as a library (no server), "
                             "but the HTTP API enables service-to-service use.",
                constraints="A GGUF model file must be loaded at startup.",
                reasoning="Exposing the OpenAI-compatible API lets LiteLLM and "
                          "other proxies route to llama.cpp transparently.",
                verification="curl http://localhost:8080/v1/models",
                lineage="llama.cpp server — https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md",
            ),
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="vllm",
    layer="Engines",
    interfaces=[
        ToolInterface(
            interface_id="openai_api",
            protocol="HTTP",
            api_format="OpenAI",
            port=8000,
            base_path="/v1",
            auth="None (or API key if configured)",
            description="vLLM OpenAI-compatible API: /v1/chat/completions, "
                        "/v1/models, /v1/completions, /v1/embeddings. "
                        "High-throughput inference with PagedAttention.",
            context=EngineeringContext(
                decision="Expose vLLM's OpenAI-compatible API as its primary interface.",
                observation="vLLM implements the full OpenAI API spec with "
                            "additional features (beam search, guided decoding).",
                constraints="Requires CUDA GPU and sufficient VRAM for the "
                            "target model.",
                reasoning="vLLM is the highest-throughput open-source LLM "
                          "server.  OpenAI API compatibility ensures all "
                          "upstream consumers can use it without changes.",
                verification="curl http://localhost:8000/v1/models",
                lineage="vLLM — https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU-accelerated inference with PagedAttention.",
            config_key="CUDA_VISIBLE_DEVICES",
            required=True,
            context=EngineeringContext(
                decision="vLLM requires CUDA for its custom CUDA kernels "
                         "(PagedAttention, custom attention backends).",
                observation="vLLM's performance advantage comes entirely from "
                            "GPU-optimised kernels.",
                reasoning="vLLM without CUDA would have no performance "
                          "advantage over llama.cpp on CPU.",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="airllm",
    layer="Engines",
    interfaces=[
        ToolInterface(
            interface_id="airllm_api",
            protocol="HTTP",
            api_format="REST",
            port=8001,
            auth="None",
            description="AirLLM REST API for memory-efficient 70B inference.",
        ),
    ],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU inference for 70B models on limited VRAM.",
            required=True,
        ),
    ],
))

_reg(StackWiring(
    tool_id="koboldcpp",
    layer="Engines",
    interfaces=[
        ToolInterface(
            interface_id="koboldcpp_api",
            protocol="HTTP",
            api_format="KoboldAI",
            port=5001,
            base_path="/api",
            auth="None",
            description="KoboldCPP API: /api/v1/generate with KoboldAI "
                        "format. Supports CUDA and Vulkan backends.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="llamafile",
    layer="Engines",
    interfaces=[
        ToolInterface(
            interface_id="llamafile_api",
            protocol="HTTP",
            api_format="OpenAI",
            port=None,
            base_path="/v1",
            auth="None",
            description="Llamafile embeds an LLM server in a single binary. "
                        "Exposes OpenAI-compatible API when run with --serve.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="locally_uncensored",
    layer="Engines",
    interfaces=[],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="native_api",
            purpose="Model management — pulls uncensored models via Ollama.",
            config_key="OLLAMA_HOST",
            required=True,
            context=EngineeringContext(
                decision="Locally-Uncensored is a model collection that uses "
                         "Ollama to manage and serve models.",
                observation="It provides model files and Modelfile recipes "
                            "that are loaded into Ollama.",
                reasoning="No point duplicating model serving — Ollama already "
                          "handles that.  Locally-Uncensored adds the model curation.",
                lineage="Locally-Uncensored — https://github.com/nicely-done/locally-uncensored",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="turbollm",
    layer="Engines",
    interfaces=[
        ToolInterface(
            interface_id="turbollm_api",
            protocol="HTTP",
            api_format="REST",
            port=8000,
            auth="None",
            description="TurboLLM REST API for fast LLM inference.",
        ),
    ],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU-accelerated inference.",
            required=True,
        ),
    ],
))


# ──────────────────────────────────────────────────────────────────
# L5: Distributed Runtime
# (vLLM is already registered above — it sits at L5 in the taxonomy
#  but is logically grouped with inference engines in the wiring.)
# ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────
# L6: AI Endpoints  (→ the restored "Routing" layer in the 11-layer taxonomy)
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="litellm",
    layer="Routing",
    interfaces=[
        ToolInterface(
            interface_id="openai_api",
            protocol="HTTP",
            api_format="OpenAI",
            port=4000,
            base_path="/v1",
            auth="API key (LITELLM_MASTER_KEY or per-model keys)",
            description="LiteLLM unified proxy API.  Exposes a single "
                        "OpenAI-compatible endpoint that routes to multiple "
                        "backends (Ollama, vLLM, Anthropic, Azure, etc.). "
                        "Supports /v1/chat/completions, /v1/models, "
                        "/v1/embeddings, and load balancing.",
            context=EngineeringContext(
                decision="LiteLLM as the unified LLM proxy for the stack.",
                observation="LiteLLM normalises 100+ LLM providers behind a "
                            "single OpenAI-compatible API with features like "
                            "fallback, load balancing, spend tracking.",
                alternatives="Build a custom proxy, or have each tool connect "
                             "directly to its preferred backend.",
                constraints="Must be configured with model routes in its "
                            "config.yaml before consumers can use it.",
                reasoning="A single proxy simplifies the stack — consumers "
                          "point to one URL instead of managing multiple "
                          "backend connections.",
                verification="curl http://localhost:4000/v1/models -H 'Authorization: Bearer <key>'",
                lineage="LiteLLM — https://docs.litellm.ai/docs/proxy",
                assumptions="LiteLLM config.yaml has at least one model_list entry.",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Route requests to Ollama-hosted models via OpenAI API.",
            config_key="model_list[].litellm_params.api_base",
            required=False,
            context=EngineeringContext(
                decision="Ollama is the default backend for local models.",
                observation="LiteLLM's 'ollama/' model prefix connects to "
                            "Ollama's OpenAI-compatible endpoint.",
                reasoning="Ollama is the most common local LLM server; "
                          "LiteLLM provides first-class support for it.",
            ),
        ),
        Connection(
            target_tool="vllm",
            interface_id="openai_api",
            purpose="Route requests to vLLM for high-throughput inference.",
            config_key="model_list[].litellm_params.api_base",
            required=False,
            context=EngineeringContext(
                decision="vLLM as an optional high-performance backend.",
                observation="LiteLLM can route to vLLM's OpenAI-compatible "
                            "endpoint for models that need PagedAttention.",
                reasoning="vLLM excels at batched serving — LiteLLM can "
                          "route appropriate models there.",
            ),
        ),
        Connection(
            target_tool="llamacpp",
            interface_id="openai_api",
            purpose="Route requests to llama.cpp for GGUF model inference.",
            config_key="model_list[].litellm_params.api_base",
            required=False,
            context=EngineeringContext(
                decision="llama.cpp as an optional backend for GGUF models.",
                observation="Some models are only available in GGUF format.",
                reasoning="LiteLLM can proxy to llama.cpp when Ollama is "
                          "not the preferred runner.",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="9router_proxy",
    layer="Routing",
    interfaces=[
        ToolInterface(
            interface_id="router_api",
            protocol="HTTP",
            api_format="REST",
            port=4001,
            auth="None",
            description="9Router proxy API for routing LLM requests to "
                        "multiple inference backends.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Route inference requests to Ollama.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="deep_eye",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="deep_eye_api",
            protocol="HTTP",
            api_format="REST",
            port=8100,
            auth="None",
            description="Deep Eye vision/analysis endpoint API.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for vision analysis tasks.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="luxtts",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="tts_api",
            protocol="HTTP",
            api_format="REST",
            port=8500,
            auth="None",
            description="LuxTTS text-to-speech synthesis API.",
        ),
    ],
    connections=[],
))


# ──────────────────────────────────────────────────────────────────
# L7: Data & Knowledge Pipelines
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="chromadb",
    layer="Knowledge Management",
    interfaces=[
        ToolInterface(
            interface_id="http_api",
            protocol="HTTP",
            api_format="REST",
            port=8000,
            base_path="/api/v1",
            auth="None (local only)",
            description="ChromaDB HTTP REST API for vector collection "
                        "management: create/list/get/delete collections, "
                        "add/query/delete vectors, get/update embeddings.",
            context=EngineeringContext(
                decision="Expose ChromaDB's HTTP API for service-to-service access.",
                observation="ChromaDB runs a separate HTTP server (chromadb "
                            "run --host 0.0.0.0 --port 8000) that exposes "
                            "its full API over REST.",
                alternatives="Python client library (in-process), but that "
                             "requires the consumer to be in the same process.",
                constraints="Collections must be created before vectors can be "
                            "inserted or queried.",
                reasoning="HTTP API allows tools like Open WebUI and OpenJarvis "
                          "to use ChromaDB as a remote vector store.",
                verification="curl http://localhost:8000/api/v1/heartbeat",
                lineage="ChromaDB — https://docs.trychroma.com/docs/api/rest",
                assumptions="ChromaDB server running on port 8000.",
            ),
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="qdrant",
    layer="Knowledge Management",
    interfaces=[
        ToolInterface(
            interface_id="http_api",
            protocol="HTTP",
            api_format="REST",
            port=6333,
            base_path="/collections",
            auth="API key (optional)",
            description="Qdrant HTTP REST API for vector search: "
                        "collection CRUD, point upsert/search/delete, "
                        "payload filtering.  Also available on gRPC port 6334.",
            context=EngineeringContext(
                decision="Expose Qdrant's HTTP API for vector search.",
                observation="Qdrant's REST API is the standard interface for "
                            "collection management and similarity search.",
                alternatives="gRPC API (port 6334) for lower latency.",
                constraints="Must create collections with proper vector dimensions.",
                reasoning="HTTP is more universally accessible than gRPC; "
                          "most tools have HTTP client support built in.",
                verification="curl http://localhost:6333/collections",
                lineage="Qdrant — https://qdrant.tech/documentation/",
            ),
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="lancedb",
    layer="Knowledge Management",
    interfaces=[
        ToolInterface(
            interface_id="http_api",
            protocol="HTTP",
            api_format="REST",
            port=8484,
            auth="None",
            description="LanceDB HTTP API for vector search and table management.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="elasticsearch",
    layer="Knowledge Management",
    interfaces=[
        ToolInterface(
            interface_id="http_api",
            protocol="HTTP",
            api_format="REST",
            port=9200,
            auth="Basic auth (elastic/password)",
            description="Elasticsearch REST API for full-text search, "
                        "indexing, and document retrieval.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="neo4j",
    layer="Knowledge Management",
    interfaces=[
        ToolInterface(
            interface_id="http_api",
            protocol="HTTP",
            api_format="REST",
            port=7474,
            auth="Username/password (neo4j/neo4j default)",
            description="Neo4j HTTP API for graph database queries "
                        "(Cypher over REST).  Bolt protocol on port 7687.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="meilisearch",
    layer="Knowledge Management",
    interfaces=[
        ToolInterface(
            interface_id="http_api",
            protocol="HTTP",
            api_format="REST",
            port=7700,
            auth="API key (master + search keys)",
            description="Meilisearch REST API for typo-tolerant full-text search.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="airweave",
    layer="Knowledge Management",
    interfaces=[
        ToolInterface(
            interface_id="airweave_api",
            protocol="HTTP",
            api_format="REST",
            port=8600,
            auth="None",
            description="Airweave API for data pipeline orchestration and "
                        "knowledge graph construction.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="parakeet",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="parakeet_api",
            protocol="HTTP",
            api_format="REST",
            port=8300,
            auth="None",
            description="Parakeet text-to-speech API.",
        ),
    ],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU-accelerated speech synthesis.",
            required=True,
        ),
    ],
))

_reg(StackWiring(
    tool_id="turbovec",
    layer="Knowledge Management",
    interfaces=[
        ToolInterface(
            interface_id="turbovec_api",
            protocol="HTTP",
            api_format="REST",
            port=8101,
            auth="None",
            description="TurboVec embedding generation API.",
        ),
    ],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU-accelerated embedding generation.",
            required=True,
        ),
    ],
))

_reg(StackWiring(
    tool_id="crawl4ai",
    layer="Knowledge Management",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="Crawl4AI is a CLI/library for web crawling. No network "
                 "service interface.",
        observation="Used programmatically as a Python library for "
                    "web content extraction.",
        reasoning="Not a long-running service — invoked on-demand.",
    ),
))

_reg(StackWiring(
    tool_id="docling",
    layer="Knowledge Management",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="Docling is a CLI/library for document parsing. No network "
                 "service interface.",
        reasoning="Used as a Python library for document conversion.",
    ),
))

_reg(StackWiring(
    tool_id="fabric",
    layer="Orchestrators",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="Fabric is a CLI tool for LLM-augmented text processing. "
                 "No network service interface.",
        reasoning="Invoked from the command line with pre-defined patterns.",
    ),
))

_reg(StackWiring(
    tool_id="graphrag",
    layer="Knowledge Management",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="GraphRAG is a library/pipeline for knowledge graph construction. "
                 "No network service interface.",
        reasoning="Run as a batch process or embedded in applications.",
    ),
))

_reg(StackWiring(
    tool_id="markitdown",
    layer="Knowledge Management",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="MarkItDown is a CLI/library for converting files to Markdown. "
                 "No network service interface.",
        reasoning="Used as a Python library or CLI command.",
    ),
))

_reg(StackWiring(
    tool_id="mirofish",
    layer="Knowledge Management",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="Mirofish is a passive tool. No network service interface.",
        reasoning="Not a long-running service.",
    ),
))

_reg(StackWiring(
    tool_id="opendataloader",
    layer="Knowledge Management",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="OpenDataloader is a CLI/library. No network service interface.",
        reasoning="Used as a Python library for data loading.",
    ),
))

_reg(StackWiring(
    tool_id="opendataloader_pdf",
    layer="Knowledge Management",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="OpenDataloader-PDF is a CLI/library. No network service interface.",
        reasoning="Used as a Python library for PDF data extraction.",
    ),
))

_reg(StackWiring(
    tool_id="understand_anything",
    layer="Knowledge Management",
    interfaces=[],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for document understanding and analysis.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="whisper",
    layer="Knowledge Management",
    interfaces=[],
    connections=[],
    context=EngineeringContext(
        decision="Whisper is a CLI/model for speech-to-text. No network "
                 "service interface.",
        reasoning="Used as a Python library or CLI command for transcription.",
    ),
))


# ──────────────────────────────────────────────────────────────────
# L8: Automation & Execution
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="n8n",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="n8n_api",
            protocol="HTTP",
            api_format="REST",
            port=5678,
            base_path="/api/v1",
            auth="API key or session cookie",
            description="n8n REST API for workflow management: list/run/stop "
                        "workflows, manage credentials, execute webhooks.",
            context=EngineeringContext(
                decision="n8n exposes a REST API for programmatic workflow control.",
                observation="n8n is a workflow automation platform that can "
                            "call out to LLMs, databases, and other services.",
                alternatives="Direct shell scripting, Apache Airflow.",
                reasoning="n8n provides a visual workflow builder and webhook "
                          "system that integrates with the rest of the stack.",
                verification="curl http://localhost:5678/api/v1/workflows",
                lineage="n8n — https://docs.n8n.io/api/",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="redis",
            interface_id="redis",
            purpose="Queue management and pub/sub for workflow orchestration.",
            config_key="N8N_REDIS_URL",
            required=False,
            context=EngineeringContext(
                decision="n8n can optionally use Redis for its queue mode.",
                observation="n8n's queue mode uses Redis (or RabbitMQ) for "
                            "distributing workflow execution across workers.",
                alternatives="n8n's built-in in-memory queue (default mode).",
                constraints="Redis must be configured in n8n's environment variables.",
                reasoning="Redis-backed queues enable horizontal scaling of "
                          "n8n workers.",
                lineage="n8n queue mode — https://docs.n8n.io/hosting/scaling/queue-mode/",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="nightshift",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="nightshift_api",
            protocol="HTTP",
            api_format="REST",
            port=8800,
            auth="None",
            description="Nightshift automation and scheduling API.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="hivemind",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="hivemind_api",
            protocol="HTTP",
            api_format="REST",
            port=8700,
            auth="None",
            description="HiveMind multi-agent coordination API.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for agent reasoning and decision making.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="hermes_agent",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="hermes_agent_api",
            protocol="HTTP",
            api_format="REST",
            port=17051,
            auth="None",
            description="Hermes Agent API for AI-powered task execution.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for agent task execution.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="openhands",
    layer="DevOps",
    interfaces=[
        ToolInterface(
            interface_id="openhands_api",
            protocol="HTTP",
            api_format="REST",
            port=3000,
            auth="None",
            description="OpenHands AI coding agent API.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for code generation and software engineering tasks.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

# Passive / CLI-only tools in L8 — no interfaces or network connections
for _tid in [
    "agent_reach", "agentic_os", "aider", "algory", "atlas_os",
    "claude_code", "eagle_eye", "headroom", "honcho",
    "loop_engineering", "mcp_drift_state_tracker", "nvidia_agent_skills",
    "ponytail", "promptops", "skillspector", "spec_kit", "synapscli",
    "wayland_ai",
]:
    _ollama_consumers = {
        "agentic_os", "aider", "atlas_os", "claude_code", "ponytail",
    }
    _cuda_consumers = {"nvidia_agent_skills"}
    _conns: list[Connection] = []
    _ctx = EngineeringContext(
        decision=f"{_tid} connects to Ollama for LLM inference.",
        observation=f"{_tid} is a CLI or library tool that calls an "
                    f"LLM backend for its core functionality.",
        reasoning="These tools embed LLM calls as part of their workflow.",
        lineage=f"Tool-specific — see {_tid} documentation.",
    )
    if _tid in _ollama_consumers:
        _conns.append(Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for AI-powered features.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_ctx,
        ))
    if _tid in _cuda_consumers:
        _conns.append(Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU acceleration for AI skill execution.",
            config_key="CUDA_VISIBLE_DEVICES",
            required=True,
        ))
    _reg(StackWiring(
        tool_id=_tid,
        layer="DevOps",
        interfaces=[],
        connections=_conns,
        context=EngineeringContext(
            decision=f"{_tid} is a passive/CLI tool. No network interfaces exposed.",
            observation=f"Used programmatically or from the command line.",
            reasoning="Not a long-running service — no interfaces to wire.",
        ),
    ))

# agno has a web interface but no deps in defaults
_reg(StackWiring(
    tool_id="agno",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="agno_web",
            protocol="HTTP",
            api_format="REST",
            port=None,
            auth="None",
            description="Agno AI agent framework web interface.",
        ),
    ],
    connections=[],
))


# ──────────────────────────────────────────────────────────────────
# L9: Observability
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="prometheus",
    layer="Observability",
    interfaces=[
        ToolInterface(
            interface_id="prometheus_api",
            protocol="HTTP",
            api_format="REST",
            port=9090,
            base_path="/api/v1",
            auth="None (local only)",
            description="Prometheus HTTP API for querying metrics: "
                        "/api/v1/query, /api/v1/query_range, /api/v1/series. "
                        "Also accepts remote writes via /api/v1/write.",
            context=EngineeringContext(
                decision="Prometheus as the central metrics store.",
                observation="Prometheus scrapes metrics from instrumented "
                            "services and stores them as time-series data.",
                alternatives="VictoriaMetrics, InfluxDB, Thanos.",
                constraints="Must be configured with scrape targets.",
                reasoning="Prometheus is the de-facto standard for metrics "
                          "collection in cloud-native stacks.",
                verification="curl http://localhost:9090/api/v1/query?query=up",
                lineage="Prometheus — https://prometheus.io/docs/",
            ),
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="grafana",
    layer="Observability",
    interfaces=[
        ToolInterface(
            interface_id="grafana_web",
            protocol="HTTP",
            api_format="REST",
            port=3000,
            base_path="/api",
            auth="API key or session cookie",
            description="Grafana dashboard and API: /api/dashboards, "
                        "/api/datasources, /api/alerts.  Also serves "
                        "the web UI for visualising metrics.",
            context=EngineeringContext(
                decision="Grafana as the primary dashboard and visualisation layer.",
                observation="Grafana connects to Prometheus (and other data "
                            "sources) to render dashboards.",
                alternatives="Grafana is the standard — no real alternative "
                             "with equivalent ecosystem.",
                constraints="Must have at least one data source configured.",
                reasoning="Grafana provides the visual layer on top of "
                          "Prometheus metrics.",
                verification="curl http://localhost:3000/api/health",
                lineage="Grafana — https://grafana.com/docs/",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="prometheus",
            interface_id="prometheus_api",
            purpose="Query Prometheus metrics for dashboard visualisation.",
            config_key="GF_DATASOURCES__0__URL",
            required=True,
            context=EngineeringContext(
                decision="Grafana's primary data source is Prometheus.",
                observation="Grafana natively supports Prometheus as a data "
                            "source with PromQL query editor.",
                alternatives="Could connect to Loki (logs) or Tempo (traces) "
                             "as additional data sources.",
                reasoning="Prometheus + Grafana is the standard observability "
                          "pairing in cloud-native stacks.",
                verification="Configure in Grafana: Configuration > Data Sources > Add > Prometheus",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="grafana_alloy",
    layer="Observability",
    interfaces=[
        ToolInterface(
            interface_id="otlp_grpc",
            protocol="gRPC",
            api_format="OTLP",
            port=12345,
            auth="None",
            description="Grafana Alloy OTLP gRPC endpoint for receiving "
                        "metrics, logs, and traces from instrumented services. "
                        "Forwards to Prometheus, Loki, and Tempo.",
            context=EngineeringContext(
                decision="Grafana Alloy as the OpenTelemetry collector.",
                observation="Alloy receives OTLP data and fans it out to "
                            "Grafana's backend services (Prometheus, Loki, Tempo).",
                alternatives="OTel Collector, Vector.",
                constraints="Alloy must be configured with export targets.",
                reasoning="Alloy is Grafana's recommended collector — tighter "
                          "integration with Grafana ecosystem.",
                verification="Alloy health check on its admin port.",
                lineage="Grafana Alloy — https://grafana.com/docs/alloy/",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="prometheus",
            interface_id="prometheus_api",
            purpose="Forward collected metrics to Prometheus via remote write.",
            config_key="prometheus.remote_write",
            required=True,
            context=EngineeringContext(
                decision="Alloy pushes metrics to Prometheus via remote write.",
                observation="Alloy's prometheus.remote_write component sends "
                            "metrics to Prometheus' /api/v1/write endpoint.",
                reasoning="This is the standard way to get Alloy-collected "
                          "metrics into Prometheus.",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="glances",
    layer="Observability",
    interfaces=[
        ToolInterface(
            interface_id="glances_web",
            protocol="HTTP",
            api_format="REST",
            port=61208,
            auth="None (or basic auth)",
            description="Glances system monitoring web UI and API.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="opik",
    layer="Observability",
    interfaces=[
        ToolInterface(
            interface_id="opik_api",
            protocol="HTTP",
            api_format="REST",
            port=3000,
            auth="API key",
            description="Opik LLM observability and tracing API.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="pulse_ai",
    layer="Observability",
    interfaces=[
        ToolInterface(
            interface_id="pulse_ai_api",
            protocol="HTTP",
            api_format="REST",
            port=8900,
            auth="None",
            description="Pulse AI monitoring and health check API.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="hermes_dashboard_page",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="dashboard_api",
            protocol="HTTP",
            api_format="REST",
            port=17050,
            auth="None",
            description="Hermes Dashboard API for monitoring Hermes agent activity.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Display LLM usage metrics and agent activity.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="latitude",
    layer="Observability",
    interfaces=[
        ToolInterface(
            interface_id="latitude_api",
            protocol="HTTP",
            api_format="REST",
            port=9300,
            auth="None",
            description="Latitude LLM evaluation and monitoring API.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Send evaluation prompts through Ollama.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))


# ──────────────────────────────────────────────────────────────────
# L10: Intelligent Routing  (folded into "Orchestrators" in the 11-layer taxonomy)
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="odysseus",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="odysseus_api",
            protocol="HTTP",
            api_format="REST",
            port=7000,
            auth="None",
            description="Odysseus intelligent routing and reasoning API.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for routing decisions and reasoning.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="glassmind",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="glassmind_api",
            protocol="HTTP",
            api_format="REST",
            port=9400,
            auth="None",
            description="GlassMind reasoning and cognitive architecture API.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for cognitive reasoning.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="mnemo_cortex",
    layer="Knowledge Management",
    interfaces=[
        ToolInterface(
            interface_id="mnemo_cortex_api",
            protocol="HTTP",
            api_format="REST",
            port=7200,
            auth="None",
            description="Mnemo Cortex memory and reasoning API.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for memory-augmented reasoning.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="openbrain",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="openbrain_api",
            protocol="HTTP",
            api_format="REST",
            port=7100,
            auth="None",
            description="OpenBrain AI reasoning and planning API.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for reasoning and planning.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="everos_memory",
    layer="Knowledge Management",
    interfaces=[
        ToolInterface(
            interface_id="everos_memory_api",
            protocol="HTTP",
            api_format="REST",
            port=9200,
            auth="None",
            description="EverOS memory and context management API.",
        ),
    ],
    connections=[],
))

# Passive L10 tools
for _tid in ["autogen", "crewai", "openai_swarm"]:
    _reg(StackWiring(
        tool_id=_tid,
        layer="Orchestrators",
        interfaces=[],
        connections=[],
        context=EngineeringContext(
            decision=f"{_tid} is a Python library/framework. No network service interface.",
            observation="These are multi-agent frameworks consumed as Python packages.",
            reasoning="Not long-running services — used as libraries in applications.",
        ),
    ))


# ──────────────────────────────────────────────────────────────────
# L11: User Interfaces
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="openwebui",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="openwebui_web",
            protocol="HTTP",
            api_format="REST",
            port=8080,
            base_path="/api",
            auth="Session cookie or API key",
            description="Open WebUI: full-featured web chat interface with "
                        "RAG, document upload, model management, and user auth.",
            context=EngineeringContext(
                decision="Open WebUI as the primary chat/LLM web interface.",
                observation="Open WebUI provides the best out-of-the-box "
                            "experience for interacting with local LLMs — "
                            "chat, RAG, document upload, model switching.",
                alternatives="LibreChat, AnythingLLM, Dify, Flowise.",
                constraints="Requires an LLM backend (Ollama or OpenAI-compatible).",
                reasoning="Open WebUI is the most polished open-source chat UI "
                          "for local LLMs with the deepest feature set.",
                verification="Open http://localhost:8080 in a browser.",
                lineage="Open WebUI — https://docs.openwebui.com/",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Primary LLM backend for chat inference.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=EngineeringContext(
                decision="Ollama is the default and most tightly integrated LLM backend.",
                observation="Open WebUI auto-discovers Ollama and lists its "
                            "models.  Can also connect to any OpenAI-compatible endpoint.",
                alternatives="LiteLLM, vLLM, or any OpenAI-compatible API.",
                reasoning="Ollama provides the simplest setup for Open WebUI — "
                          "just point at localhost:11434.",
                verification="Settings > Connections in Open WebUI UI.",
            ),
        ),
        Connection(
            target_tool="litellm",
            interface_id="openai_api",
            purpose="Alternative LLM backend via LiteLLM proxy for multi-model routing.",
            config_key="OPENAI_API_BASE_URL",
            required=False,
            context=_LITELLM_CONSUMER_CTX,
        ),
        Connection(
            target_tool="chromadb",
            interface_id="http_api",
            purpose="RAG vector storage for document embeddings and retrieval.",
            config_key="CHROMADB_URL",
            required=False,
            context=EngineeringContext(
                decision="Use ChromaDB as the vector store for RAG.",
                observation="Open WebUI uses ChromaDB (built-in) for storing "
                            "document embeddings and performing similarity search.",
                alternatives="Open WebUI can also use its built-in ChromaDB "
                             "instance — external ChromaDB is optional.",
                reasoning="External ChromaDB allows sharing embeddings across "
                          "tools (e.g. with OpenJarvis).",
                verification="Settings > Documents > Vector Database in Open WebUI.",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="dify",
    layer="Routing",
    interfaces=[
        ToolInterface(
            interface_id="dify_web",
            protocol="HTTP",
            api_format="REST",
            port=80,
            base_path="/v1",
            auth="API key (per-app)",
            description="Dify: visual LLM app builder with workflow editor, "
                        "RAG pipeline, agent builder, and API exposure.",
            context=EngineeringContext(
                decision="Dify as the visual workflow/agent builder interface.",
                observation="Dify provides a no-code/low-code platform for "
                            "building LLM-powered applications with workflows.",
                alternatives="Flowise, Langflow.",
                constraints="Requires PostgreSQL and Redis.",
                reasoning="Dify has the most complete workflow builder for "
                          "LLM apps — beats Flowise and Langflow on feature depth.",
                verification="Open http://localhost in a browser.",
                lineage="Dify — https://docs.dify.ai/",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="postgresql",
            interface_id="postgresql",
            purpose="Persistent storage for apps, workflows, conversations, and user data.",
            config_key="DB_HOST / DB_PORT / DB_USERNAME / DB_PASSWORD / DB_DATABASE",
            required=True,
            context=EngineeringContext(
                decision="PostgreSQL as Dify's primary database.",
                observation="Dify requires PostgreSQL for all persistent data. "
                            "It manages its own schema via Alembic migrations.",
                alternatives="Dify does not support SQLite or MySQL in production.",
                constraints="Database and user must be created before Dify starts.",
                reasoning="PostgreSQL is Dify's only supported production database.",
                verification="Dify startup logs show successful DB connection.",
            ),
        ),
        Connection(
            target_tool="redis",
            interface_id="redis",
            purpose="Caching, session management, and Celery broker for async tasks.",
            config_key="REDIS_HOST / REDIS_PORT / REDIS_DB",
            required=True,
            context=EngineeringContext(
                decision="Redis as Dify's cache and task queue broker.",
                observation="Dify uses Redis for its Celery task queue, "
                            "rate limiting, and caching.",
                alternatives="Dify does not support alternative brokers.",
                constraints="Redis must be running before Dify starts.",
                reasoning="Redis is the standard message broker for Python "
                          "async task queues (Celery).",
                verification="Dify startup logs show successful Redis connection.",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="flowise",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="flowise_web",
            protocol="HTTP",
            api_format="REST",
            port=3000,
            base_path="/api/v1",
            auth="API key (optional)",
            description="Flowise: drag-and-drop LLM flow builder with "
                        "chatbot API, document loaders, and vector stores.",
            context=EngineeringContext(
                decision="Flowise as a visual LLM flow builder.",
                observation="Flowise provides a node-based UI for building "
                            "LLM pipelines (LangChain-based).",
                alternatives="Dify, Langflow.",
                reasoning="Flowise is simpler than Dify for basic LLM chains.",
                lineage="Flowise — https://docs.flowiseai.com/",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="litellm",
            interface_id="openai_api",
            purpose="LLM inference via LiteLLM proxy for multi-model support.",
            config_key="OPENAI_API_BASE",
            required=False,
            context=_LITELLM_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="openjarvis",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="openjarvis_web",
            protocol="HTTP",
            api_format="REST",
            port=17070,
            base_path="/api",
            auth="None",
            description="OpenJarvis: AI assistant web interface with "
                        "knowledge base and tool integration.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for assistant responses.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
        Connection(
            target_tool="chromadb",
            interface_id="http_api",
            purpose="Vector storage for knowledge base RAG retrieval.",
            config_key="CHROMADB_HOST",
            required=False,
            context=_VECTOR_STORE_CONSUMER_CTX,
        ),
        Connection(
            target_tool="qdrant",
            interface_id="http_api",
            purpose="Alternative vector storage for knowledge base.",
            config_key="QDRANT_HOST",
            required=False,
            context=EngineeringContext(
                decision="Qdrant as an alternative to ChromaDB for OpenJarvis.",
                observation="Qdrant offers more advanced filtering and "
                            "better performance at scale.",
                alternatives="ChromaDB (simpler, embedded option).",
                reasoning="Giving OpenJarvis the option to use either vector store.",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="hermes",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="hermes_web",
            protocol="HTTP",
            api_format="REST",
            port=17050,
            base_path="/api",
            auth="None",
            description="Hermes: AI assistant and agent web interface.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for Hermes assistant and agent features.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="librechat",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="librechat_web",
            protocol="HTTP",
            api_format="REST",
            port=3080,
            base_path="/api",
            auth="Session cookie",
            description="LibreChat: open-source ChatGPT-clone web interface "
                        "with multi-model support.",
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Ollama as an LLM endpoint for chat completions.",
            config_key="OPENAI_REVERSE_PROXY or custom endpoint config",
            required=False,
            context=EngineeringContext(
                decision="Connect LibreChat to Ollama via OpenAI-compatible endpoint.",
                observation="LibreChat supports custom OpenAI-compatible endpoints.",
                alternatives="Direct OpenAI, Anthropic, or Google API.",
                reasoning="Ollama provides local LLM access for LibreChat.",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="anythingllm",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="anythingllm_web",
            protocol="HTTP",
            api_format="REST",
            port=3001,
            auth="None",
            description="AnythingLLM: RAG-first chat interface with built-in "
                        "document management and vector storage.",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="langflow",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="langflow_web",
            protocol="HTTP",
            api_format="REST",
            port=7860,
            base_path="/api/v1",
            auth="API key",
            description="Langflow: visual LLM flow builder (LangChain-based).",
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="forge",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="forge_web",
            protocol="HTTP",
            api_format="REST",
            port=7860,
            auth="None",
            description="Forge: AI model/image generation web interface.",
        ),
    ],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU-accelerated model inference and image generation.",
            config_key="CUDA_VISIBLE_DEVICES",
            required=True,
        ),
    ],
))

_reg(StackWiring(
    tool_id="invokeai",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="invokeai_web",
            protocol="HTTP",
            api_format="REST",
            port=9090,
            auth="None",
            description="InvokeAI: professional AI image generation interface.",
        ),
    ],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU-accelerated Stable Diffusion image generation.",
            config_key="CUDA_VISIBLE_DEVICES",
            required=True,
        ),
    ],
))

_reg(StackWiring(
    tool_id="dashy",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="dashy_web",
            protocol="HTTP",
            api_format="REST",
            port=3000,
            auth="None",
            description="Dashy: customisable dashboard/hompage for accessing "
                        "all stack services.",
        ),
    ],
    connections=[],
))

# Passive L11 tools
for _tid in ["hermes_desktop", "local_llm_launcher"]:
    _conns = []
    if _tid in ("hermes_desktop", "local_llm_launcher"):
        _conns.append(Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for desktop launcher features.",
            config_key="OLLAMA_BASE_URL",
            required=True,
            context=_OLLAMA_CONSUMER_CTX,
        ))
    _reg(StackWiring(
        tool_id=_tid,
        layer="User Interfaces",
        interfaces=[],
        connections=_conns,
        context=EngineeringContext(
            decision=f"{_tid} is a desktop/CLI tool. No web interface.",
            reasoning="Not a long-running HTTP service.",
        ),
    ))


# ──────────────────────────────────────────────────────────────────
# L12: DevOps
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="opensandbox",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="opensandbox_web",
            protocol="HTTP",
            api_format="REST",
            port=9100,
            auth="None",
            description="OpenSandbox: sandboxed development environment API.",
        ),
    ],
    connections=[],
))

# Passive L12 tools — CLI tools and IaC frameworks with no network interfaces
for _tid in [
    "ansible", "aws_cdk", "bicep", "container_tool", "crossplane",
    "homelab", "opentofu", "pulumi", "puppet", "sst",
    "stack_exporter", "terraform", "terragrunt",
]:
    _conns: list[Connection] = []
    if _tid == "crossplane":
        _conns.append(Connection(
            target_tool="kubectl",  # kubectl is not in registry, note as system dep
            interface_id="kubectl",
            purpose="Kubernetes API access for infrastructure provisioning.",
            config_key="KUBECONFIG",
            required=True,
            context=EngineeringContext(
                decision="Crossplane requires Kubernetes API access.",
                observation="Crossplane runs as a Kubernetes controller.",
                reasoning="Crossplane manages cloud resources through Kubernetes.",
            ),
        ))
    if _tid == "terragrunt":
        _conns.append(Connection(
            target_tool="terraform",
            interface_id="terraform_cli",
            purpose="Terragrunt wraps Terraform for configuration management.",
            config_key="TERRAGRUNT_TFPATH",
            required=True,
            context=EngineeringContext(
                decision="Terragrunt depends on Terraform as its execution backend.",
                observation="Terragrunt is a thin wrapper that invokes Terraform.",
                reasoning="Terragrunt adds DRY configs, remote state management, "
                          "and dependency orchestration on top of Terraform.",
            ),
        ))
    if _tid == "homelab":
        _conns.append(Connection(
            target_tool="ansible",
            interface_id="ansible_cli",
            purpose="Homelab uses Ansible playbooks for server provisioning.",
            config_key="ANSIBLE_CONFIG",
            required=True,
        ))
    _reg(StackWiring(
        tool_id=_tid,
        layer="DevOps",
        interfaces=[],
        connections=_conns,
        context=EngineeringContext(
            decision=f"{_tid} is a CLI/IaC tool. No network service interface.",
            reasoning="These are command-line tools invoked on-demand.",
        ),
    ))


# ──────────────────────────────────────────────────────────────────
# L13: Knowledge Management
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="paperlessngx",
    layer="Knowledge Management",
    interfaces=[
        ToolInterface(
            interface_id="paperlessngx_web",
            protocol="HTTP",
            api_format="REST",
            port=8000,
            base_path="/api",
            auth="Token auth",
            description="Paperless-ngx: document management system API for "
                        "OCR, tagging, and full-text search of scanned documents.",
            context=EngineeringContext(
                decision="Paperless-ngx as the document management system.",
                observation="Paperless-ngx stores, OCRs, and indexes scanned "
                            "documents for search and retrieval.",
                constraints="Requires PostgreSQL and Redis.",
                reasoning="Paperless-ngx is the best open-source document "
                          "management system with OCR capabilities.",
                verification="Open http://localhost:8000 in a browser.",
                lineage="Paperless-ngx — https://docs.paperless-ngx.com/",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="postgresql",
            interface_id="postgresql",
            purpose="Persistent storage for documents, metadata, and search index.",
            config_key="PAPERLESS_DBHOST / PAPERLESS_DBPORT",
            required=True,
            context=EngineeringContext(
                decision="PostgreSQL for Paperless-ngx document metadata and search index.",
                observation="Paperless-ngx requires PostgreSQL for its metadata "
                            "database and full-text search.",
                constraints="Database must be created before Paperless-ngx starts.",
                reasoning="PostgreSQL provides the full-text search and "
                          "JSONB storage that Paperless-ngx needs.",
            ),
        ),
        Connection(
            target_tool="redis",
            interface_id="redis",
            purpose="Task queue broker for async document processing (OCR, indexing).",
            config_key="PAPERLESS_REDIS",
            required=True,
            context=EngineeringContext(
                decision="Redis for Paperless-ngx task queue (Celery).",
                observation="Paperless-ngx uses Celery + Redis for background "
                            "tasks (OCR, file consumption, indexing).",
                reasoning="Document processing is CPU-intensive — must be "
                          "offloaded to background workers via Redis queue.",
            ),
        ),
    ],
))

# Passive L13 tools — desktop apps and CLI tools
for _tid in [
    "calibre", "career_ops", "joplin", "kanban", "logseq",
    "mnemosyne", "obsidian", "zotero", "pm_skills",
]:
    _reg(StackWiring(
        tool_id=_tid,
        layer="Knowledge Management",
        interfaces=[],
        connections=[],
        context=EngineeringContext(
            decision=f"{_tid} is a desktop/CLI tool. No network service interface to wire.",
            reasoning="These are local applications — they don't expose "
                      "network APIs consumed by other stack tools.",
        ),
    ))


# ──────────────────────────────────────────────────────────────────
# L5 additions: terminal coding agents (registry expansion pass)
# (coding agents now live in DevOps L10; meshllm/picode in Routing L5)
# opencode / gemini_cli / qwen_code / goose / codex — all multi-provider
# CLI agents that consume an OpenAI-compatible endpoint.  Wired to both
# Ollama (direct) and LiteLLM (proxied) so staging either backend
# prevents orphan-flagging in the Pipeline Ticker.
# ──────────────────────────────────────────────────────────────────

_CODING_AGENT_CTX = EngineeringContext(
    decision="Terminal coding agents consume an OpenAI-compatible "
             "chat endpoint for LLM inference.",
    observation="Every modern coding agent (opencode, Gemini CLI, "
                "Qwen Code, goose, Codex) speaks the OpenAI wire "
                "format for at least one provider slot.",
    alternatives="Native provider SDKs (Anthropic, Google) or a "
                 "custom proxy.",
    constraints="The endpoint must be reachable and expose "
                "/v1/chat/completions.",
    reasoning="OpenAI-compat is the de-facto agent ↔ LLM contract; "
              "pointing the agents at localhost keeps inference "
              "local per AI-LSC policy.",
    verification="Set the agent's base-URL env var to "
                 "http://127.0.0.1:11434/v1 and list models.",
    lineage="Mirrors the OpenAI API spec; adopted by Ollama, vLLM, "
            "SGLang, LiteLLM.",
    assumptions="At least one model is served by the target backend.",
)

_reg(StackWiring(
    tool_id="opencode",
    layer="DevOps",
    interfaces=[],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Local LLM inference for terminal coding sessions.",
            config_key="OPENAI_BASE_URL (ollama provider, opencode.json)",
            required=False,
            context=_CODING_AGENT_CTX,
        ),
        Connection(
            target_tool="litellm",
            interface_id="openai_api",
            purpose="Multi-model routing via LiteLLM proxy.",
            config_key="OPENAI_BASE_URL",
            required=False,
            context=_LITELLM_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="gemini_cli",
    layer="DevOps",
    interfaces=[],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Local LLM inference via the openai-compat provider.",
            config_key="OPENAI_BASE_URL",
            required=False,
            context=_CODING_AGENT_CTX,
        ),
        Connection(
            target_tool="litellm",
            interface_id="openai_api",
            purpose="Multi-model routing via LiteLLM proxy.",
            config_key="OPENAI_BASE_URL",
            required=False,
            context=_LITELLM_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="qwen_code",
    layer="DevOps",
    interfaces=[],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Local Qwen model inference via openai-compat provider.",
            config_key="OPENAI_BASE_URL",
            required=False,
            context=_CODING_AGENT_CTX,
        ),
        Connection(
            target_tool="litellm",
            interface_id="openai_api",
            purpose="Multi-model routing via LiteLLM proxy.",
            config_key="OPENAI_BASE_URL",
            required=False,
            context=_LITELLM_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="goose",
    layer="DevOps",
    interfaces=[],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Local LLM backend for goose sessions and MCP extensions.",
            config_key="GOOSE_PROVIDER / OPENAI_BASE_URL",
            required=False,
            context=_CODING_AGENT_CTX,
        ),
        Connection(
            target_tool="litellm",
            interface_id="openai_api",
            purpose="Multi-model routing via LiteLLM proxy.",
            config_key="OPENAI_BASE_URL",
            required=False,
            context=_LITELLM_CONSUMER_CTX,
        ),
    ],
))

# codex existed in the registry since v3.1 but had no STACK_WIRINGS
# entry, so it was flagged as an orphan by the Pipeline Ticker whenever
# it was staged.  This wiring closes that gap.
_reg(StackWiring(
    tool_id="codex",
    layer="DevOps",
    interfaces=[],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Local LLM inference for terminal coding sessions.",
            config_key="OPENAI_BASE_URL",
            required=False,
            context=_CODING_AGENT_CTX,
        ),
        Connection(
            target_tool="litellm",
            interface_id="openai_api",
            purpose="Multi-model routing via LiteLLM proxy.",
            config_key="OPENAI_BASE_URL",
            required=False,
            context=_LITELLM_CONSUMER_CTX,
        ),
    ],
))

_reg(StackWiring(
    tool_id="letta",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="http_api",
            protocol="HTTP",
            api_format="REST",
            port=8283,
            auth="Optional password (LETTA_SERVER_PASSWORD)",
            description="Letta agent server REST API — create/state/"
                        "message agents with persistent memory.",
            context=EngineeringContext(
                decision="Expose the Letta server REST API as its "
                         "primary interface.",
                observation="Letta (formerly MemGPT) manages stateful "
                            "agents whose memory/context survives across "
                            "sessions; the REST API is the management "
                            "surface.",
                alternatives="Python SDK in-process, or Letta Cloud "
                             "(SaaS — excluded by policy).",
                constraints="Requires a database — SQLite by default, "
                            "PostgreSQL recommended for persistence.",
                reasoning="A local agent-memory server complements "
                          "stateless coding agents in the stack.",
                verification="curl http://localhost:8283/v1/agents",
                lineage="Letta — https://docs.letta.com/",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for agent reasoning and memory operations.",
            config_key="LETTA_INFERENCE_BASE_URL / model config",
            required=False,
            context=_OLLAMA_CONSUMER_CTX,
        ),
        Connection(
            target_tool="postgresql",
            interface_id="postgresql",
            purpose="Persistent agent/state storage (SQLite fallback).",
            config_key="LETTA_PG_URI",
            required=False,
            context=EngineeringContext(
                decision="PostgreSQL as the optional durable backend for "
                         "Letta's state store.",
                observation="Letta defaults to SQLite; PostgreSQL is "
                            "recommended for multi-user / long-lived "
                            "deployments.",
                alternatives="Built-in SQLite (zero-config).",
                reasoning="Sharing one PostgreSQL instance with other "
                          "stack tools keeps state management uniform.",
                verification="letta server with LETTA_PG_URI set; "
                             "inspect created tables.",
                lineage="Letta — https://docs.letta.com/",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="sglang",
    layer="Engines",
    interfaces=[
        ToolInterface(
            interface_id="openai_api",
            protocol="HTTP",
            api_format="OpenAI",
            port=30000,
            base_path="/v1",
            auth="None (or API key if configured)",
            description="SGLang OpenAI-compatible API: /v1/chat/completions, "
                        "/v1/models, /v1/embeddings.  High-throughput serving "
                        "with RadixAttention prefix caching.",
            context=EngineeringContext(
                decision="Expose SGLang's OpenAI-compatible API as its "
                         "primary interface.",
                observation="SGLang rivals vLLM on throughput for "
                            "many-workload serving, and prefix caching "
                            "benefits agentic loops that resend context.",
                alternatives="vLLM (port 8000), Ollama, llama.cpp server.",
                constraints="Requires a CUDA GPU with sufficient VRAM for "
                            "the target model.",
                reasoning="OpenAI API compatibility lets every consumer in "
                          "the stack use SGLang without code changes.",
                verification="curl http://localhost:30000/v1/models",
                lineage="SGLang — https://docs.sglang.ai/",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU-accelerated inference kernels.",
            config_key="CUDA_VISIBLE_DEVICES",
            required=True,
            context=EngineeringContext(
                decision="SGLang requires CUDA for its serving kernels.",
                observation="SGLang's throughput comes from custom CUDA "
                            "kernels and RadixAttention.",
                reasoning="SGLang without a GPU has no advantage over "
                          "llama.cpp on CPU.",
                verification="nvidia-smi confirms driver and GPU availability.",
                lineage="SGLang — https://docs.sglang.ai/",
            ),
        ),
    ],
))

# ──────────────────────────────────────────────────────────────────
# L8 / L10 / L3 additions: jan, mem0, tinygrad
# ──────────────────────────────────────────────────────────────────

_reg(StackWiring(
    tool_id="jan",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="openai_api",
            protocol="HTTP",
            api_format="OpenAI",
            port=1337,
            base_path="/v1",
            auth="None (local only)",
            description="Jan's built-in OpenAI-compatible local API server "
                        "powered by its bundled llama.cpp engine — a "
                        "drop-in replacement for cloud APIs.",
            context=EngineeringContext(
                decision="Expose Jan's local API server as its wiring "
                         "interface.",
                observation="Jan is a self-contained desktop app: engine, "
                            "model manager, and API server in one; the API "
                            "server listens on 127.0.0.1:1337.",
                alternatives="Ollama as the engine with a separate chat UI.",
                constraints="The API server toggle must be enabled in Jan's "
                            "settings; Electron desktop UI is not "
                            "web-embeddable.",
                reasoning="A GUI chat app that also serves an "
                          "OpenAI-compatible endpoint doubles as an "
                          "inference provider for other stack tools.",
                verification="curl http://127.0.0.1:1337/v1/models",
                lineage="Jan — https://jan.ai/docs/desktop/api-server",
                assumptions="API server enabled (default on recent builds).",
            ),
        ),
    ],
    connections=[],
))

_reg(StackWiring(
    tool_id="mem0",
    layer="Knowledge Management",
    interfaces=[],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="LLM inference for memory extraction/summarisation "
                    "and embeddings for memory vectors.",
            config_key="OPENAI_BASE_URL / embedding model config",
            required=False,
            context=_OLLAMA_CONSUMER_CTX,
        ),
        Connection(
            target_tool="qdrant",
            interface_id="http_api",
            purpose="Vector storage for long-term memories.",
            config_key="QDRANT_HOST",
            required=False,
            context=EngineeringContext(
                decision="Qdrant as an optional external vector backend "
                         "for stored memories.",
                observation="Mem0 ships with an embedded vector store by "
                            "default and supports pluggable backends "
                            "(Qdrant, Chroma, pgvector).",
                alternatives="Mem0's built-in store, or ChromaDB.",
                reasoning="Sharing one Qdrant instance across knowledge "
                          "tools keeps embeddings co-located.",
                verification="Configure vector_store.provider=qdrant in "
                             "mem0 config; run a memory add + search.",
                lineage="Mem0 — https://docs.mem0.ai/",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="tinygrad",
    layer="GPU Runtimes",
    interfaces=[],
    connections=[
        Connection(
            target_tool="cuda",
            interface_id="cuda_driver",
            purpose="GPU-accelerated tensor ops on NVIDIA backends.",
            config_key="CUDA_VISIBLE_DEVICES",
            required=False,
            context=EngineeringContext(
                decision="CUDA is optional — tinygrad also runs on CPU and "
                         "AMD backends.",
                observation="tinygrad's lazy execution compiles kernels per "
                            "backend at runtime; the NVIDIA backend needs "
                            "the CUDA driver.",
                alternatives="CuPy for NumPy-compat GPU arrays; PyTorch for "
                             "a full training stack.",
                reasoning="Wiring CUDA (optionally) surfaces tinygrad in "
                          "the ticker when a GPU stack is staged, without "
                          "forcing it on CPU-only hosts.",
                verification="python3 -c \"from tinygrad import Tensor; "
                             "print(Tensor([1,2,3]).sum().item())\"",
                lineage="tinygrad — https://github.com/tinygrad/tinygrad",
            ),
        ),
    ],
))


# ══════════════════════════════════════════════════════════════════
# Topology query helpers
# ══════════════════════════════════════════════════════════════════

def get_providers(tool_id: str) -> list[StackWiring]:
    """Return all StackWirings that have an interface consumed by *tool_id*.

    In other words: which tools does *tool_id* connect TO?
    """
    wiring = STACK_WIRINGS.get(tool_id)
    if wiring is None:
        return []
    provider_ids = {c.target_tool for c in wiring.connections}
    return [STACK_WIRINGS[pid] for pid in provider_ids if pid in STACK_WIRINGS]


def get_consumers(tool_id: str) -> list[StackWiring]:
    """Return all StackWirings that consume an interface exposed by *tool_id*.

    In other words: which tools connect TO *tool_id*?
    """
    # M-24: removed dead `exposed` set.  The function only needs to walk
    # every other wiring's `connections` list and check whether any
    # connection targets *tool_id*.  Interface-level matching can be
    # added later if needed (see TODO).
    wiring = STACK_WIRINGS.get(tool_id)
    if wiring is None:
        return []

    consumers = []
    for other in STACK_WIRINGS.values():
        if other.tool_id == tool_id:
            continue
        for conn in other.connections:
            if conn.target_tool == tool_id:
                consumers.append(other)
                break
    return consumers


def get_topology() -> dict[str, dict[str, Any]]:
    """Return the full wiring graph as a nested dict.

    Format::

        {
            "<tool_id>": {
                "layer": "...",
                "exposes": ["<interface_id>", ...],
                "consumes": [
                    {"target": "<tool_id>", "interface": "<interface_id>"},
                    ...
                ],
            },
            ...
        }
    """
    result: dict[str, dict[str, Any]] = {}
    for tid, w in STACK_WIRINGS.items():
        result[tid] = {
            "layer": w.layer,
            "exposes": [i.interface_id for i in w.interfaces],
            "consumes": [
                {"target": c.target_tool, "interface": c.interface_id}
                for c in w.connections
            ],
        }
    return result


def validate_wiring() -> list[str]:
    """Validate the entire wiring graph for consistency.

    Checks:
    1. Every Connection.target_tool exists in STACK_WIRINGS.
    2. Every Connection.interface_id matches an interface on the target.
    3. CUDA virtual interface is properly used by passive tools.

    Returns a list of validation error strings (empty = valid).
    """
    errors: list[str] = []
    for tid, w in STACK_WIRINGS.items():
        for conn in w.connections:
            # Check target exists (allow known system-level dependencies
            # that are not in the tool registry — kubectl, etc.)
            _system_deps = {"kubectl"}
            if conn.target_tool not in STACK_WIRINGS:
                if conn.target_tool not in _system_deps:
                    errors.append(
                        f"[{tid}] Connection to unknown tool '{conn.target_tool}' "
                        f"via interface '{conn.interface_id}'"
                    )
                continue
            # Check interface exists on target (skip virtual/native interfaces)
            target = STACK_WIRINGS[conn.target_tool]
            target_iface_ids = {i.interface_id for i in target.interfaces}
            # Virtual/system interfaces whose targets aren't in STACK_WIRINGS
            _virtual_interfaces = {
                "cuda_driver", "terraform_cli", "kubectl", "ansible_cli",
            }
            if (conn.interface_id not in target_iface_ids
                    and conn.interface_id not in _virtual_interfaces):
                errors.append(
                    f"[{tid}] Interface '{conn.interface_id}' not found on "
                    f"target '{conn.target_tool}' "
                    f"(available: {sorted(target_iface_ids) or 'none'})"
                )
    return errors

# ──────────────────────────────────────────────────────────────────
# Graphify — knowledge graph builder + MCP server (rewired from passive)
# Removed from the L8 passive/CLI list above and given a proper wiring
# since graphify is both a CLI tool and an MCP stdio server.
# ──────────────────────────────────────────────────────────────────
_reg(StackWiring(
    tool_id="graphify",
    layer="Orchestrators",
    interfaces=[
        ToolInterface(
            interface_id="graphify_mcp",
            protocol="stdio",
            api_format="MCP",
            port=None,
            base_path="",
            auth="None (local stdio)",
            description="Graphify MCP stdio server. Start with "
                        "`graphify --mcp`. Other MCP-aware agents "
                        "(Claude Code, opencode with MCP support, "
                        "etc.) can query the knowledge graph via the "
                        "standard MCP protocol. Exposes tools for "
                        "graph query, path finding, and concept "
                        "explanation.",
            context=EngineeringContext(
                decision="Expose graphify as an MCP server so other "
                         "agents can query its knowledge graph.",
                observation="Graphify's --mcp mode runs a stdio MCP "
                            "server. Any MCP-aware agent can call "
                            "graphify's query/path/explain tools to "
                            "navigate the codebase graph without "
                            "re-reading source files.",
                alternatives="CLI-only mode (graphify query '...') "
                             "or direct graph.json consumption.",
                constraints="Graph must be built first via "
                            "`graphify .` before the MCP server can "
                            "answer queries.",
                reasoning="MCP is the standard agent-to-tool protocol. "
                          "Exposing graphify via MCP lets every coding "
                          "agent in the stack benefit from the "
                          "knowledge graph without each one needing "
                          "a custom graphify integration.",
                verification="Start `graphify --mcp` and send an MCP "
                             "initialize request on stdin.",
                lineage="Graphify — https://github.com/Graphify-Labs/graphify",
                assumptions="graphify installed (uv tool graphifyy) and "
                            "a graph has been built in the working "
                            "directory.",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="meshllm",
            interface_id="openai_api",
            purpose="Optional LLM backend for graphify's vision/extraction "
                    "pass. Graphify defaults to Claude (Anthropic API); "
                    "users who want fully-local extraction can configure "
                    "it to use MeshLLM (:9337/v1) instead.",
            config_key="OPENAI_API_BASE (set to http://localhost:9337/v1 "
                       "to route extraction through the mesh)",
            required=False,
            context=EngineeringContext(
                decision="Graphify can use MeshLLM as its extraction "
                         "backend instead of Claude.",
                observation="Graphify uses an LLM to extract concepts "
                            "and relationships from files. The default "
                            "is Claude (Anthropic), but it speaks "
                            "OpenAI-compat so any OpenAI-format endpoint "
                            "works.",
                reasoning="For a fully-local stack, route graphify's "
                          "extraction through MeshLLM or Ollama direct. "
                          "Claude gives better vision results for "
                          "images/diagrams, so the connection is "
                          "optional — users choose.",
                lineage="Graphify docs — https://github.com/Graphify-Labs/graphify",
                assumptions="MeshLLM has a vision-capable model if the "
                            "corpus contains images.",
            ),
        ),
        Connection(
            target_tool="litellm",
            interface_id="openai_api",
            purpose="Fallback LLM backend (general LiteLLM proxy on :4000).",
            config_key="OPENAI_API_BASE",
            required=False,
            context=_LITELLM_CONSUMER_CTX,
        ),
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Direct Ollama fallback for extraction (bypass both "
                    "meshes). Useful for single-node setups without "
                    "MeshLLM.",
            config_key="OPENAI_API_BASE (set to http://localhost:11434/v1)",
            required=False,
            context=EngineeringContext(
                decision="Ollama direct as a third extraction option.",
                observation="Same OpenAI-compat contract as MeshLLM "
                            "and LiteLLM.",
                reasoning="Single-node users who don't need mesh "
                          "pooling can point graphify straight at "
                          "Ollama for the extraction LLM calls.",
            ),
        ),
    ],
))

_reg(StackWiring(
    tool_id="meshllm",
    layer="Routing",
    interfaces=[
        ToolInterface(
            interface_id="openai_api",
            protocol="HTTP",
            api_format="OpenAI",
            port=9337,
            base_path="/v1",
            auth="API key (MESH_LLM_KEY, optional — local mesh is open by default)",
            description="MeshLLM unified API. Exposes a single "
                        "OpenAI-compatible endpoint that routes requests "
                        "across pooled GPUs/memory. Supports "
                        "/v1/chat/completions, /v1/models, "
                        "/v1/embeddings. The mesh decides whether a "
                        "model runs locally, routes to a peer node, or "
                        "uses Skippy stage splits for models too large "
                        "for one box. Use model='mesh' to fan out one "
                        "prompt to every model in the mesh (MoA gateway).",
            context=EngineeringContext(
                decision="MeshLLM as the mesh-pooling LLM gateway for "
                         "multi-node inference.",
                observation="MeshLLM pools GPUs and memory across "
                            "machines. Every node exposes the same /v1 "
                            "API. Requests are routed by the 'model' "
                            "field to the peer that can serve that "
                            "model. QUIC end-to-end encrypts peer "
                            "traffic via Iroh relays.",
                alternatives="LiteLLM (proxy only, no mesh pooling), "
                             "vLLM (single-node high-throughput), "
                             "direct Ollama (single-node).",
                constraints="mesh-llm setup must be run before first "
                            "serve. Multi-node mesh requires peers to "
                            "be discoverable via Nostr (public mesh) "
                            "or invite token (private mesh).",
                reasoning="MeshLLM is the only tool in the stack that "
                          "can split a model too large for one GPU "
                          "across multiple nodes (Skippy stage splits). "
                          "For single-node workloads, Ollama or LiteLLM "
                          "are simpler; MeshLLM shines when you add a "
                          "second machine.",
                verification="curl http://localhost:9337/v1/models",
                lineage="MeshLLM — https://github.com/Mesh-LLM/mesh-llm",
                assumptions="mesh-llm binary installed and `mesh-llm "
                            "setup` completed. At least one model is "
                            "available (auto-downloaded by `serve --auto` "
                            "or specified via --model).",
            ),
        ),
        ToolInterface(
            interface_id="mesh_web_console",
            protocol="HTTP",
            api_format="REST",
            port=3131,
            base_path="",
            auth="None (local only)",
            description="MeshLLM web console. Browser UI for mesh "
                        "management, node inventory, model routing, "
                        "and peer discovery. Use `mesh-llm serve "
                        "--headless` to hide the console while "
                        "keeping the management API.",
            context=EngineeringContext(
                decision="Expose a separate web console port for mesh "
                         "management.",
                observation="The console is a browser UI distinct from "
                            "the OpenAI-compat API. Operators use it "
                            "to monitor mesh health, add peers, and "
                            "configure model routing.",
                reasoning="Separating management UI from inference API "
                          "lets operators lock down :9337 (inference) "
                          "while keeping :3131 (console) accessible "
                          "only on the LAN.",
                verification="curl http://localhost:3131/",
                lineage="MeshLLM console — https://github.com/Mesh-LLM/mesh-llm",
                assumptions="MeshLLM was started without --headless.",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Optional: use Ollama as a local-model backend via "
                    "`mesh-llm client --auto` (API-only client mode). "
                    "When configured, MeshLLM routes to Ollama for "
                    "models not served by the mesh itself.",
            config_key="mesh-llm client --auto (reads OLLAMA_BASE_URL)",
            required=False,
            context=EngineeringContext(
                decision="Ollama is an OPTIONAL backend for MeshLLM, "
                         "not a required one.",
                observation="MeshLLM can load GGUF models directly "
                            "(--model /path/to/model.gguf) without "
                            "Ollama. The `mesh-llm client --auto` "
                            "subcommand turns MeshLLM into a pure "
                            "client that routes to other meshes or "
                            "Ollama-compatible backends.",
                reasoning="In the local-coder-mesh stack, most users "
                          "will run MeshLLM standalone (it auto-"
                          "downloads a suitable model). The Ollama "
                          "connection is for users who want to expose "
                          "their existing Ollama model fleet through "
                          "the mesh routing layer.",
            ),
        ),
    ],
))

# ──────────────────────────────────────────────────────────────────
# PiCode — coding agent, consumes mesh first, falls back to LiteLLM + Ollama
# ──────────────────────────────────────────────────────────────────
_reg(StackWiring(
    tool_id="picode",
    layer="Routing",
    interfaces=[],
    connections=[
        Connection(
            target_tool="meshllm",
            interface_id="openai_api",
            purpose="Primary LLM route for PiCode — mesh-pooled inference "
                    "across all available nodes.",
            config_key="OPENAI_API_BASE (set to http://localhost:9337/v1)",
            required=False,
            context=EngineeringContext(
                decision="PiCode points at MeshLLM first.",
                observation="MeshLLM's :9337 endpoint gives PiCode "
                            "access to every model in the mesh via "
                            "one URL.",
                alternatives="LiteLLM proxy (localhost:4000) or direct "
                             "Ollama (localhost:11434).",
                reasoning="Mesh-pooled inference is preferable when "
                          "available — it can serve models larger than "
                          "any single GPU via Skippy stage splits.",
                verification="Set OPENAI_API_BASE=http://localhost:9337/v1 "
                             "and list models.",
                lineage="PiCode — https://github.com/jasonjmcghee/picode",
                assumptions="MeshLLM is running and has at least one "
                            "model available.",
            ),
        ),
        Connection(
            target_tool="litellm",
            interface_id="openai_api",
            purpose="Fallback mesh (general LiteLLM proxy on :4000).",
            config_key="OPENAI_API_BASE",
            required=False,
            context=_LITELLM_CONSUMER_CTX,
        ),
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Direct Ollama fallback (bypass both meshes).",
            config_key="OPENAI_API_BASE",
            required=False,
            context=_CODING_AGENT_CTX,
        ),
    ],
))

# ──────────────────────────────────────────────────────────────────
# ZCoder — coding agent, same consumer pattern as PiCode
# ──────────────────────────────────────────────────────────────────
_reg(StackWiring(
    tool_id="zcoder",
    layer="DevOps",
    interfaces=[],
    connections=[
        Connection(
            target_tool="meshllm",
            interface_id="openai_api",
            purpose="Primary LLM route for ZCoder — mesh-pooled inference.",
            config_key="OPENAI_API_BASE (set to http://localhost:9337/v1)",
            required=False,
            context=EngineeringContext(
                decision="ZCoder points at MeshLLM first.",
                observation="Same OpenAI-compat contract as PiCode.",
                reasoning="Consistent routing across all coding agents "
                          "in the stack — they all prefer the mesh.",
                lineage="ZCoder (Zhipu AI)",
                assumptions="MeshLLM is running.",
            ),
        ),
        Connection(
            target_tool="litellm",
            interface_id="openai_api",
            purpose="Fallback mesh (general LiteLLM proxy).",
            config_key="OPENAI_API_BASE",
            required=False,
            context=_LITELLM_CONSUMER_CTX,
        ),
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Direct Ollama fallback (bypass both meshes).",
            config_key="OPENAI_API_BASE",
            required=False,
            context=_CODING_AGENT_CTX,
        ),
    ],
))

# ──────────────────────────────────────────────────────────────────
# Hermes WebUI — web frontend, backend is hermes_agent (NOT ollama direct)
# ──────────────────────────────────────────────────────────────────
_reg(StackWiring(
    tool_id="hermes_webui",
    layer="User Interfaces",
    interfaces=[
        ToolInterface(
            interface_id="hermes_webui_http",
            protocol="HTTP",
            api_format="REST",
            port=8081,
            base_path="",
            auth="WebUI auth (first-run admin signup)",
            description="Hermes-themed Open-WebUI instance. Separate "
                        "port (8081) and data volume from the general "
                        "openwebui instance so user accounts and RAG "
                        "corpus don't collide.",
            context=EngineeringContext(
                decision="Run a second Open-WebUI instance dedicated "
                         "to the Hermes stack.",
                observation="Open-WebUI supports multiple instances "
                            "with separate data-dir flags. The general "
                            "openwebui tool already occupies :3000 with "
                            "Ollama direct as backend.",
                alternatives="Use a single Open-WebUI instance with "
                             "model name prefixes (hermes/*).",
                constraints="Must run on a different port (8081) and "
                            "data-dir than the general openwebui.",
                reasoning="Dedicated Hermes UI keeps the Hermes agent "
                          "runtime as the single backend, so every "
                          "Hermes WebUI conversation flows through "
                          "hermes_agent's tool-use / function-calling "
                          "layer instead of raw Ollama.",
                verification="curl http://localhost:8081/health",
                lineage="Open-WebUI — https://github.com/open-webui/open-webui",
                assumptions="hermes_agent is running on :17051.",
            ),
        ),
    ],
    connections=[
        Connection(
            target_tool="hermes_agent",
            interface_id="hermes_agent_api",
            purpose="Primary backend — every chat goes through the "
                    "Hermes agent runtime (tool use, function calling).",
            config_key="OLLAMA_BASE_URL (set to http://localhost:17051)",
            required=True,
            context=EngineeringContext(
                decision="Hermes WebUI talks to hermes_agent, NOT "
                         "Ollama direct.",
                observation="hermes_agent exposes an OpenAI-compat "
                            "endpoint on :17051 that wraps Ollama with "
                            "Hermes function-calling logic.",
                reasoning="Routing through hermes_agent gives the "
                          "WebUI access to Hermes tool use without "
                          "requiring the user to wire it manually.",
            ),
        ),
        Connection(
            target_tool="ollama",
            interface_id="openai_api",
            purpose="Embedding model for RAG (nomic-embed-text). "
                    "Embeddings bypass hermes_agent for speed.",
            config_key="OLLAMA_BASE_URL (RAG_EMBEDDING_ENGINE=ollama)",
            required=False,
            context=EngineeringContext(
                decision="Use Ollama direct for embeddings, "
                         "hermes_agent for chat.",
                observation="Embeddings don't need Hermes function "
                            "calling — direct Ollama is faster.",
                reasoning="Splitting chat vs. embedding traffic "
                          "keeps hermes_agent focused on tool-use "
                          "calls.",
            ),
        ),
    ],
))
