# Quickstart Guide

Get AI Local Stack Control up and running in under 5 minutes.

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| OS | Arch Linux | Arch Linux / EndeavourOS |
| Python | 3.11 | 3.12+ |
| RAM | 8 GB | 16 GB+ (for LLM inference) |
| Disk | 4 GB free | 20 GB+ (for model storage) |
| GPU | None | NVIDIA (CUDA) or AMD (ROCm) |

## Installation

### Option 1: Bootstrap Script (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/ai-lsc.git
cd ai-lsc

# Run the bootstrap script (installs system + Python deps)
chmod +x bootstrap.sh
./bootstrap.sh

# Launch the application
python -m ai_lsc
```

### Option 2: Manual Install

#### Step 1: System Dependencies

```bash
# Core packages (Arch Linux)
sudo pacman -S python python-pip pyside6 \
 git tmux ripgrep fd tree-sitter sqlite redis

# Optional: GPU support
sudo pacman -S cuda # NVIDIA
# sudo pacman -S rocm-hip-sdk # AMD

# Optional: Container runtimes
sudo pacman -S podman docker
# Optional: LXC support
sudo pacman -S lxc lxcfs
```

#### Step 2: Python Dependencies

```bash
cd ai-lsc

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate

# Install PySide6 and dependencies
pip install PySide6
pip install -e .
```

#### Step 3: Verify Installation

```bash
# Check that the registry loads correctly
python -c "
from ai_lsc import DEFAULT_REGISTRY, validate_registry
errors = validate_registry(DEFAULT_REGISTRY)
print(f'Registry loaded: {len(DEFAULT_REGISTRY)} tools')
print(f'Validation errors: {len(errors)}')
"

# Expected output (v3.1):
# Registry loaded: 125 tools
# Validation errors: 0
```

#### Step 4: Launch

```bash
python -m ai_lsc
```

## First Launch

When you launch AI-LSC for the first time, you will see the **Stack Template Wizard**. This is your entry point for configuring your AI stack.

### Choosing a Template

| Template | Best For | Tool Count |
|----------|----------|-----------|
| Claude Code Setup | Claude Code development workflow | 11 |
| Free Claude Code | Minimal Claude Code environment | 4 |
| Local LLM Lab | Self-hosted LLM experimentation | 10 |
| SaaS Integrations | Production deployment with SSL/CDN | 12 |

### Manual Configuration

If you prefer to build your stack from scratch:

1. Select **Create From Scratch** in the wizard
2. Navigate to the **Infrastructure** section in the sidebar
3. Expand each layer and toggle tools on/off
4. Use the **IPC Stack** tab to validate dependencies
5. Click **Compile** to save your stack configuration

### Watching the Pipeline Ticker

Once you have tools staged, the **Pipeline Ticker** at the top of every tab comes alive. It scrolls horizontally through the wiring topology of your active tools:

- `provider ──interface──▶ consumer` shows the data-flow direction
- Arrow color encodes the interface type (blue = openai_api, green = vector, orange = redis_pubsub, purple = postgresql, teal = http_api)
- Tools with no in-stack wiring are flagged red with an `❗` prefix — these are orphans worth investigating (either they're missing a `STACK_WIRINGS` entry in `stack/connections.py`, or the tools they wire to aren't yet staged)
- Hover over the ticker to pause the scroll
- Click any tool pill to jump to the Tools tab — the matching row is selected, scrolled to center, and flashed amber for 1.5 s

The ticker refreshes automatically on every service-status poll (every 2 s by default) so running-state color changes (stopped → running) propagate immediately.

### Using the Workspace Tab

The **Workspace** nav entry (between Chat and Git Sources) is your peek-style orchestration surface — think virt-manager for your AI stack. After you stage + start tools:

1. Click **Workspace** in the sidebar
2. You'll see one sub-tab per active tool, prefixed with an emoji:
 - 🌐 — web-interface tool (OpenWebUI, Hermes, Odysseus, etc.)
 - ⌨ — CLI tool (Aider, Claude Code, OpenHands, etc.)
 - 📦 — passive / library tool (no interactive surface)
 - ⏸ suffix — tool is staged but not yet running
3. For web tools: the sub-tab embeds the tool's web UI directly via `QWebEngineView` at `http://127.0.0.1:{port}` — no need to leave the app for a browser. A URL bar at the top shows the loaded URL; click ⟳ to reload or ↗ to open in an external browser
4. For CLI tools: the sub-tab embeds the tool's tmux session output, polled at 4 Hz via `tmux capture-pane`. The terminal is read-only — use a real terminal app for interactive input
5. For not-yet-running tools: the sub-tab shows a **Start tool** button that wires back to the existing service-start flow
6. Close a sub-tab with the × button — this stops the polling but does NOT stop the underlying tool (use the Stack Editor for that)

