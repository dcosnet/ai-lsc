#!/usr/bin/env python3
"""
DCOS.net AI-LSC Codebase Reorganization & 10-Layer Migration Utility
Author: Jeremy Anderson
Domain: dcos.net
Contact: info@dcos.net
License: CC-BY-SA 4.0 International

This script programmatically upgrades the entire ai_lsc codebase to be
10-layer compliant. It reorganizes layer order, updates the category map,
and ensures that all stack wiring loops dynamically look up layer metadata.
"""

import os
import re
from pathlib import Path

# ── 1. Reorganized 10-Layer Taxonomy ───────────────────────────────────────
NEW_LAYERS = [
    "Host Platform & Infrastructure",
    "Development Runtime & Environment",
    "GPU Acceleration & Optimization",
    "Local Inference Engines",
    "Intelligent API Routers & Proxies",
    "Multi-Agent Orchestration Runtimes",
    "Agentic Software Engineering & Sandboxes",
    "Decentralized Knowledge & Vector Stores",
    "Data Extraction & Pipeline Harvest",
    "Human Interface & System Operations"
]

# ── 2. Reorganized CATEGORY_MAP ─────────────────────────────────────────────
NEW_CATEGORY_MAP = {
    "Agent Daemon": {"layer": "Multi-Agent Orchestration Runtimes", "level": 6, "role": "Agent Daemon"},
    "Agent Shell": {"layer": "Multi-Agent Orchestration Runtimes", "level": 6, "role": "Agent Shell"},
    "Agentless Deployment": {"layer": "Human Interface & System Operations", "level": 10, "role": "Agentless Deployment"},
    "Alloy Telemetry": {"layer": "Human Interface & System Operations", "level": 10, "role": "Alloy Telemetry"},
    "Analytical Database": {"layer": "Host Platform & Infrastructure", "level": 1, "role": "Analytical Database"},
    "Audio Extraction": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "Audio Extraction"},
    "Auto Recovery Daemon": {"layer": "Human Interface & System Operations", "level": 10, "role": "Auto Recovery Daemon"},
    "CI/CD Orchestration": {"layer": "Agentic Software Engineering & Sandboxes", "level": 7, "role": "CI/CD Orchestration"},
    "CLI Pair Programmer": {"layer": "Agentic Software Engineering & Sandboxes", "level": 7, "role": "CLI Pair Programmer"},
    "Cache": {"layer": "Host Platform & Infrastructure", "level": 1, "role": "Cache"},
    "Cloud Dev Kit": {"layer": "Human Interface & System Operations", "level": 10, "role": "Cloud Dev Kit"},
    "Cluster Homepage": {"layer": "Human Interface & System Operations", "level": 10, "role": "Cluster Homepage"},
    "Code Refactoring": {"layer": "Agentic Software Engineering & Sandboxes", "level": 7, "role": "Code Refactoring"},
    "Codex Developer": {"layer": "Agentic Software Engineering & Sandboxes", "level": 7, "role": "Codex Developer"},
    "Collaborative Chat": {"layer": "Human Interface & System Operations", "level": 10, "role": "Collaborative Chat"},
    "Context Integrity Core": {"layer": "Agentic Software Engineering & Sandboxes", "level": 7, "role": "Context Integrity Core"},
    "Coordination Protocol": {"layer": "Multi-Agent Orchestration Runtimes", "level": 6, "role": "Coordination Protocol"},
    "Curation Pipeline": {"layer": "Intelligent API Routers & Proxies", "level": 5, "role": "Curation Pipeline"},
    "Data Ingest": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "Data Ingest"},
    "Database": {"layer": "Host Platform & Infrastructure", "level": 1, "role": "Database"},
    "Datacenter Inference": {"layer": "Local Inference Engines", "level": 4, "role": "Datacenter Inference"},
    "Desktop Agent Core": {"layer": "Multi-Agent Orchestration Runtimes", "level": 6, "role": "Desktop Agent Core"},
    "Desktop GUI": {"layer": "Human Interface & System Operations", "level": 10, "role": "Desktop GUI"},
    "Distributed Search": {"layer": "Decentralized Knowledge & Vector Stores", "level": 8, "role": "Distributed Search"},
    "Document Archiver": {"layer": "Human Interface & System Operations", "level": 10, "role": "Document Archiver"},
    "Document Comprehension": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "Document Comprehension"},
    "Document Parser": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "Document Parser"},
    "ETL Transformation": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "ETL Transformation"},
    "Ecosystem Launcher": {"layer": "Human Interface & System Operations", "level": 10, "role": "Ecosystem Launcher"},
    "Enterprise Assistant": {"layer": "Human Interface & System Operations", "level": 10, "role": "Enterprise Assistant"},
    "Extensible Interface": {"layer": "Human Interface & System Operations", "level": 10, "role": "Extensible Interface"},
    "File Discovery": {"layer": "Development Runtime & Environment", "level": 2, "role": "File Discovery"},
    "GGUF Runtime": {"layer": "Local Inference Engines", "level": 4, "role": "GGUF Runtime"},
    "GPU Computing": {"layer": "GPU Acceleration & Optimization", "level": 3, "role": "GPU Computing"},
    "Gap Analyzer": {"layer": "Human Interface & System Operations", "level": 10, "role": "Gap Analyzer"},
    "Graph Database": {"layer": "Decentralized Knowledge & Vector Stores", "level": 8, "role": "Graph Database"},
    "Hardware Acceleration": {"layer": "GPU Acceleration & Optimization", "level": 3, "role": "Hardware Acceleration"},
    "High-Performance Vector": {"layer": "Decentralized Knowledge & Vector Stores", "level": 8, "role": "High-Performance Vector"},
    "IaC DRY Wrapper": {"layer": "Human Interface & System Operations", "level": 10, "role": "IaC DRY Wrapper"},
    "Image WebUI": {"layer": "Human Interface & System Operations", "level": 10, "role": "Image WebUI"},
    "Infrastructure Provision": {"layer": "Human Interface & System Operations", "level": 10, "role": "Infrastructure Provision"},
    "Infrastructure as Code": {"layer": "Development Runtime & Environment", "level": 2, "role": "Infrastructure as Code"},
    "Integration Library": {"layer": "Multi-Agent Orchestration Runtimes", "level": 6, "role": "Integration Library"},
    "Isolation": {"layer": "Host Platform & Infrastructure", "level": 1, "role": "Isolation"},
    "LLM Observability": {"layer": "Human Interface & System Operations", "level": 10, "role": "LLM Observability"},
    "Layer-wise Inference": {"layer": "Local Inference Engines", "level": 4, "role": "Layer-wise Inference"},
    "Learning Cards": {"layer": "Human Interface & System Operations", "level": 10, "role": "Learning Cards"},
    "Lexical Search": {"layer": "Decentralized Knowledge & Vector Stores", "level": 8, "role": "Lexical Search"},
    "Library Manager": {"layer": "Human Interface & System Operations", "level": 10, "role": "Library Manager"},
    "Load Balancer": {"layer": "Intelligent API Routers & Proxies", "level": 5, "role": "Load Balancer"},
    "Local Central Shell": {"layer": "Human Interface & System Operations", "level": 10, "role": "Local Central Shell"},
    "Local Declarative DSL": {"layer": "Human Interface & System Operations", "level": 10, "role": "Local Declarative DSL"},
    "Local LLM Runner": {"layer": "Local Inference Engines", "level": 4, "role": "Local LLM Runner"},
    "Markdown Converter": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "Markdown Converter"},
    "Metal Provisioner": {"layer": "Human Interface & System Operations", "level": 10, "role": "Metal Provisioner"},
    "Metric Scraper": {"layer": "Human Interface & System Operations", "level": 10, "role": "Metric Scraper"},
    "Mixed Precision": {"layer": "GPU Acceleration & Optimization", "level": 3, "role": "Mixed Precision"},
    "Model Curation": {"layer": "Local Inference Engines", "level": 4, "role": "Model Curation"},
    "Model Manager GUI": {"layer": "Human Interface & System Operations", "level": 10, "role": "Model Manager GUI"},
    "Model Optimization": {"layer": "GPU Acceleration & Optimization", "level": 3, "role": "Model Optimization"},
    "Model Surgery": {"layer": "Local Inference Engines", "level": 4, "role": "Model Surgery"},
    "Multi-Agent Framework": {"layer": "Multi-Agent Orchestration Runtimes", "level": 6, "role": "Multi-Agent Framework"},
    "Native Inference": {"layer": "Local Inference Engines", "level": 4, "role": "Native Inference"},
    "Offline Journal": {"layer": "Human Interface & System Operations", "level": 10, "role": "Offline Journal"},
    "Open-Source IaC": {"layer": "Human Interface & System Operations", "level": 10, "role": "Open-Source IaC"},
    "Outliner Graph": {"layer": "Human Interface & System Operations", "level": 10, "role": "Outliner Graph"},
    "Output Evaluator": {"layer": "Human Interface & System Operations", "level": 10, "role": "Output Evaluator"},
    "PDF Processing": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "PDF Processing"},
    "Parsing Engine": {"layer": "Development Runtime & Environment", "level": 2, "role": "Parsing Engine"},
    "Performance Engine": {"layer": "Local Inference Engines", "level": 4, "role": "Performance Engine"},
    "Platform Workspace": {"layer": "Human Interface & System Operations", "level": 10, "role": "Platform Workspace"},
    "Production Multi-Agent": {"layer": "Multi-Agent Orchestration Runtimes", "level": 6, "role": "Production Multi-Agent"},
    "Programmable IaC": {"layer": "Human Interface & System Operations", "level": 10, "role": "Programmable IaC"},
    "Prompt Tester": {"layer": "Agentic Software Engineering & Sandboxes", "level": 7, "role": "Prompt Tester"},
    "RAG Flow Canvas": {"layer": "Human Interface & System Operations", "level": 10, "role": "RAG Flow Canvas"},
    "Reference Manager": {"layer": "Human Interface & System Operations", "level": 10, "role": "Reference Manager"},
    "Requirement Builder": {"layer": "Agentic Software Engineering & Sandboxes", "level": 7, "role": "Requirement Builder"},
    "Role-Playing Agent": {"layer": "Multi-Agent Orchestration Runtimes", "level": 6, "role": "Role-Playing Agent"},
    "Runtime Environment": {"layer": "Development Runtime & Environment", "level": 2, "role": "Runtime Environment"},
    "Runtime Packaging": {"layer": "Host Platform & Infrastructure", "level": 1, "role": "Runtime Packaging"},
    "Serverless Database": {"layer": "Decentralized Knowledge & Vector Stores", "level": 8, "role": "Serverless Database"},
    "Single-File Runtime": {"layer": "Local Inference Engines", "level": 4, "role": "Single-File Runtime"},
    "Skill Auditor": {"layer": "Agentic Software Engineering & Sandboxes", "level": 7, "role": "Skill Auditor"},
    "Sovereign Graph Editor": {"layer": "Human Interface & System Operations", "level": 10, "role": "Sovereign Graph Editor"},
    "Sovereign Software Agent": {"layer": "Agentic Software Engineering & Sandboxes", "level": 7, "role": "Sovereign Software Agent"},
    "Speech Transcriber": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "Speech Transcriber"},
    "Sprint Planner": {"layer": "Human Interface & System Operations", "level": 10, "role": "Sprint Planner"},
    "Sprints Manager": {"layer": "Human Interface & System Operations", "level": 10, "role": "Sprints Manager"},
    "Stateless Orchestration": {"layer": "Multi-Agent Orchestration Runtimes", "level": 6, "role": "Stateless Orchestration"},
    "Structured Synthesis": {"layer": "Decentralized Knowledge & Vector Stores", "level": 8, "role": "Structured Synthesis"},
    "Studio Canvas": {"layer": "Human Interface & System Operations", "level": 10, "role": "Studio Canvas"},
    "Synchronization Layer": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "Synchronization Layer"},
    "System Auditor": {"layer": "Human Interface & System Operations", "level": 10, "role": "System Auditor"},
    "System Console": {"layer": "Human Interface & System Operations", "level": 10, "role": "System Console"},
    "Telemetry Monitor": {"layer": "Human Interface & System Operations", "level": 10, "role": "Telemetry Monitor"},
    "Telemetry Visualizer": {"layer": "Human Interface & System Operations", "level": 10, "role": "Telemetry Visualizer"},
    "Terminal Agent": {"layer": "Multi-Agent Orchestration Runtimes", "level": 6, "role": "Terminal Agent"},
    "Terminal Coding Agent": {"layer": "Agentic Software Engineering & Sandboxes", "level": 7, "role": "Terminal Coding Agent"},
    "Text Search": {"layer": "Development Runtime & Environment", "level": 2, "role": "Text Search"},
    "Unified API Gateway": {"layer": "Intelligent API Routers & Proxies", "level": 5, "role": "Unified API Gateway"},
    "Vector Engine": {"layer": "Decentralized Knowledge & Vector Stores", "level": 8, "role": "Vector Engine"},
    "Vision describer": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "Vision describer"},
    "Visual Agent Canvas": {"layer": "Human Interface & System Operations", "level": 10, "role": "Visual Agent Canvas"},
    "Voice Synthesis": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "Voice Synthesis"},
    "Web Scraper": {"layer": "Data Extraction & Pipeline Harvest", "level": 9, "role": "Web Scraper"},
}

