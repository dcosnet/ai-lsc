"""
AI-LSC / Open Engineer -- Built-in OE-derived stack templates.

These templates demonstrate the standard template format by mapping
Open Engineer's engineering principles to practical AI-LSC tool stacks.
Each template carries full OE engineering context (the "why") alongside
the AI-LSC stack configuration (the "what").

The templates live here as Python-generated JSON and are registered
with StackTemplateManager at import time via :func:`get_templates`.
"""

from __future__ import annotations

from ai_lsc.registry.openengineer.schema import StandardTemplate


def get_templates() -> list[StandardTemplate]:
    """Return all built-in OE-derived StandardTemplates.

    Each template maps an Open Engineer concept or example discipline
    to an AI-LSC tool stack that helps preserve and apply that concept.
    """
    return [
        _thread_integrity_stack(),
        _verification_loop_stack(),
        _stewardship_stack(),
        _observation_first_stack(),
        _context_preservation_stack(),
        _engineering_decisions_stack(),
    ]


# ── Template definitions ───────────────────────────────────────────

def _thread_integrity_stack() -> StandardTemplate:
    """Thread Integrity -- the knowledge continuity stack.

    Preserves the reasoning chain so future practitioners can
    reconstruct why decisions were made.  Maps to OE-0001 (Foundation)
    and the thread integrity concept.
    """
    return StandardTemplate(
        template_id="oe-thread-integrity",
        name="OE Thread Integrity -- Knowledge Continuity Stack",
        version="1.0.0-oe-rc3",
        author="openengineer",
        description=(
            "Preserve engineering reasoning across generations. "
            "RAG-backed knowledge base + structured documentation + "
            "vector search ensures the thread of understanding "
            "remains intact."
        ),
        source_type="native",
        oe_spec_refs=["OE-0001", "OE-0003", "OE-0009"],
        engineering_context={
            "decision": (
                "Deploy a multi-store knowledge continuity system "
                "using Qdrant (semantic vector memory), ChromaDB "
                "(document embeddings), Redis (hot-path cache), and "
                "MariaDB (persistent structured storage) to preserve "
                "the reasoning chain behind engineering decisions."
            ),
            "observation": (
                "Engineers across all disciplines report that inherited "
                "systems without context records require significantly "
                "more effort to maintain, modify, or extend than systems "
                "with preserved reasoning. Knowledge continuity breaks "
                "when context is lost between practitioners."
            ),
            "alternatives": (
                "1. Flat file storage -- simple but lacks semantic "
                "search, no cross-reference capability.\n"
                "2. Wiki/confluence -- unstructured, no schema "
                "enforcement, context decays over time.\n"
                "3. Git-only history -- preserves what changed but "
                "not why it changed.\n"
                "4. Pure vector DB -- semantic search but no "
                "structured field validation (fails OE-0000 criterion 1)."
            ),
            "constraints": (
                "Must support OE-0000 conformance criteria for context "
                "records. Must provide both semantic search (vector) "
                "and structured field queries (relational). Must operate "
                "entirely on localhost for privacy and latency."
            ),
            "reasoning": (
                "The multi-store approach maps to the OE knowledge "
                "hierarchy: Redis carries hot-path session state (ms "
                "latency), Qdrant carries semantic memory for RAG "
                "retrieval, ChromaDB provides dedicated document chunk "
                "embeddings, and MariaDB persists structured context "
                "records with field-level validation. This satisfies "
                "OE-0001's requirement that the thread carry understanding, "
                "not just information."
            ),
            "verification": (
                "Thread integrity is measured by whether a subsequent "
                "practitioner can reconstruct the reasoning behind a "
                "prior decision without direct access to the original "
                "decision-maker (OE-0001). The vector search recall rate "
                "and structured query completeness provide quantitative "
                "verification."
            ),
            "lineage": (
                "Directly implements OE-0003 (Engineering Context), "
                "OE-0009 (Stewardship), and OE-0010 (Inheritance). "
                "The Antikythera example (examples/antikythera.md) "
                "demonstrates the cost of thread integrity failure."
            ),
            "assumptions": (
                "Assumes that engineering context can be partially "
                "captured in structured records (acknowledges OE-0003 "
                "known limitation regarding tacit knowledge). Assumes "
                "vector embeddings provide sufficient semantic fidelity "
                "for cross-domain context retrieval."
            ),
        },
        stack_config={
            "id": "oe-thread-integrity",
            "name": "OE Thread Integrity -- Knowledge Continuity Stack",
            "description": (
                "Preserve engineering reasoning with multi-store "
                "knowledge continuity: vector memory + structured "
                "records + hot cache."
            ),
            "version": "1.0.0-oe-rc3",
            "author": "openengineer",
            "tags": [
                "openengineer", "thread-integrity", "knowledge",
                "rag", "stewardship", "local-first",
            ],
            "tools": [
                "ollama", "qdrant", "chromadb", "redis", "mariadb",
                "litellm", "openwebui", "fabric", "markitdown",
            ],
            "endpoints": {
                "qdrant": "http://localhost:6333",
                "chromadb": "http://localhost:8000",
                "redis": "localhost:6379",
                "mariadb": "localhost:3306",
                "litellm": "http://localhost:4000",
                "openwebui": "http://localhost:8080",
            },
        },
        notes={
            "oe_concept": "thread_integrity",
            "memory_hierarchy": (
                "Redis (hot, ms latency) -> Qdrant (semantic, us) -> "
                "ChromaDB (document chunks) -> MariaDB (persistent, ms)"
            ),
            "setup_order": [
                "1. MariaDB, Redis (infrastructure)",
                "2. Qdrant, ChromaDB (memory)",
                "3. Ollama, LiteLLM (inference)",
                "4. OpenWebUI (interface)",
                "5. Fabric, MarkItDown (content tools)",
            ],
        },
    )


