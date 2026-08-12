# ADR-001: The Capability Architecture

**AI-LSC v3.0 — Ankh of Jah**

> *This is the single architectural definition for AI-LSC. Every module, every
> template, every resolver path either implements something defined here or it
> does not belong.*

---

## Status

**Accepted.** Adopted as the foundational architecture for v3.0 (Ankh of Jah)
and all subsequent releases. The agentic execution layer is deferred to v4.0.

---

## 1. Context

AI-LSC did not begin as an architecture. It began as a question:

> "Can I stop manually juggling a dozen AI tools on a Linux machine?"

v1 answered: *yes, with a monolithic script.*
v2 answered: *yes, with a modular registry and layers.*
v3 answers a different question entirely:

> "Can a system *understand* AI infrastructure well enough to deploy,
> validate, diagnose, and reproduce it — without the operator thinking
> about individual tools?"

The shift is from tool-first to system-first. Earlier development asked
"how do we add support for X?" Current development asks "where does X belong
in the architecture?" That is not a cosmetic change. It is a phase change.

Three releases revealed a consistent pattern: the same architectural verbs
kept reappearing across unrelated features. Install, verify, configure,
launch, monitor, export, diagnose, reproduce. Every tool needed them. Every
stack needed them. Every container needed them. The repetition was not a
failure to abstract — it was evidence of an abstraction waiting to be named.

This document names it.

---

## 2. The Foundational Object: Capability

Every system has one concept that, if removed, causes the entire structure to
collapse. For AI-LSC, that concept is **Capability**.

A Capability is a named, validated unit of infrastructure that a machine either
possesses or does not. It is not a tool. It is not a process. It is not a
package. It is a *statement about the machine*.

```
"Inference"    — this machine can run LLM inference.
"Vector Store"  — this machine can store and query embeddings.
"Monitoring"    — this machine can observe its own services.
"GPU Compute"   — this machine has CUDA/cuDNN available.
```

Capabilities are discovered, not declared. A tool *provides* capabilities. A
template *requires* capabilities. A pipeline *consumes* capabilities. A
container *exports* capabilities. A dashboard *reports* capabilities. A skill
*extends* capabilities. Monitoring *validates* capabilities.

Every subsystem points at Capability. No subsystem points at Tool directly
except the Registry, which maps tools to the capabilities they provide.

This single inversion eliminates most of the coupling in the application:

```
Tool         ──provides──►  Capability  ◄──requires──  Template
                              ▲
Pipeline     ──consumes──────┘
                              ▲
Container    ──exports───────┘
                              ▲
Dashboard    ──reports───────┘
                              ▲
Skill        ──extends───────┘
                              ▲
Monitoring   ──validates─────┘
```

Swap Ollama for vLLM. Swap Grafana for another observability stack. Swap
Qdrant for Milvus. Everything above the Registry layer does not notice.
The capability model remains stable even when implementations evolve,
technologies are replaced, or entirely new categories of AI software emerge.

---

## 3. The Architecture Pipeline