def migrate_constants(path: Path):
    if not path.exists():
        print(f"[-] constants.py not found at {path}")
        return
    content = path.read_text(encoding="utf-8")
    
    # Locate NAV_LAYER_ORDER array
    nav_pattern = re.compile(r'NAV_LAYER_ORDER:\s*list\[str\]\s*=\s*\[[^\]]+\]', re.DOTALL)
    new_nav_str = "NAV_LAYER_ORDER: list[str] = [\n" + "".join(f'    "{l}",\n' for l in NEW_LAYERS) + "]"
    
    if nav_pattern.search(content):
        content = nav_pattern.sub(new_nav_str, content)
        path.write_text(content, encoding="utf-8")
        print(f"[+] Migrated constants.py layers!")
    else:
        print(f"[-] NAV_LAYER_ORDER block not matched in constants.py")

def migrate_db_manager(path: Path):
    if not path.exists():
        print(f"[-] db_manager.py not found at {path}")
        return
    content = path.read_text(encoding="utf-8")
    
    # Locate CATEGORY_MAP dict block
    map_pattern = re.compile(r'CATEGORY_MAP:\s*dict\[str,\s*dict\[str,\s*object\]\]\s*=\s*\{[^}]+(\}[^}]*)*\}', re.DOTALL)
    
    # Format CATEGORY_MAP dict
    new_map_str = "CATEGORY_MAP: dict[str, dict[str, object]] = {\n"
    for cat in sorted(NEW_CATEGORY_MAP.keys()):
        val = NEW_CATEGORY_MAP[cat]
        new_map_str += f'    "{cat}": ' + "{" + f'"layer": "{val["layer"]}", "level": {val["level"]}, "role": "{val["role"]}"' + "},\n"
    new_map_str += "}"
    
    if map_pattern.search(content):
        content = map_pattern.sub(new_map_str, content)
        path.write_text(content, encoding="utf-8")
        print(f"[+] Migrated db_manager.py CATEGORY_MAP!")
    else:
        print(f"[-] CATEGORY_MAP block not matched in db_manager.py")