def _verification_loop_stack() -> StandardTemplate:
    """Verification Loop -- the observation-verification cycle stack.

    Maps to OE-0007 (Verification) and the verification loop concept
    from OE-0001: observe -> verify -> deepen -> repeat.
    """
    return StandardTemplate(
        template_id="oe-verification-loop",
        name="OE Verification Loop -- Test Against Reality Stack",
        version="1.0.0-oe-rc3",
        author="openengineer",
        description=(
            "Close the loop between observation and verification. "
            "Automated testing + monitoring + code review ensures "
            "understanding is tested against reality at every stage."
        ),
        source_type="native",
        oe_spec_refs=["OE-0001", "OE-0004", "OE-0007", "OE-0008"],
        engineering_context={
            "decision": (
                "Deploy a verification pipeline combining Aider (code "
                "generation + testing), Glances (runtime monitoring), "
                "Prometheus/Grafana (metrics collection), and Opik "
                "(LLM output evaluation) to close the verification loop "
                "defined in OE-0007."
            ),
            "observation": (
                "No amount of reasoning, no matter how elegant, "
                "substitutes for verification. An engineering model "
                "that has not been verified is a hypothesis -- "
                "potentially valuable, but not yet reliable enough to "
                "base decisions on (OE-0007)."
            ),
            "alternatives": (
                "1. Manual testing only -- slow, non-repeatable, "
                "doesn't scale.\n"
                "2. CI-only verification -- misses runtime behavior, "
                "no continuous monitoring.\n"
                "3. LLM self-evaluation -- introduces confirmation "
                "bias, needs independent verification (OE-0004)."
            ),
            "constraints": (
                "Verification must test against observable outcomes, "
                "not against models or opinions (OE-0000 criterion 6). "
                "Must support both automated and human-in-the-loop "
                "verification. Must be able to measure understanding "
                "reconstruction success."
            ),
            "reasoning": (
                "The verification loop (OE-0007) closes with observation: "
                "observe -> survey -> understand -> verify -> (if fail) "
                "return to observation. This stack provides tooling at "
                "each stage: Aider generates and tests code, Opik evaluates "
                "LLM reasoning quality, Glances/Prometheus/Grafana monitor "
                "runtime behavior, and Fabric transforms verification "
                "results into structured records."
            ),
            "verification": (
                "The stack is verified by: (1) running Aider's test "
                "suite on a known codebase and confirming it catches "
                "seeded bugs, (2) confirming Glances reports match "
                "Prometheus metrics, (3) confirming Opik evaluation "
                "scores correlate with human assessment."
            ),
            "lineage": (
                "Implements the verification loop defined in OE-0007 "
                "and the spiral re-evaluation concept from OE-0001. "
                "Builds on the observation-first principle (RFC-0001)."
            ),
            "assumptions": (
                "Assumes that automated verification can catch a "
                "meaningful fraction of engineering errors. Assumes "
                "LLM evaluation metrics (Opik) provide useful signal "
                "for reasoning quality assessment."
            ),
        },
        stack_config={
            "id": "oe-verification-loop",
            "name": "OE Verification Loop -- Test Against Reality Stack",
            "description": (
                "Close the observation-verification cycle with "
                "automated testing, runtime monitoring, and LLM "
                "evaluation."
            ),
            "version": "1.0.0-oe-rc3",
            "author": "openengineer",
            "tags": [
                "openengineer", "verification", "testing",
                "monitoring", "spiral-re-evaluation", "local-first",
            ],
            "tools": [
                "ollama", "aider", "fabric", "ripgrep", "fd",
                "tree_sitter", "glances", "prometheus", "grafana",
                "opik",
            ],
            "endpoints": {
                "ollama": "http://localhost:11434/v1",
                "glances": "http://localhost:61208",
                "prometheus": "http://localhost:9090",
                "grafana": "http://localhost:3000",
                "opik": "http://localhost:3000",
            },
        },
        notes={
            "oe_concept": "verification_loop",
            "spiral_note": (
                "Each verification cycle either eliminates ambiguity "
                "or strengthens traceability (OE-0011, Amendment). "
                "This is spiral re-evaluation, not linear iteration."
            ),
        },
    )