AI-LSC is not an installer. It is a pipeline from intent to infrastructure.

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTENT                              │
│                                                                  │
│  "I want a Research Workstation"                                  │
│  "I want a RAG Server"                                            │
│  "I want a GPU Inference Cluster"                                │
│  "I want a Coding Assistant"                                      │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                      TEMPLATE (Recipe)                             │
│                     Desired Architecture                          │
│                                                                  │
│  Research Workstation  │  RAG Appliance  │  Inference Node       │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                       RESOLVER                                    │
│                    Infrastructure Planning                        │
│                                                                  │
│  • Detect hardware         • Detect OS                            │
│  • Detect installed sw     • Detect conflicts                     │
│  • Expand dependencies     • Select implementations                │
│  • Produce execution plan                                           │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                       REGISTRY                                    │
│                   Individual Components                            │
│                                                                  │
│  Every tool knows: Install · Update · Verify · Launch             │
│                   Health · Configure · Container · Export         │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                        RUNTIME                                    │
│                                                                  │
│  Native  ·  Podman  ·  Docker  ·  LXC  ·  Cluster  ·  Remote     │
└──────────────────────────────────────────────────────────────────┘
```

The Resolver is the brain. It is the only component that translates between
the declarative world of templates and the imperative world of package
managers, container runtimes, and service launchers. No other component
performs this translation. This constraint ensures that adding a new runtime
target (say, Kubernetes) requires changes only in the Registry (new tool
entries) and Runtime (new executor), never in templates or pipelines.

---

## 4. Stack Recipes (Templates as Intent)

### 4.1 What a Template Is

A template is infrastructure intent, not an install script. It declares what
the operator wants the machine to become. It does not duplicate install
logic, configuration logic, or launch logic — the Registry already owns all
of that.

The current template format is a flat list of tool IDs. This is functional
but insufficient for the capability architecture. The evolved format — the
**Stack Recipe** — declares capabilities, roles, connections, and startup
semantics:

```yaml
# Stack Recipe — evolved template format (v4.0 target)
stack:
  name: Claude Memory Assistant
  version: "1.0"
  maturity: official          # official | community | local | frozen

capabilities:
  required:
    - inference               # needs an LLM engine
    - vector_database         # needs embedding storage
    - relational_database     # needs structured storage
    - web_interface           # needs a browser-accessible UI
  optional:
    - monitoring
    - automation

components:
  inference:
    engine: ollama
    model: llama3
  memory:
    vectordb: qdrant
    embedding_model: nomic-embed-text
  database:
    engine: postgres
  ui:
    provider: open_webui

connections:
  - from: inference
    to: vector_database
    protocol: embedding
  - from: inference
    to: relational_database
    protocol: session_store
  - from: ui
    to: inference
    protocol: openai_compat

startup:
  order:
    1. relational_database
    2. vector_database
    3. inference
    4. ui
  health_wait:
    - relational_database    # UI waits until DB is accepting connections
    - vector_database
    - inference

health:
  checks:
    - capability: inference
      probe: GET /api/tags
    - capability: vector_database
      probe: GET /collections
```

### 4.2 What a Template Is Not

A template does not contain:

- Installation commands (the Registry knows how to install)
- File paths (the Resolver knows the layout)
- Port assignments (conflict detection is automatic)
- OS-specific logic (the Resolver handles this)
- Dependency installation order beyond what `startup.order` declares

A template also does not hardcode implementations. It specifies roles:

```yaml
components:
  vector_database:
    role: vector_store        # NOT "qdrant"
```

The Resolver maps `vector_store` to whatever provider is installed or
available. On one machine that is Qdrant. On another it is Milvus. On a
third the Resolver recommends Chroma. The template never changes.

### 4.3 Template Maturity

Templates have a maturity level that signals trust and intent:

| Level | Meaning | Use Case |
|-------|---------|----------|
| **Official** | Maintained by the AI-LSC project | Curated reference stacks |
| **Community** | Shared by users, reviewed | Experimentation, collaboration |
| **Local** | Created by the operator | Personal workflows, one-off stacks |
| **Frozen** | Exact snapshot of a validated environment | Reproducibility, CI/CD, audit |

A Frozen template pins every version, every config hash, every capability
signature. Deploying a Frozen template on a different machine produces a
bit-for-bit equivalent environment. This is the mechanism for long-term
reproducibility — not containerization alone, but declarative infrastructure
with verified provenance.

---

## 5. Role-Based Resolution

The critical distinction between AI-LSC and every other "AI launcher" is
that templates specify **roles**, not implementations.

A role is a capability category with multiple possible providers:

```
Role: Inference Engine
  Providers:  Ollama  ·  llama.cpp  ·  vLLM  ·  TensorRT-LLM  ·  SGlang