def migrate_connections(path: Path, defaults_path: Path):
    if not path.exists():
        print(f"[-] connections.py not found at {path}")
        return
    if not defaults_path.exists():
        print(f"[-] defaults.py not found at {defaults_path} - cannot resolve dynamic tool layers")
        return
        
    # Dynamically read tool_id -> layer from defaults.py
    sys.path.insert(0, str(defaults_path.parent))
    import defaults
    tool_to_layer = {}
    for tid, tool in defaults.DEFAULT_REGISTRY.items():
        tool_to_layer[tid] = tool["layer"]
        
    content = path.read_text(encoding="utf-8")
    
    # Add DEFAULT_REGISTRY import to connections.py if missing
    import_line = "from ai_lsc.registry.defaults import DEFAULT_REGISTRY"
    if "import DEFAULT_REGISTRY" not in content and import_line not in content:
        # Insert after absolute imports
        content = "from ai_lsc.registry.defaults import DEFAULT_REGISTRY\n" + content
        print("[+] Added DEFAULT_REGISTRY import to connections.py")

    # Reorganize the StackWiring layer arguments in connections.py
    blocks = content.split("_reg(StackWiring(")
    new_blocks = [blocks[0]]
    updated_count = 0
    
    for block in blocks[1:]:
        tid_match = re.search(r"""tool_id\s*=\s*["']?([a-zA-Z0-9_-]+)["']?""", block)
        if tid_match:
            tid = tid_match.group(1)
            if tid in tool_to_layer:
                new_layer = tool_to_layer[tid]
                # Replace layer="..." or layer='...'
                block, count = re.subn(r"""layer\s*=\s*["|'][^"'\s]+["|']""", f'layer="{new_layer}"', block)
                if count:
                    updated_count += 1
        new_blocks.append(block)
        
    content = "_reg(StackWiring(".join(new_blocks)
    
    # Convert hardcoded loops to look up the layer from the registry dynamically
    # Example: layer="DevOps" inside loops -> layer=DEFAULT_REGISTRY[_tid]["layer"]
    content, loops_updated = re.subn(
        r"""layer\s*=\s*["'](?:DevOps|User Interfaces|Knowledge Management|Orchestrators|Host Platform|Development Environment|GPU Runtimes|Engines|Routing|Security|Observability)["']""",
        'layer=DEFAULT_REGISTRY[_tid]["layer"]',
        content
    )
    if loops_updated:
        print(f"[+] Converted {loops_updated} loop-based StackWiring layers to dynamic lookups!")
        
    path.write_text(content, encoding="utf-8")
    print(f"[+] Migrated connections.py! Rebuilt {updated_count} static tool-layer definitions.")