def _stewardship_stack() -> StandardTemplate:
    """Stewardship -- the knowledge maintenance and transmission stack.

    Maps to OE-0009 (Stewardship) and OE-0010 (Inheritance).
    """
    return StandardTemplate(
        template_id="oe-stewardship",
        name="OE Stewardship -- Knowledge Maintenance Stack",
        version="1.0.0-oe-rc3",
        author="openengineer",
        description=(
            "Maintain and improve engineering knowledge for future "
            "practitioners. Document management + knowledge graph + "
            "note-taking + RAG ensures context survives handoffs."
        ),
        source_type="native",
        oe_spec_refs=["OE-0003", "OE-0009", "OE-0010"],
        engineering_context={
            "decision": (
                "Deploy a knowledge stewardship stack with Paperless-NGX "
                "(document archive), Obsidian (knowledge graph notes), "
                "Logseq (outliner), and OpenWebUI+RAG (AI-assisted "
                "context retrieval) to implement OE-0009 Stewardship "
                "and OE-0010 Inheritance."
            ),
            "observation": (
                "The most durable knowledge systems -- open-source "
                "software, professional engineering bodies, craft "
                "guilds -- are governed by stewardship rather than "
                "ownership (RFC-0005). The Roman concrete example "
                "(examples/roman-concrete.md) shows how stewardship "
                "failure (transmitting prescriptions, not principles) "
                "causes understanding loss for millennia."
            ),
            "alternatives": (
                "1. Shared drive only -- no structure, no graph, "
                "no AI-assisted retrieval.\n"
                "2. Confluence/Notion -- cloud-dependent, proprietary, "
                "no local-first guarantee.\n"
                "3. Git-only docs -- preserves artifacts but not "
                "reasoning, no knowledge graph."
            ),
            "constraints": (
                "Must support both the transmit discipline (stewardship) "
                "and the receive discipline (inheritance). Must flag "
                "obsolete or incorrect context. Must work offline "
                "(OE-0009 known limitation regarding proprietary content)."
            ),
            "reasoning": (
                "Stewardship and inheritance are coupled but distinct: "
                "stewardship is the transmit direction, inheritance is "
                "the receive direction. Paperless-NGX provides the "
                "document archive (storing artifacts), Obsidian provides "
                "the knowledge graph (connecting reasoning), and RAG "
                "via OpenWebUI allows AI-assisted context retrieval "
                "(supporting inheritance by helping new practitioners "
                "reconstruct understanding)."
            ),
            "verification": (
                "Stewardship success is measured by whether inherited "
                "context enables understanding reconstruction (OE-0001 "
                "thread integrity test). Practical test: can a new team "
                "member explain a past decision using only the preserved "
                "context records?"
            ),
            "lineage": (
                "Directly implements OE-0009 (Stewardship) and "
                "OE-0010 (Inheritance). The Bessemer process example "
                "(examples/inheritance-steelmaking.md) demonstrates "
                "active vs. passive inheritance."
            ),
            "assumptions": (
                "Assumes that structured knowledge representation "
                "(markdown, knowledge graphs) captures sufficient "
                "explicit context to support inheritance. Acknowledges "
                "OE-0003's known limitation regarding tacit knowledge."
            ),
        },
        stack_config={
            "id": "oe-stewardship",
            "name": "OE Stewardship -- Knowledge Maintenance Stack",
            "description": (
                "Steward engineering knowledge across generations "
                "with document management, knowledge graphs, and "
                "AI-assisted context retrieval."
            ),
            "version": "1.0.0-oe-rc3",
            "author": "openengineer",
            "tags": [
                "openengineer", "stewardship", "inheritance",
                "knowledge-management", "documentation", "local-first",
            ],
            "tools": [
                "ollama", "openwebui", "chromadb", "docling",
                "markitdown", "whisper", "fabric", "paperlessngx",
                "obsidian", "logseq",
            ],
            "endpoints": {
                "ollama": "http://localhost:11434",
                "openwebui": "http://localhost:8080",
                "chromadb": "http://localhost:8000",
                "paperlessngx": "http://localhost:8000",
            },
        },
        notes={
            "oe_concept": "stewardship",
            "transmit_receive": (
                "Stewardship (transmit) and Inheritance (receive) are "
                "coupled but face different failure modes: stewardship "
                "fails through neglect, inheritance fails through "
                "passivity (OE-0009)."
            ),
        },
    )