Role: Vector Database
  Providers:  Qdrant  ·  Chroma  ·  Milvus  ·  Weaviate  ·  FAISS

Role: LLM Gateway
  Providers:  LiteLLM  ·  9Router Proxy  ·  Local proxy

Role: Monitoring
  Providers:  Grafana + Prometheus  ·  Glances  ·  Netdata

Role: Agent Frontend
  Providers:  Open WebUI  ·  LibreChat  ·  AnythingLLM  ·  Continue
```

The Resolver performs role resolution in this order:

1. **Already installed?** Use what is present.
2. **Compatible with hardware?** Select the best fit (GPU → CUDA-aware provider).
3. **Template preference?** Honor explicit provider hints.
4. **Fallback chain.** Try each candidate in order.
5. **Recommend.** If nothing installs cleanly, report what is needed.

This means a single template shared between two machines can resolve to
completely different toolsets:

```
"Research Workstation" template

Laptop (CPU-only):
  → llama.cpp (CPU inference)
  → LiteLLM (gateway)
  → Chroma (lightweight vector store)
  → Open WebUI (interface)

Desktop (RTX 4090):
  → Ollama (CUDA inference)
  → vLLM (high-throughput serving)
  → Qdrant (production vector store)
  → LibreChat (multi-provider interface)
```

Same template. Different reality. The Resolver is what makes that work.

---

## 6. Component Connections

Installing tools side-by-side is not an architecture. Understanding how they
interact is.

The Stack Recipe format includes a `connections` section that declares
relationships between components. These are not just documentation — they are
inputs to the Stack Doctor (Section 12) and the Resolver's validation
engine.

A connection declaration:

```yaml
connections:
  - from: ui            # Open WebUI
    to: inference        # Ollama
    protocol: openai_compat    # Expects OpenAI-compatible API
  - from: ui
    to: vector_database
    protocol: embedding  # Needs embedding endpoint
```

The Resolver uses connections to:

- Validate that protocols are compatible (OpenAI-compat ↔ OpenAI-compat).
- Detect likely misconfigurations (OLLAMA_HOST=localhost when UI is remote).
- Generate connection-specific health checks.
- Produce diagnostic suggestions when connections fail.

This is dependency injection for infrastructure. The template declares the
graph. The Resolver validates the graph. The Runtime instantiates the graph.

---

## 7. The 13-Layer Model

AI-LSC organizes all AI infrastructure into 13 layers. Each layer represents
a category of capability. Tools register into one (sometimes two) layers.
Templates reference layers instead of individual tools when expressing
broad requirements.

```
Layer 1   Host Platform          — OS, kernel, filesystem, base packages
Layer 2   Development Env        — Python, Rust, Node.js, Go, build tools
Layer 3   GPU Runtime             — CUDA, cuDNN, ROCm, Vulkan compute
Layer 4   Inference Engines      — Ollama, llama.cpp, vLLM, TensorRT-LLM
Layer 5   Distributed Runtime     — Ray, Kubeflow, cluster schedulers
Layer 6   AI Endpoints            — LiteLLM, model routers, API gateways
Layer 7   Data & Knowledge       — PostgreSQL, MariaDB, data pipelines
Layer 8   Knowledge Management   — Qdrant, Chroma, Milvus, vector stores
Layer 9   Automation & Execution   — n8n, Airflow, task schedulers
Layer 10  Observability          — Prometheus, Grafana, Glances, logging
Layer 11  Intelligent Routing     — Fabric, Hermes, agent dispatchers
Layer 12  User Interfaces         — Open WebUI, LibreChat, AnythingLLM
Layer 13  Containers             — Podman, Docker, LXC, export targets
```

A template can express requirements by layer:

```yaml
capabilities:
  layers:
    - Inference Engines       # Layer 4
    - AI Endpoints            # Layer 6
    - Knowledge Management   # Layer 8
    - User Interfaces         # Layer 12