def migrate_layers(layers_dir: Path, defaults_path: Path):
    if not layers_dir.is_dir():
        print(f"[-] Layers directory not found at {layers_dir}")
        return
    if not defaults_path.exists():
        print(f"[-] defaults.py not found - cannot update layer files")
        return
        
    import defaults
    tool_to_layer = {}
    tool_to_level = {}
    for tid, tool in defaults.DEFAULT_REGISTRY.items():
        tool_to_layer[tid] = tool["layer"]
        tool_to_level[tid] = tool["level"]
        
    updated_files = 0
    for path in layers_dir.glob("*.py"):
        if path.name == "__init__.py":
            continue
        original = path.read_text(encoding="utf-8")
        content = original
        
        # Replace level and layer for each tool inside the file
        for tid in tool_to_layer:
            # Look for block: 'tool_id': { or "tool_id": {
            # we do a specific match and replace within that dict
            tool_pattern = re.compile(rf"""["']{tid}["']\s*:\s*\{{[^}}]+}}""", re.DOTALL)
            match = tool_pattern.search(content)
            if match:
                block = match.group(0)
                # Replace level
                block = re.sub(r'"level":\s*\d+', f'"level": {tool_to_level[tid]}', block)
                # Replace layer
                block = re.sub(r""""layer":\s*["|'][^"'\s]+["|']""", f'"layer": "{tool_to_layer[tid]}"', block)
                content = content.replace(match.group(0), block)
                
        if content != original:
            path.write_text(content, encoding="utf-8")
            print(f"[+] Realigned tool layers & levels inside modular layer file: {path.name}")
            updated_files += 1
            
    print(f"[+] Layer files update complete. Modified {updated_files} layer modules.")

def main():
    import sys
    root = Path(__file__).resolve().parent
    src_dir = root / "src"
    
    # Setup paths relative to root or src
    constants_path = src_dir / "ai_lsc" / "constants.py"
    db_manager_path = src_dir / "ai_lsc" / "ui" / "pages" / "db_manager.py"
    connections_path = src_dir / "ai_lsc" / "stack" / "connections.py"
    defaults_path = src_dir / "ai_lsc" / "registry" / "defaults.py"
    layers_dir = src_dir / "ai_lsc" / "registry" / "layers"
    
    print("[*] Starting taxonomy migration sweeps...")
    migrate_constants(constants_path)
    migrate_db_manager(db_manager_path)
    migrate_connections(connections_path, defaults_path)
    migrate_layers(layers_dir, defaults_path)
    print("[+] Entire codebase has been successfully upgraded to the 10-Layer Architecture!")

if __name__ == "__main__":
    main()