def _observation_first_stack() -> StandardTemplate:
    """Observation First -- the data collection and measurement stack.

    Maps to OE-0004 (Observation) and RFC-0001 (Observation First).
    """
    return StandardTemplate(
        template_id="oe-observation-first",
        name="OE Observation First -- Data Collection Stack",
        version="1.0.0-oe-rc3",
        author="openengineer",
        description=(
            "Observe first. Collect, parse, and structure data from "
            "multiple sources before reasoning. Web scraping + "
            "document parsing + audio transcription + data pipeline "
            "tools feed the observation layer."
        ),
        source_type="native",
        oe_spec_refs=["OE-0004", "OE-0005", "OE-0001"],
        engineering_context={
            "decision": (
                "Deploy a multi-modal data collection pipeline with "
                "Crawl4AI (web scraping), Docling + MarkItDown (document "
                "parsing), Whisper (audio transcription), OpenDataLoader "
                "(structured data), and Elasticsearch + Meilisearch "
                "(search) to implement the observation-first principle."
            ),
            "observation": (
                "Throughout the development of Open Engineer, the most "
                "robust principles emerged from verifiable encounters "
                "with reality (RFC-0001). Henry Darcy's 1856 work "
                "demonstrated that measuring first, theorizing second "
                "produces principles that endure 160+ years "
                "(examples/observation-first-darcy.md)."
            ),
            "alternatives": (
                "1. Manual data collection only -- slow, incomplete, "
                "not reproducible.\n"
                "2. Single-source scraping -- misses multi-modal "
                "observations (web + documents + audio).\n"
                "3. LLM-only extraction -- introduces model bias, "
                "violates observation-first (model is not reality)."
            ),
            "constraints": (
                "Observations must be verifiable encounters with reality "
                "(OE-0004). The pipeline must distinguish direct "
                "observations from corroborated observations. Must "
                "support the survey aggregation step (OE-0005)."
            ),
            "reasoning": (
                "OE-0004 defines two observation categories: direct "
                "(measurements, experiments) and corroborated "
                "(independently confirmed external observations). "
                "This stack provides tooling for both: web crawlers "
                "and document parsers capture direct observations, "
                "while search engines enable corroboration against "
                "existing knowledge bases."
            ),
            "verification": (
                "Pipeline output is verified by: (1) confirming "
                "extracted data matches source documents (Docling "
                "accuracy), (2) confirming web-scraped content is "
                "complete and not truncated, (3) confirming search "
                "index recall rate meets threshold."
            ),
            "lineage": (
                "Implements OE-0004 (Observation) and provides the "
                "input layer for the full OE dependency chain: "
                "Observation -> Survey (OE-0005) -> Understanding "
                "(OE-0006) -> Verification (OE-0007)."
            ),
            "assumptions": (
                "Assumes that the majority of engineering observations "
                "can be captured through text, documents, and audio. "
                "Acknowledges that some observations (tactile, "
                "environmental) require specialized sensors beyond "
                "this stack's scope."
            ),
        },
        stack_config={
            "id": "oe-observation-first",
            "name": "OE Observation First -- Data Collection Stack",
            "description": (
                "Multi-modal observation pipeline: web scraping + "
                "document parsing + audio transcription + search "
                "indexing."
            ),
            "version": "1.0.0-oe-rc3",
            "author": "openengineer",
            "tags": [
                "openengineer", "observation-first", "data-pipeline",
                "scraping", "parsing", "search", "local-first",
            ],
            "tools": [
                "crawl4ai", "docling", "markitdown", "whisper",
                "opendataloader", "opendataloader_pdf", "fabric",
                "elasticsearch", "meilisearch", "understand_anything",
            ],
            "endpoints": {
                "elasticsearch": "http://localhost:9200",
                "meilisearch": "http://localhost:7700",
            },
        },
        notes={
            "oe_concept": "observation_first",
            "observation_types": (
                "Direct: web scraping, document parsing, audio "
                "transcription. Corroborated: search index matching "
                "against existing knowledge (OE-0004 taxonomy)."
            ),
        },
    )