```

The Resolver fills in everything else. If the template needs inference
(Layer 4) and the host has no GPU (Layer 3), the Resolver knows to
recommend CPU-only providers and skip CUDA-dependent tools automatically.

### Stress Test

The 13-layer model must accommodate any AI project without forcing it. A
non-exhaustive validation set:

| Project | Natural Layer Fit |
|---------|-------------------|
| Open WebUI | 12 (User Interfaces) |
| LiteLLM | 6 (AI Endpoints) |
| Qdrant | 8 (Knowledge Management) |
| Ollama | 4 (Inference Engines) |
| vLLM | 4 (Inference Engines) |
| ComfyUI | 12 (User Interfaces) |
| Flowise | 12 (User Interfaces) |
| n8n | 9 (Automation & Execution) |
| Prometheus | 10 (Observability) |
| Ray | 5 (Distributed Runtime) |
| Langflow | 12 (User Interfaces) |
| Chroma | 8 (Knowledge Management) |
| Milvus | 8 (Knowledge Management) |
| llama.cpp | 4 (Inference Engines) |
| TensorRT-LLM | 4 (Inference Engines) |
| OpenHands | 12 (User Interfaces) |
| Aider | 2 (Development Env) |
| Continue | 2 (Development Env) |
| Kubeflow | 5 (Distributed Runtime) |
| Kafka | 7 (Data & Knowledge) |

Every project in the validation set fits naturally into exactly one layer.
None require special casing. The model appears to generalize well.

---

## 8. Skills as Derived Capabilities

Skills are not file lookups. They are capability queries.

The old model: "Does this Python file exist in the skills directory?"
The new model: "Does this machine currently possess this capability?"

Skills derive from deployed, validated infrastructure:

```
Template: Research Workstation
    │
    ▼  Deployed
    │
    ▼  Verified
    │
    ▼  Registered as Capabilities
    │
    ▼  Skills become available:
    │
    ├── "Local RAG"        (has: inference + vector_store + ui)
    ├── "Python AI"        (has: development + inference)
    ├── "Vision"           (has: inference + multimodal_model)
    ├── "Speech"           (has: inference + whisper + tts)
    └── "Distributed Inference"  (has: inference + distributed_runtime)
```

A skill definition references capabilities, not tools:

```yaml
skill:
  name: Local RAG
  requires:
    capabilities: [inference, vector_database, web_interface]
  optional:
    capabilities: [monitoring, relational_database]
  description: >
    End-to-end retrieval-augmented generation using local models.
    Available when the machine has an inference engine, a vector store,
    and a web interface — regardless of which specific tools provide them.
```

This means installing a new tool that provides an existing capability can
silently unlock skills the operator never explicitly configured. Replace
Qdrant with Milvus and every RAG skill still works, because the capability
did not change — only the provider did.

---

## 9. Pipelines Consume Capabilities

A pipeline is a directed graph of capability requirements. It never names a
tool. It names what it needs:

```
Pipeline: Document RAG

  [Source] → [Chunking] → [Embedding] → [Vector Store] → [Retriever] → [LLM] → [Output]
```

Each node is a capability. The Resolver maps each node to a tool at runtime:

```
Embedding:
  → nomic-embed-text (via Ollama)
  or
  → bge-small (via llama.cpp)

Vector Store:
  → Qdrant
  or
  → Chroma

LLM:
  → Ollama (llama3)
  or
  → vLLM (deepseek-coder-33b)
```

The pipeline graph never changes when implementations change. This is what
makes pipelines portable across machines, containers, and clusters.

---

## 10. Container Export as Capability Export

A container image is not a bag of tools. It is a frozen capability set.

When an operator exports a Research Workstation to Podman, the exported
image carries a capability manifest alongside the filesystem layers:

```
Research_Workstation_v1.0

  Capabilities:
    ✓ Inference (Ollama, llama3)
    ✓ GPU Compute (CUDA 12.4, cuDNN 9.1)
    ✓ Vector Database (Qdrant)
    ✓ LLM Gateway (LiteLLM)
    ✓ Web Interface (Open WebUI)
    ✓ Monitoring (Prometheus + Grafana)
    ✓ Relational Database (PostgreSQL)

  Stack Recipe: embedded (frozen)
  Template: Research Workstation v1.0
  Exported: 2026-06-28
  Architecture: x86_64
