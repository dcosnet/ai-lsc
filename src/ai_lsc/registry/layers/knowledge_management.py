"""Registry entries for the Knowledge Management layer (L11).

Contains vector stores, graph databases, search engines, document parsers,
data pipelines, memory systems, and knowledge management tools.

This module is consumed by
:mod:`ai_lsc.registry.loader`.

Structural fields (layer, level) follow the 10-Layer Systems
Architecture Taxonomy; tools may be regrouped across files in a
future pass — the loader merges by tool, not by filename.
"""

TOOLS: dict[str, dict] = {
    'zotero': {
    "name": "Zotero",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Reference Manager',
    "category": 'Reference Manager',
    "installer": {
        "type": "pacman",
        "pkg": "zotero"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "zotero",
        "default_port": None
    },
    "deps": [],
    "description": "Free reference management for researchers.",
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'calibre': {
    "name": "Calibre",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Library Manager',
    "category": 'Library Manager',
    "installer": {
        "type": "pacman",
        "pkg": "calibre"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "calibre",
        "default_port": None
    },
    "deps": [],
    "description": "E-book library management and converter.",
    "license": 'GPL-3.0',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'paperlessngx': {
    "name": "Paperless-ngx",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Document Archiver',
    "category": 'Document Archiver',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/paperless-ngx/paperless-ngx"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/paperlessngx && python3 manage.py runserver 0.0.0.0:{port}",
        "default_port": 8000
    },
    "deps": [
        "postgresql",
        "redis"
    ],
    "description": "Document management system with OCR.",
    "license": 'GPL-3.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'logseq': {
    "name": "Logseq",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Outliner Graph',
    "category": 'Outliner Graph',
    "installer": {
        "type": "npm",
        "pkg": "logseq"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "logseq",
        "default_port": None
    },
    "deps": [],
    "description": "Privacy-first knowledge graph outliner.",
    "license": 'AGPL-3.0',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'joplin': {
    "name": "Joplin",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Offline Journal',
    "category": 'Offline Journal',
    "installer": {
        "type": "pacman",
        "pkg": "joplin"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "joplin",
        "default_port": None
    },
    "deps": [],
    "description": "Open-source note taking and to-do application.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": True,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'chromadb': {
    "name": "ChromaDB",
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Vector Engine',
    "category": 'Vector Engine',
    "installer": {
        "type": "uv",
        "pkg": "chromadb"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "chroma run --path {models_root}/chroma --port {port}",
        "default_port": 8000
    },
    "deps": [],
    "description": "AI-native open-source vector database.",
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": False,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'lancedb': {
    "name": "LanceDB",
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Serverless Database',
    "category": 'Serverless Database',
    "installer": {
        "type": "uv",
        "pkg": "lancedb"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "python3 -m lancedb serve --port {port}",
        "default_port": 8484
    },
    "deps": [],
    "description": "Serverless vector database for AI applications.",
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'qdrant': {
    "name": "Qdrant",
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'High-Performance Vector',
    "category": 'High-Performance Vector',
    "installer": {
        "type": "script",
        "cmd": "curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-musl.tar.gz | tar xz -C {tools_root}/qdrant && chmod +x {tools_root}/qdrant/qdrant",
        "pkg": "https://github.com/qdrant/qdrant"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "./qdrant --storage-path {models_root}/qdrant --host 127.0.0.1 --port {port}",
        "default_port": 6333
    },
    "deps": [],
    "description": "High-performance vector database with mmap storage, payload filtering, and multi-vector support.",
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    },
    "filesystem": {
        "install": "tools/qdrant",
        "data": "data/qdrant",
        "logs": "logs/qdrant"
    }
},
    'neo4j': {
    "name": "Neo4j",
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Graph Database',
    "category": 'Graph Database',
    "installer": {
        "type": "pacman",
        "pkg": "neo4j"
    },
    "launcher": {
        "type": "systemd",
        "cmd": "neo4j",
        "default_port": 7474
    },
    "deps": [],
    "description": "Native graph database and knowledge graph engine.",
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'elasticsearch': {
    "name": "Elasticsearch",
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Distributed Search',
    "category": 'Distributed Search',
    "installer": {
        "type": "pacman",
        "pkg": "elasticsearch"
    },
    "launcher": {
        "type": "systemd",
        "cmd": "elasticsearch",
        "default_port": 9200
    },
    "deps": [],
    "description": "Distributed search and analytics engine.",
    "license": 'Apache-2.0',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'meilisearch': {
    "name": "Meilisearch",
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Lexical Search',
    "category": 'Lexical Search',
    "installer": {
        "type": "script",
        "cmd": "mkdir -p {tools_root}/bin && cd {tools_root}/bin && curl -L https://install.meilisearch.com | sh",
        "pkg": "https://github.com/meilisearch/meilisearch"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "meilisearch --port {port}",
        "default_port": 7700
    },
    "deps": [],
    "description": "Fast, relevant, and typo-tolerant search engine.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'graphrag': {
    "name": "GraphRAG",
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Structured Synthesis',
    "category": 'Structured Synthesis',
    "installer": {
        "type": "uv",
        "pkg": "graphrag"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 -m graphrag init",
        "default_port": None
    },
    "deps": [],
    "description": "Microsoft GraphRAG for knowledge graph construction.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'turbovec': {
    "name": "TurboVec",
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Embedding',
    "category": 'Vector Engine',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/ryancodrai/turbovec"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/turbovec && python3 serve.py --port {port}",
        "default_port": 8101
    },
    "deps": [
        "cuda"
    ],
    "description": "High-speed embedding generation and vector engine.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'airweave': {
    "name": "Airweave",
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Synchronization Layer',
    "category": 'Synchronization Layer',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/airweave-ai/airweave"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/airweave && python3 -m airweave serve --port {port}",
        "default_port": 8600
    },
    "deps": [],
    "description": "Real-time data synchronization and integration layer.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'crawl4ai': {
    "name": "Crawl4AI",
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Web Scraper',
    "category": 'Web Scraper',
    "installer": {
        "type": "uv",
        "pkg": "crawl4ai"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "crawl4ai https://example.com",
        "default_port": None
    },
    "deps": [],
    "description": "LLM-friendly web crawler and data extractor.",
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'docling': {
    "name": "Docling",
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Document Parser',
    "category": 'Document Parser',
    "installer": {
        "type": "uv",
        "pkg": "docling"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "docling",
        "default_port": None
    },
    "deps": [],
    "description": "Advanced document parsing and chunking.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'markitdown': {
    "name": "MarkItDown",
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Markdown Converter',
    "category": 'Markdown Converter',
    "installer": {
        "type": "uv",
        "pkg": "markitdown"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "markitdown document.pdf",
        "default_port": None
    },
    "deps": [],
    "description": "Microsoft tool to convert files to Markdown.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'opendataloader': {
    "name": "OpenDataLoader",
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Data Ingest',
    "category": 'Data Ingest',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/opendataloader-project/opendataloader-pdf"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 -m opendataloader --help",
        "default_port": None
    },
    "deps": [],
    "description": "Universal data loading and preprocessing pipeline.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'whisper': {
    "name": "Whisper",
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Audio Extraction',
    "category": 'Audio Extraction',
    "installer": {
        "type": "uv",
        "pkg": "openai-whisper"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "whisper",
        "default_port": None
    },
    "deps": [],
    "description": "Robust Speech Recognition via Large-Scale Weak Supervision.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'mnemosyne': {
    "name": "Mnemosyne",
    "level": 10,
    "layer": 'Human Interface & System Operations',
    "role": 'Learning Cards',
    "category": 'Learning Cards',
    "installer": {
        "type": "pipx",
        "pkg": "mnemosyne"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "mnemosyne",
        "default_port": None
    },
    "deps": [],
    "description": "Spaced repetition flashcard program with AI integration.",
    "license": 'MIT',
    "flags": {
        "has_cli": False,
        "has_gui": True,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'mnemo_cortex': {
    "name": "Mnemo Cortex",
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Memory',
    "category": 'Cortex Memory',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/GuyMannDude/mnemo-cortex"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/mnemo_cortex && python3 -m mnemo_cortex serve --port {port}",
        "default_port": 7200
    },
    "deps": [
        "ollama"
    ],
    "description": "Hierarchical cortex memory for AI agents.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'everos_memory': {
    "name": "EverOS Memory",
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Memory',
    "category": 'Persistent Memory',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/EverMind-AI/EverOS"
    },
    "launcher": {
        "type": "tmux",
        "cmd": "cd {tools_root}/everos_memory && python3 -m everos serve --port {port}",
        "default_port": 9200
    },
    "deps": [],
    "description": "Persistent long-term memory system for AI agents.",
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": True,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'mirofish': {
    "name": "Mirofish",
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'ETL Transformation',
    "category": 'ETL Transformation',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/666ghj/MiroFish"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "mirofish --help",
        "default_port": None
    },
    "deps": [],
    "description": "Data transformation and ETL pipeline framework.",
    "license": 'Proprietary',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'opendataloader_pdf': {
    "name": "OpenDataLoader PDF",
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'PDF Processing',
    "category": 'PDF Processing',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/opendataloader-project/opendataloader-pdf"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "opendataloader-pdf extract file.pdf",
        "default_port": None
    },
    "deps": [],
    "description": "Specialized PDF extraction and data loading pipeline.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'understand_anything': {
    "name": "Understand Anything",
    "level": 9,
    "layer": 'Data Extraction & Pipeline Harvest',
    "role": 'Document Comprehension',
    "category": 'Document Comprehension',
    "installer": {
        "type": "git",
        "pkg": "https://github.com/Egonex-AI/Understand-Anything"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "understand-anything analyze file.pdf",
        "default_port": None
    },
    "deps": [
        "ollama"
    ],
    "description": "Universal document understanding and summarization.",
    "license": 'MIT',
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": False,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
    'mem0': {
    "name": "Mem0",
    "level": 8,
    "layer": 'Decentralized Knowledge & Vector Stores',
    "role": 'Memory',
    "category": 'Memory System',
    "installer": {
        "type": "uv",
        "pkg": "mem0ai"
    },
    "launcher": {
        "type": "desktop",
        "cmd": "python3 -c \"import mem0; print('ok')\"",
        "default_port": None
    },
    "deps": [],
    "description": "Memory layer for AI applications and agents — extracts, "
                  "stores, and retrieves long-term user/agent memories across "
                  "sessions, backed by pluggable vector stores.",
    "license": "Apache-2.0",
    "flags": {
        "has_cli": True,
        "has_gui": False,
        "has_web": False,
        "is_ollama": False,
        "is_passive": True,
        "is_mcp": False,
        "is_skills_collection": False
    }
},
}