def _context_preservation_stack() -> StandardTemplate:
    """Context Preservation -- the complete OE context record stack.

    Maps to OE-0003 (Engineering Context) and OE-0008 (Decisions).
    This is the "full stack" for OE compliance -- all ten conformance
    criteria are supported.
    """
    return StandardTemplate(
        template_id="oe-context-preservation",
        name="OE Context Preservation -- Full Engineering Context Stack",
        version="1.0.0-oe-rc3",
        author="openengineer",
        description=(
            "The complete OE-compliant engineering context preservation "
            "stack. Multi-agent reasoning + structured documentation + "
            "full RAG + vector search + knowledge graph + monitoring. "
            "Satisfies all ten OE-0000 conformance criteria."
        ),
        source_type="native",
        oe_spec_refs=[
            "OE-0000", "OE-0001", "OE-0002", "OE-0003", "OE-0004",
            "OE-0005", "OE-0006", "OE-0007", "OE-0008", "OE-0009",
            "OE-0010", "OE-0011",
        ],
        engineering_context={
            "decision": (
                "Deploy a comprehensive stack that implements every layer "
                "of the Open Engineer specification: multi-agent reasoning "
                "(CrewAI/AutoGen/Agno) for decision analysis, full RAG "
                "pipeline for context retrieval, structured documentation "
                "tools for context record creation, and monitoring for "
                "verification tracking."
            ),
            "observation": (
                "Engineers across all disciplines report that inherited "
                "systems without context records require significantly "
                "more effort to maintain, modify, or extend (RFC-0003). "
                "The 47 retaining wall failure survey (examples/"
                "survey-retaining-wall-failure.md) demonstrated that 71% "
                "of failures involved conditions known at design time but "
                "not accounted for -- a direct context preservation failure."
            ),
            "alternatives": (
                "1. Manual documentation only -- no structured schema, "
                "no conformance checking, fails OE-0000 criterion 1.\n"
                "2. AI-only context generation -- no observation "
                "grounding, violates OE-0004 observation-first.\n"
                "3. Issue tracker only -- captures tasks but not "
                "reasoning, alternatives, or constraints.\n"
                "4. Wiki + git notes -- better than nothing but no "
                "schema enforcement, no conformance validation."
            ),
            "constraints": (
                "Must satisfy all ten OE-0000 conformance criteria. "
                "Must preserve the OE-0003 nine required fields. Must "
                "support both creation (stewardship) and retrieval "
                "(inheritance) of context records. Must support the "
                "amendment workflow (OE-0011)."
            ),
            "reasoning": (
                "The stack maps to the full OE dependency chain: "
                "Observation (data tools) -> Survey (RAG aggregation) -> "
                "Understanding (multi-agent analysis) -> Verification "
                "(monitoring + testing) -> Decision (structured record) -> "
                "Stewardship (documentation) -> Inheritance (knowledge "
                "graph + RAG retrieval). Each layer of the AI-LSC 10-layer "
                "architecture provides tooling for the corresponding OE "
                "specification layer."
            ),
            "verification": (
                "Verified against OE-0000's ten conformance criteria: "
                "(1) field completeness via schema validation, "
                "(2) decision specificity via template constraints, "
                "(3) observation traceability via source references, "
                "(4) constraint bounding via required constraints field, "
                "(5) alternatives plural via required alternatives field, "
                "(6) verification against reality via monitoring tools, "
                "(7) reasoning references alternatives via template "
                "structure, (8) lineage traceability via OE spec refs, "
                "(9) assumption awareness via required field, "
                "(10) no contradiction via validator."
            ),
            "lineage": (
                "Implements the complete OE-0000 through OE-0011 "
                "specification chain. Every OE document is represented. "
                "The template itself is an OE amendment (OE-0011) that "
                "extends the standard into the AI tooling domain."
            ),
            "assumptions": (
                "Assumes that the OE specification's ten conformance "
                "criteria provide sufficient coverage for context record "
                "quality. Assumes that AI-assisted context extraction "
                "can reduce (but not eliminate) the manual effort of "
                "creating compliant context records. Acknowledges OE-0003's "
                "known limitation regarding tacit knowledge."
            ),
        },
        stack_config={
            "id": "oe-context-preservation",
            "name": "OE Context Preservation -- Full Engineering Context Stack",
            "description": (
                "Complete OE-compliant context preservation: multi-agent "
                "reasoning + full RAG + knowledge graph + structured "
                "documentation + monitoring. 25+ tools."
            ),
            "version": "1.0.0-oe-rc3",
            "author": "openengineer",
            "tags": [
                "openengineer", "context-preservation", "full-stack",
                "multi-agent", "rag", "knowledge-graph", "local-first",
            ],
            "tools": [
                "ollama", "vllm", "litellm", "qdrant", "chromadb",
                "redis", "mariadb", "elasticsearch", "meilisearch",
                "crewai", "autogen", "agno", "langchain",
                "aider", "fabric", "docling", "markitdown", "whisper",
                "openwebui", "glances", "prometheus", "grafana",
                "opik", "crawl4ai", "opendataloader", "graphrag",
            ],
            "endpoints": {
                "ollama": "http://localhost:11434/v1",
                "vllm": "http://localhost:8000",
                "litellm": "http://localhost:4000",
                "qdrant": "http://localhost:6333",
                "chromadb": "http://localhost:8000",
                "redis": "localhost:6379",
                "mariadb": "localhost:3306",
                "elasticsearch": "http://localhost:9200",
                "meilisearch": "http://localhost:7700",
                "openwebui": "http://localhost:8080",
                "glances": "http://localhost:61208",
                "prometheus": "http://localhost:9090",
                "grafana": "http://localhost:3000",
                "opik": "http://localhost:3000",
            },
        },
        notes={
            "oe_concept": "context_preservation",
            "conformance_coverage": (
                "This template satisfies all 10 OE-0000 conformance "
                "criteria. The conformance_score for the built-in "
                "engineering_context is 100%."
            ),
            "setup_order": [
                "Tier 1 (infrastructure): redis, mariadb, elasticsearch",
                "Tier 2 (memory): qdrant, chromadb, meilisearch",
                "Tier 3 (inference): ollama, vllm, litellm",
                "Tier 4 (data tools): docling, markitdown, whisper, crawl4ai, opendataloader",
                "Tier 5 (agents): crewai, autogen, agno, langchain",
                "Tier 6 (coding): aider, fabric",
                "Tier 7 (monitoring): glances, prometheus, grafana, opik",
                "Tier 8 (interface): openwebui",
            ],
            "memory_hierarchy": (
                "5-tier: Redis (hot, ms) -> Qdrant (semantic, us) -> "
                "ChromaDB (documents) -> Elasticsearch (full-text) -> "
                "Meilisearch (typo-tolerant instant) -> MariaDB (persistent)"
            ),
        },
    )