```

When another machine imports this image, AI-LSC reads the manifest and
immediately knows what the container provides — no scanning, no probing, no
guessing. The capabilities are declared, trusted, and verified.

Export targets are format-agnostic:

```
Recipe → Resolver → Generate Deployment
                    ├── Podman Quadlet
                    ├── Docker Compose
                    ├── LXC Config
                    └── Kubernetes YAML (future)
```

The recipe never changes. Only the exporter changes.

---

## 11. Dashboards Report Capability Health

The dashboard does not display process status. It displays infrastructure
health.

```
┌──────────────────────────────────────────────────────┐
│  Research Workstation                     ████████ 92%│
│                                                       │
│  Host Platform          ✓                             │
│  Development Env        ✓                             │
│  GPU Runtime            ⚠ CUDA Update Available       │
│  Inference Engines      ✓  Ollama · llama3            │
│  AI Endpoints           ✓  LiteLLM :4000               │
│  Data & Knowledge       ✓  PostgreSQL :5432            │
│  Knowledge Management   ✓  Qdrant :6333                │
│  Automation             —                             │
│  Observability          ✓  Grafana · Prometheus         │
│  Intelligent Routing    ✓  Fabric                      │
│  User Interfaces        ✓  Open WebUI :8080            │
│  Containers             2 specialist images            │
│                                                       │
│  Templates: 7 installed    Skills: 12 available        │
└──────────────────────────────────────────────────────┘
```

Each row is a capability, not a tool. The status reflects whether the
machine possesses that capability in a healthy state, regardless of which
tool provides it. If the operator swaps Grafana for Netdata, the
Observability row still shows the same status — because the capability
did not change.

---

## 12. Stack Doctor

The Stack Doctor is a reasoning engine, not a log viewer. It understands
relationships between components and can diagnose problems that span multiple
tools.

Example diagnosis:

```
DIAGNOSIS: Open WebUI cannot reach Ollama

REASON: OLLAMA_HOST is set to localhost (127.0.0.1)
        but Open WebUI is configured to connect to port 11434
        on all interfaces. Connection is refused.

RECOMMENDATION:
  Option A: Set OLLAMA_HOST=0.0.0.0 in Ollama environment
  Option B: Bind Open WebUI to localhost only
  Option C: Route through LiteLLM proxy
```

Example conflict detection:

```
DIAGNOSIS: Port conflict detected

  LiteLLM wants port 4000  ✓ (available)
  vLLM wants port 8000      ✗ (occupied by TensorRT-LLM)

RECOMMENDATION:
  Move LiteLLM to port 4001
  or
  Disable TensorRT-LLM if not needed