> **Servo note:** Web embedding uses `QWebEngineView` by default. To swap in Mozilla's servo engine later, replace `_make_web_view()` in `src/ai_lsc/ui/widgets/workspace_tab.py` — the rest of the WorkspaceTab code only depends on the `setUrl()` / `url()` / `load()` API.

## Post-Setup

### Installing a Base LLM

Most tools depend on Ollama as the local LLM runtime:

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3
ollama pull codellama # Good for coding assistance
ollama pull mistral # Lightweight general-purpose
```

### Starting Services

After configuring your stack in the IPC Stack tab:

1. Click **Compile** to save the stack configuration
2. Switch to the **Monitor** tab
3. Click **Start All** or start individual services
4. Check service status indicators (green = running)
5. Watch the **Pipeline Ticker** at the top of the screen — pills turn blue as their tools come online
6. Switch to the **Workspace** tab to interact with each running tool in its own sub-tab

### Connecting the Chat Console

Once Ollama is running:

1. Navigate to the **Chat** section
2. Select a model from the dropdown (e.g., `llama3`, `codellama`)
3. Start chatting with your local AI assistant

## Common Tasks

### Adding a New Tool

1. Identify the target layer in `registry/layers/`
2. Add the tool entry following the canonical schema
3. Restart the application — the tool appears automatically

### Exporting to Containers

1. Open **Deployment Targets** from the sidebar
2. Select your backend: Podman, Docker, or LXC
3. Click **Export** to generate configuration files
4. Deploy with `podman compose up` or `lxc-launch.sh`

### Managing LXC Containers

```bash
# Create a container from exported config
sudo lxc-create -n ollama -f ollama.conf

# Start the container
sudo lxc-start -n ollama

# Attach to the container console
sudo lxc-attach -n ollama

# Freeze/unfreeze
sudo lxc-freeze -n ollama
sudo lxc-unfreeze -n ollama

# Destroy
sudo lxc-stop -n ollama
sudo lxc-destroy -n ollama
```

## Troubleshooting

### PySide6 Import Error

```
ModuleNotFoundError: No module named 'PySide6'
```

**Fix:** Install PySide6: `pip install PySide6`

### Registry Loading Errors

```
ERROR: Failed to load layer file: SyntaxError
```

**Fix:** Validate layer files:
```bash
python3 -c "
import ast, os
for f in os.listdir('ai_lsc/registry/layers'):
 if f.endswith('.py') and f != '__init__.py':
 ast.parse(open(f'ai_lsc/registry/layers/{f}').read())
 print(f'{f}: OK')
"
```

### Service Won't Start

1. Check the **Monitor** tab for error messages
2. Verify the tool is installed: `which <tool_name>`
3. Check launcher command in the registry entry
4. For systemd services: `systemctl --user status <service>`

### Ollama Connection Refused

1. Ensure Ollama is running: `ollama serve` or `systemctl --user start ollama`
2. Check port: `curl http://localhost:11434/api/tags`
3. Verify the endpoint in Settings matches your Ollama port

## Next Steps

- Explore the **Infrastructure** section to understand the 10-layer architecture
- Try different **Stack Templates** to find the right combination for your workflow
- Set up the **Skills Console** to extend your tool capabilities
- Use **Code Analysis** to inspect and understand your project dependencies
- Read [CHANGES.md](CHANGES.md) for the full v3.1 changelog
- Read [whatremains.txt](whatremains.txt) for known deferred items (curl|sh installers, etc.)
- Read [docs/ADR-002-pipeline-ticker.md](docs/ADR-002-pipeline-ticker.md) and [docs/ADR-003-workspace-tab.md](docs/ADR-003-workspace-tab.md) for the design rationale behind the two new widgets