def _engineering_decisions_stack() -> StandardTemplate:
    """Engineering Decisions -- the structured decision-making stack.

    Maps to OE-0008 (Decisions) and the decision-as-context-record concept.
    Focused on AI-assisted engineering decision analysis and recording.
    """
    return StandardTemplate(
        template_id="oe-engineering-decisions",
        name="OE Engineering Decisions -- Structured Decision Stack",
        version="1.0.0-oe-rc3",
        author="openengineer",
        description=(
            "Structure and analyze engineering decisions with AI "
            "assistance. Multi-agent collaboration (CrewAI) + code "
            "review (Aider) + pair programming (Aider) + document "
            "generation (Fabric) produce OE-0003 compliant context "
            "records for every significant decision."
        ),
        source_type="native",
        oe_spec_refs=["OE-0003", "OE-0007", "OE-0008"],
        engineering_context={
            "decision": (
                "Deploy a decision engineering stack with CrewAI "
                "(multi-agent analysis), Aider (code review + pair "
                "programming), Fabric (document transformation), "
                "and Ollama (local LLM reasoning) to produce structured "
                "engineering context records that satisfy OE-0003."
            ),
            "observation": (
                "The software architecture migration example "
                "(examples/software-architecture-migration.md) shows "
                "that without context records, a future developer "
                "cannot reconstruct why Python was ever used when the "
                "system was rewritten in Rust. The biomedical implant "
                "example (examples/biomedical-implant-context.md) shows "
                "that cross-discipline constraints are the most commonly "
                "lost context."
            ),
            "alternatives": (
                "1. ADR (Architecture Decision Record) files only -- "
                "no AI assistance, no conformance checking, manual "
                "maintenance.\n"
                "2. Issue tracker decisions -- no structured format, "
                "no alternatives/constraints documentation.\n"
                "3. Unstructured meeting notes -- no reproducibility, "
                "no verification, fails OE-0000 criterion 6."
            ),
            "constraints": (
                "Every decision must produce a context record with all "
                "nine OE-0003 required fields. Must support multi-agent "
                "analysis (researcher + reviewer + recorder roles). "
                "Must verify reasoning against alternatives (OE-0000 "
                "criterion 7)."
            ),
            "reasoning": (
                "CrewAI provides role-based agent teams that mirror "
                "the OE decision process: a Researcher agent gathers "
                "observations (OE-0004), a Reviewer agent verifies "
                "reasoning (OE-0007), and a Recorder agent structures "
                "the output as an OE-0003 compliant context record. "
                "Aider provides code-level decision context, and Fabric "
                "transforms the output into documentation."
            ),
            "verification": (
                "Each generated context record is validated against "
                "the ten OE-0000 conformance criteria. The "
                "decision_specificity criterion (criterion 2) ensures "
                "each record identifies exactly one choice. The "
                "alternatives_plural criterion (criterion 5) ensures "
                "at least one rejected alternative is documented."
            ),
            "lineage": (
                "Implements OE-0008 (Decisions) and depends on OE-0003 "
                "(Engineering Context) for the record structure. "
                "The 20 examples across 9 disciplines demonstrate "
                "context record patterns this stack should produce."
            ),
            "assumptions": (
                "Assumes that local LLMs (32B+ parameters) provide "
                "sufficient reasoning quality for decision analysis. "
                "Assumes that the OE-0003 nine-field structure captures "
                "the essential context for most engineering decisions."
            ),
        },
        stack_config={
            "id": "oe-engineering-decisions",
            "name": "OE Engineering Decisions -- Structured Decision Stack",
            "description": (
                "AI-assisted engineering decision analysis with "
                "multi-agent collaboration and OE-0003 compliant "
                "context record generation."
            ),
            "version": "1.0.0-oe-rc3",
            "author": "openengineer",
            "tags": [
                "openengineer", "decisions", "multi-agent",
                "code-review", "documentation", "local-first",
            ],
            "tools": [
                "ollama", "litellm", "crewai", "autogen", "agno",
                "aider", "fabric", "chromadb", "ripgrep", "fd",
                "tree_sitter",
            ],
            "endpoints": {
                "ollama": "http://localhost:11434/v1",
                "litellm": "http://localhost:4000",
                "chromadb": "http://localhost:8000",
            },
        },
        notes={
            "oe_concept": "engineering_decisions",
            "agent_roles": (
                "Researcher: gathers observations (OE-0004). "
                "Reviewer: verifies reasoning (OE-0007). "
                "Recorder: produces OE-0003 context record. "
                "Critic: checks conformance (OE-0000)."
            ),
            "decision_record_template": (
                "Each decision produces: Decision (what), Observation "
                "(why now), Alternatives (what else), Constraints "
                "(what bounded), Reasoning (why this), Verification "
                "(how confirmed), Lineage (what prior work), "
                "Assumptions (what's unknown)."
            ),
        },
    )