```

The Stack Doctor uses the connection graph from the Stack Recipe to trace
problems across component boundaries. It does not just check if a process is
running — it checks if the *capability chain* is intact from end to end.

---

## 13. Operator Workflows

### 13.1 Missions

Complex deployments are presented as **Missions**, not wizards. A Mission
is a named, scoped objective with a clear completion state:

```
┌──────────────────────────────────────────────────────┐
│  MISSION: Build Coding Assistant                      │
│                                                       │
│  Estimated effort: 8 minutes                           │
│  Status: Planning...                                   │
│                                                       │
│  [✓] Validate host platform                            │
│  [✓] Detect installed capabilities                     │
│  [→] Resolve missing dependencies                      │
│  [ ] Install Python (Layer 2)                          │
│  [ ] Install Ollama (Layer 4)                          │
│  [ ] Install LiteLLM (Layer 6)                         │
│  [ ] Install Open WebUI (Layer 12)                     │
│  [ ] Configure connections                             │
│  [ ] Verify health                                     │
│  [ ] Export ready                                      │
└──────────────────────────────────────────────────────┘
```

### 13.2 Routines

Routines are reusable infrastructure actions, not application macros:

| Routine | Actions |
|---------|---------|
| **Morning Check** | Verify all services, restart unhealthy, check updates, check GPU, check disk |
| **Pre-Inference** | GPU memory, temperature, ports, models, KV cache, endpoint ready |
| **Before Export** | Verify services, verify configs, clean logs, freeze versions, generate manifest |
| **Before Commit** | Lint, test, validate registry, validate templates, schema check |

One button. Comprehensive validation.

### 13.3 Next Best Action

AI-LSC suggests the operator's next step based on current state:

```
Good morning.
  ✓ GPU healthy
  ✓ Ollama healthy
  ⚠ Open WebUI update available (v0.3.12 → v0.3.14)
  ⚠ Research Workstation template has 1 missing dependency

Suggested: Verify Research Workstation
```

This is not AI. It is deterministic inference over the capability graph.
The system knows what is installed, what is healthy, what is outdated, and
what templates require. The recommendation follows directly.

### 13.4 Activity Timeline

Every infrastructure action is recorded with a timestamp:

```
09:13  Installed LiteLLM
09:15  Verified CUDA (driver 550.54, CUDA 12.4)
09:16  Generated template: Research Workstation
09:20  Exported Podman image: research_ws_v1.0
09:27  Health check passed (13/13 capabilities)
```

Timelines are queryable, filterable, and exportable. They provide audit
trail and operational memory.

### 13.5 Workspaces

Workspaces group related infrastructure by purpose, not by tool:

```
Research   → inference + vector_db + ui + monitoring
Coding     → development + inference + endpoints + ui
RAG        → inference + vector_db + relational_db + ui
Cluster    → distributed + inference + monitoring + containers
```

Click a workspace. Everything related appears. One context for one purpose.

---

## 14. Adaptive Templates

A single template adapts to the host hardware, installed software, and
available runtimes. The Resolver selects implementations based on
constraints, not preferences.

```
"Research Workstation" on different hardware:

Laptop (CPU, 16GB RAM):
  → llama.cpp (quantized, CPU inference)
  → Chroma (in-process vector store, minimal memory)
  → LiteLLM (lightweight gateway)
  → Glances (lightweight monitoring)
  → Open WebUI (browser interface)

Desktop (RTX 4090, 64GB RAM):
  → Ollama (CUDA-accelerated inference)
  → Qdrant (production vector store with GPU-accelerated HNSW)
  → LiteLLM + vLLM (dual gateway: fast + thorough)
  → Prometheus + Grafana (full monitoring stack)
  → LibreChat (multi-provider interface)

Server (Dual MI300X, 256GB RAM):
  → SGLang (ROCm-optimized inference)
  → Milvus (distributed vector store)
  → LiteLLM (cluster gateway)
  → Prometheus + Grafana + AlertManager (production monitoring)
  → Open WebUI (load-balanced)
```

Same template. Same intent. Different reality. The Resolver is what makes
the template portable.

---

## 15. Rationale

### Why Capability as the central abstraction?

Because tools are ephemeral. The AI landscape changes monthly. New inference
engines appear. Old ones are abandoned. Monitoring stacks get replaced.
Vector databases get acquired and deprecated.

But the *capabilities* those tools provide are remarkably stable. "The
machine can run LLM inference" has been true since 2023 and will be true
in 2030. The implementation changes. The capability does not.

Building around capabilities means AI-LSC's architecture decays at the
rate of the AI industry's *conceptual* evolution, not its *tool* churn.
Conceptual evolution is orders of magnitude slower.

### Why not just use Terraform / Kubernetes?

Because those tools solve a different problem. Terraform manages cloud
infrastructure declaratively. Kubernetes orchestrates containers at scale.
Neither understands that "install Qdrant" implies "the machine now has
vector database capability" — nor should they. That is AI-LSC's domain.

AI-LSC is specifically designed for the local AI operator who needs to
assemble, validate, and reproduce AI stacks on single machines or small
clusters. It fills the gap between "install scripts" and "cloud
orchestration."

### Why role-based resolution instead of tool-specific templates?

Because a template that hardcodes Qdrant cannot run on a machine that only
has Milvus. A template that hardcodes Ollama cannot leverage an existing
vLLM installation. Role-based resolution makes templates portable,
shareable, and future-proof without requiring the template author to
anticipate every possible provider.

---

## 16. Consequences

### Positive

- **Tool swaps are zero-cost above the Registry.** Replacing a provider
  requires only a new Registry entry with the same capability mapping.
  Templates, pipelines, skills, and dashboards are unaffected.
- **Templates are shareable across heterogeneous hardware.** The same
  recipe produces appropriate deployments on laptops, desktops, and
  servers.
- **New capabilities can be added without modifying existing templates.**
  Adding a "Speech-to-Text" capability does not require touching any
  Research Workstation template.
- **Container exports carry semantic meaning**, not just filesystem
  state. Importing a container immediately reveals its capabilities.
- **Diagnostics can reason about relationships**, not just individual
  process health.

### Neutral

- **The Resolver is the most complex component.** It must understand
  hardware detection, OS differences, dependency graphs, conflict
  resolution, and provider selection. This is acceptable because the
  Resolver is a single, well-bounded component.
- **The capability vocabulary must be curated.** New capabilities require
  consensus on naming, boundaries, and provider criteria. This is a
  governance concern, not a technical one.

### Risks

- **Over-abstraction.** If the capability vocabulary is too coarse
  ("compute"), it loses discriminating power. If too fine ("qdrant-hnsw-
  gpu"), it reverts to tool-specific coupling. The granularity must be
  calibrated through real-world use.
- **Resolver complexity.** A naive Resolver that tries all combinations
  is NP-hard. The Resolver must use heuristics, caching, and constraint
  propagation to remain fast.
- **Capability drift.** As the AI ecosystem evolves, capabilities may
  split or merge. "Inference" might split into "Text Inference" and
  "Multimodal Inference." The architecture must handle capability
  evolution without breaking existing templates.

---

## 17. Architecture Completeness

Current state of implementation (v3.0 Ankh of Jah):

```
Registry (tool metadata, 115 tools)          ████████████░ 95%
Templates (stack recipes, 4 templates)        ██████░░░░░░ 55%
Resolver (dependency expansion, planning)    ███░░░░░░░░░ 30%
Installer (native, git, npm, pip)            ████████████░ 95%
Verification (install checks, health probes) ██████████░░░ 85%
Health (service status, GPU monitoring)       ███████░░░░░ 65%
Export (Podman, Docker, LXC configs)         ████████░░░░ 80%
Monitoring (glances integration, Prometheus) █████░░░░░░░ 50%
Skills (capability-derived skills)            ███░░░░░░░░░ 25%
Pipelines (capability graph execution)      ██░░░░░░░░░░ 20%
Dashboards (capability health display)       ████░░░░░░░░ 35%
Stack Doctor (diagnostic reasoning)          ██░░░░░░░░░░ 15%
Missions (guided deployment flows)            █░░░░░░░░░░░ 10%
Workspaces (purpose-based grouping)           ███░░░░░░░░░ 25%
Activity Timeline                            ██░░░░░░░░░░ 20%
Next Best Action                             █░░░░░░░░░░░ 10%
Documentation (this ADR, README, guides)     ██████░░░░░░ 55%
Tests                                        ██░░░░░░░░░░ 20%
```

The pattern is clear: the foundation (Registry, Installer, Verification) is
strong. The intelligence layer (Resolver, Stack Doctor, Missions) is where
the next investment goes. The UI layer (Dashboards, Workspaces, Timeline)
follows the intelligence layer.

---

## 18. Feature Policy (Ankh of Jah Stabilization)

v3.0 enters a stabilization phase. Feature velocity decreases; stability
velocity increases.

### Allowed

- Bug fixes
- Registry additions (new tool metadata, new providers)
- New templates (stack recipes)
- Installer verification and hardening
- UI polish and usability improvements
- Documentation
- Tests
- Capability vocabulary refinement
- Resolver heuristic improvements

### Not Allowed

- New architectural concepts
- New runtime systems
- Major UI redesigns
- New registry formats (schema changes)
- Agent execution (deferred to v4.0)
- Cluster orchestration (deferred to v4.0)
- Remote node management (deferred to v4.0)

### v4.0 Scope (Deferred)

The agentic execution layer — where an LLM operates AI-LSC through
function-calling, using the agents/ bridge to start/stop services, pull
models, inject skills, and diagnose issues through natural language. This
is architecturally designed (agents/ package exists, tool_bridge and
ollama_tools are implemented, Redis pub/sub infrastructure is in place)
but intentionally not activated in v3.0.

---

## 19. Project Philosophy

AI-LSC is a native-first, metadata-driven infrastructure manager for local
AI systems. It treats AI software as reusable infrastructure rather than
isolated applications, enabling reproducible deployments, validation,
monitoring, and export of complete AI environments.

This single paragraph is the decision filter for every proposed feature.
If a feature supports this philosophy — making AI infrastructure easier to
deploy, validate, reproduce, and understand — it belongs. If it does not,
it does not.

AI-LSC's biggest competitor is not another AI launcher. It is the manual
process that most developers still follow: reading installation guides,
cloning repositories, creating Python environments, debugging version
conflicts, writing ad hoc shell scripts, and hoping they can recreate the
setup six months later.

If AI-LSC can replace that with: select a template, review the execution
plan, deploy, verify, export — then it has solved a real engineering
problem.

---

## 20. The Architectural Vocabulary

These terms are stable. They will not change in v3.0 patches. They may
evolve in v4.0, but only with explicit ADR amendment.

| Term | Definition |
|------|-----------|
| **Capability** | A named, validated unit of infrastructure that a machine possesses or does not. The central abstraction. |
| **Template / Stack Recipe** | A declarative document expressing infrastructure intent. Specifies capabilities and roles, not tools. |
| **Resolver** | The planning engine that maps intent to execution. Detects hardware, resolves roles, expands dependencies, produces plans. |
| **Registry** | The knowledge base of individual tools. Each entry maps a tool to its capabilities, installers, launchers, health probes, and exporters. |
| **Role** | A capability category with multiple possible providers (e.g., "Vector Database" → Qdrant, Chroma, Milvus). |
| **Skill** | A capability-derived behavior. Available when all required capabilities are present and healthy. |
| **Pipeline** | A directed graph of capability requirements. Consumes capabilities; does not name tools. |
| **Connection** | A declared relationship between two components in a Stack Recipe. Used for validation and diagnostics. |
| **Stack Doctor** | A diagnostic reasoning engine that traces problems across component boundaries using the connection graph. |
| **Mission** | A named, scoped deployment objective with a clear completion state. |
| **Routine** | A reusable infrastructure action (health check, pre-flight, cleanup). |
| **Workspace** | A purpose-based grouping of related infrastructure. |
| **Frozen** | An exact snapshot of a validated environment, pinned at every version. |
| **Layer** | One of 13 categories of AI infrastructure. Tools register into layers. Templates can reference layers. |
| **Runtime** | The execution target: native, Podman, Docker, LXC, cluster, or remote. |

---

*Ankh of Jah marks the point where AI-LSC stopped being a Python application
and became a platform architecture. Future releases build on this foundation.
They do not revisit it.*
