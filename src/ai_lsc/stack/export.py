"""
AI-LSC -- Stack export and container backend.

Contains pure-logic functions for:

* **build_stack_spec** -- serialises the current pipeline state plus
  registry metadata into a portable JSON spec.
* **ContainerBackend** -- generates Podman/Docker compose YAML,
  LXC container configs, Firecracker microVM configs, or JSON fallback
  from that spec.

No UI code here.  All path operations use :mod:`pathlib`.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_lsc.constants import BASE_DIR, STACK_SCHEMA_VERSION
from ai_lsc.registry.manager import RegistryManager
from ai_lsc.utils.paths import build_path_tree


# H-17: single helper for the placeholder-resolution chain that was
# previously duplicated in three methods (compose / lxc / firecracker).
_PLACEHOLDER_KEYS = (
    "base_dir",
    "tools_root",
    "models_root",
    "workspaces_root",
)


def _resolve_placeholders(cmd: str, paths: dict[str, Any]) -> str:
    """Replace ``{base_dir}`` / ``{tools_root}`` / ... placeholders in *cmd*.

    Returns the command unchanged if it is empty.
    """
    if not cmd:
        return ""
    resolved = cmd
    for key in _PLACEHOLDER_KEYS:
        resolved = resolved.replace("{" + key + "}", str(paths.get(key, "")))
    return resolved


def build_stack_spec(
    state: dict[str, Any],
    registry: RegistryManager,
    backend: str = "podman",
) -> dict[str, Any]:
    """Build a portable stack spec from the current state + registry.

    The resulting dict is JSON-serialisable and can be passed to
    ``ContainerBackend`` for compose-file / config generation.

    Parameters
    ----------
    state :
        Pipeline state dict (must contain ``active_tools`` and
        optionally ``port_map``).
    registry :
        A loaded ``RegistryManager`` instance.
    backend :
        Container backend type (``"podman"``, ``"docker"``, ``"lxc"``,
        or ``"firecracker"``).
    """
    tools = [
        {
            "id": tid,
            "name": registry.get_tool(tid).get("name"),
            "layer": registry.get_tool(tid).get("layer"),
            "role": registry.get_tool(tid).get("role"),
            "category": registry.get_tool(tid).get("category"),
            "launcher": registry.get_tool(tid).get("launcher"),
            "installer": registry.get_tool(tid).get("installer"),
            "deps": registry.get_tool(tid).get("deps", []),
        }
        for tid in state.get("active_tools", [])
        if not tid.startswith("skill:")
    ]

    return {
        "schema": STACK_SCHEMA_VERSION,
        "created": datetime.now().isoformat(),
        "backend": backend,
        "tools": tools,
        "ports": state.get("port_map", {}),
        "base_dir": BASE_DIR,
    }


class ContainerBackend:
    """Generates container deployment files from a stack spec.

    Supports four backends:

    * **podman/docker** -- ``docker-compose.yaml`` (version 3.8)
    * **lxc** -- per-container config files + launch script
    * **firecracker** -- per-microVM ``vm-config.json`` + launch script

    Parameters
    ----------
    exports_root :
        Directory where output files are written.
    """

    def __init__(self, exports_root: str | Path) -> None:
        self.exports_root = Path(exports_root)

    # ── Compose (Podman / Docker) ──────────────────────────────────────

    def generate_compose_yaml(self, spec: dict) -> dict:
        """Transform a stack spec into a compose-file data structure.

        Each tool becomes a service with ``network_mode: host``,
        ``restart: unless-stopped``, and the base directory mounted as a
        volume.  The launcher command's ``{placeholders}`` are resolved
        to absolute paths.
        """
        paths = build_path_tree(spec.get("base_dir", BASE_DIR))
        services: dict[str, dict] = {}

        for tool in spec.get("tools", []):
            raw_cmd = tool.get("launcher", {}).get("cmd", "")
            svc: dict[str, Any] = {
                "image": f"localhost/ai-lsc-{tool['id']}:latest",
                "network_mode": "host",
                "restart": "unless-stopped",
                "volumes": [f"{paths['base_dir']}:{paths['base_dir']}"],
            }
            clean_cmd = _resolve_placeholders(raw_cmd, paths)
            if clean_cmd.strip():
                svc["command"] = clean_cmd
            services[tool["id"]] = svc

        return {"version": "3.8", "services": services}

    def write_compose(
        self,
        spec: dict,
        backend_type: str = "podman",
    ) -> Path:
        """Write compose YAML (or JSON fallback) to disk.

        Returns the path of the written file.
        """
        self.exports_root.mkdir(parents=True, exist_ok=True)
        file_path = self.exports_root / f"{backend_type}-compose.yml"
        compose_data = self.generate_compose_yaml(spec)

        try:
            import yaml
            file_path.write_text(
                yaml.dump(compose_data, sort_keys=False),
                encoding="utf-8",
            )
        except ImportError:
            file_path.write_text(
                json.dumps(compose_data, indent=4),
                encoding="utf-8",
            )

        return file_path

    # ── LXC backend ─────────────────────────────────────────────────────

    def generate_lxc_configs(self, spec: dict) -> dict[str, str]:
        """Generate LXC config blocks for each tool in the stack.

        Returns a dict mapping container names to their config file
        content.  Each config block includes:

        * Base OS template (default: ``ubuntu:22.04``)
        * Network mode (``lxc.net.0.type = veth`` or ``none``)
        * Mount points for the base directory hierarchy
        * Autostart flag
        * Tool-specific command to execute on start
        """
        paths = build_path_tree(spec.get("base_dir", BASE_DIR))
        configs: dict[str, str] = {}

        for tool in spec.get("tools", []):
            container_name = f"ai-lsc-{tool['id']}"
            raw_cmd = tool.get("launcher", {}).get("cmd", "")

            # Resolve placeholders in the command
            clean_cmd = _resolve_placeholders(raw_cmd, paths)

            lines = [
                f"# AI-LSC auto-generated LXC config for {tool['id']}",
                f"# Container: {container_name}",
                f"# Tool: {tool.get('name', tool['id'])}",
                "",
                "# -- Basic container settings --",
                "lxc.uts.name = " + container_name,
                "lxc.init.cmd = /bin/bash",
                "",
                "# -- Network --",
                "lxc.net.0.type = veth",
                "lxc.net.0.flags = up",
                "lxc.net.0.link = lxcbr0",
                "",
                "# -- Mounts --",
                f"lxc.mount.auto = proc:mixed sys:ro",
                f"lxc.rootfs.mount = {paths['base_dir']}/containers/{container_name}/rootfs",
                f"# Mount AI stack base directory",
                f"lxc.mount.entry = {paths['base_dir']} {paths['base_dir']} none bind,rw 0 0",
                f"# Mount tools directory",
                f"lxc.mount.entry = {paths['tools_root']} {paths['tools_root']} none bind,rw 0 0",
                f"# Mount models directory",
                f"lxc.mount.entry = {paths['models_root']} {paths['models_root']} none bind,rw 0 0",
                "",
                "# -- Autostart --",
                "lxc.start.auto = 1",
                "lxc.start.delay = 5",
                "",
                "# -- Tool launch command --",
                f"lxc.execute.post = /usr/bin/env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin {clean_cmd}" if clean_cmd.strip() else "",
            ]

            configs[container_name] = "\n".join(
                line for line in lines if line
            )

        return configs

    def write_lxc(
        self,
        spec: dict,
    ) -> Path:
        """Write LXC configs and a launch script to disk.

        Creates:
        * ``<exports_root>/lxc/`` -- per-container config files
        * ``<exports_root>/lxc-launch.sh`` -- shell script to create
          and start all containers

        Returns the path of the launch script.
        """
        lxc_dir = self.exports_root / "lxc"
        lxc_dir.mkdir(parents=True, exist_ok=True)

        configs = self.generate_lxc_configs(spec)
        container_names: list[str] = []

        # Write individual config files
        for container_name, config_text in configs.items():
            config_path = lxc_dir / f"{container_name}.conf"
            config_path.write_text(config_text, encoding="utf-8")
            container_names.append(container_name)

        # Generate launch script
        script_lines = [
            "#!/usr/bin/env bash",
            "# AI-LSC LXC Stack Launcher",
            f"# Generated: {datetime.now().isoformat()}",
            f"# Containers: {len(container_names)}",
            f"# Backend: lxc",
            "",
            'set -euo pipefail',
            "",
            "LXC_DIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"",
            "",
            "echo \"[AI-LSC] Creating LXC containers...\"",
            "",
        ]

        for container_name in container_names:
            conf_file = f"{container_name}.conf"
            script_lines.extend([
                f"if ! lxc-info -n {container_name} >/dev/null 2>&1; then",
                f"    echo \"  Creating {container_name}...\"",
                f"    lxc-create -n {container_name} -t download -- -d ubuntu -r jammy -a amd64",
                f"    cp \"$LXC_DIR/{conf_file}\" /var/lib/lxc/{container_name}/config.d/ai-lsc.conf",
                f"else",
                f"    echo \"  {container_name} already exists, skipping creation\"",
                f"fi",
                "",
            ])

        script_lines.extend([
            "",
            "echo \"[AI-LSC] Starting LXC containers...\"",
            "",
        ])

        for container_name in container_names:
            script_lines.append(
                f"echo \"  Starting {container_name}...\""
            )
            script_lines.append(
                f"lxc-start -n {container_name} -d -F \"$LXC_DIR/{container_name}.conf\" 2>/dev/null || "
                f"lxc-start -n {container_name} -d"
            )
            script_lines.append("")

        script_lines.extend([
            "echo \"[AI-LSC] Stack launched. Use 'lxc-ls --running' to verify.\"",
            f"echo \"[AI-LSC] {len(container_names)} containers active.\"",
            "",
            "# -- Stop command --",
            f"echo ''",
            f"echo 'To stop all containers:'",
            f"for c in {' '.join(container_names)}; do",
            f"    echo \"  lxc-stop -n $c -t 5\"",
            f"done",
        ])

        launch_script = self.exports_root / "lxc-launch.sh"
        launch_script.write_text("\n".join(script_lines), encoding="utf-8")
        launch_script.chmod(0o755)

        return launch_script

    # ── Firecracker backend ────────────────────────────────────────────

    # Default kernel / rootfs paths under the AI-LSC base dir.  The user
    # can override these by dropping replacement files at these locations
    # or by editing the generated vm-config.json after export.
    _FC_KERNEL_PATH = "{base_dir}/containers/firecracker/vmlinux"
    _FC_ROOTFS_TEMPLATE = "{base_dir}/containers/firecracker/rootfs-{tool_id}.ext4"

    def generate_firecracker_configs(self, spec: dict) -> dict[str, dict]:
        """Generate Firecracker microVM config dicts for each tool.

        Returns a dict mapping VM names to their Firecracker API config
        (the JSON payload that gets PUT to ``/vm/config`` on the
        Firecracker VMM socket).  Each config includes:

        * ``boot-source`` -- kernel image + kernel cmdline
        * ``drives`` -- a single rootfs block device (read-write)
        * ``machine-config`` -- vCPU count, mem size Mib, HT flag
        * ``network-interfaces`` -- a single TAP interface (optional)
        * ``ai_lsc`` -- metadata block with tool id, name, and the
          resolved launch command (not consumed by Firecracker itself
          but used by the launch script)

        The actual Firecracker process is started by ``write_firecracker``'s
        ``firecracker-launch.sh`` script, which spawns one VMM per VM.
        """
        paths = build_path_tree(spec.get("base_dir", BASE_DIR))
        configs: dict[str, dict] = {}

        for tool in spec.get("tools", []):
            vm_name = f"ai-lsc-{tool['id']}"
            raw_cmd = tool.get("launcher", {}).get("cmd", "")

            # Resolve placeholders in the command
            clean_cmd = _resolve_placeholders(raw_cmd, paths)

            # Resolve port if the spec carries one for this tool
            port = spec.get("ports", {}).get(tool["id"])
            if port:
                clean_cmd = clean_cmd.replace("{port}", str(port))

            kernel_path = self._FC_KERNEL_PATH.format(
                base_dir=str(paths["base_dir"])
            )
            rootfs_path = self._FC_ROOTFS_TEMPLATE.format(
                base_dir=str(paths["base_dir"]),
                tool_id=tool["id"],
            )

            # Kernel cmdline: quiet boot, root on /dev/vda, run the
            # tool's launch command as init's first action.
            init_arg = clean_cmd.strip() or "/bin/sh"
            kernel_cmdline = (
                "console=ttyS0 reboot=k panic=1 pci=off "
                f"root=/dev/vda rw -- {init_arg}"
            )

            config = {
                "boot-source": {
                    "kernel_image_path": kernel_path,
                    "boot_args": kernel_cmdline,
                },
                "drives": [
                    {
                        "drive_id": "rootfs",
                        "path_on_host": rootfs_path,
                        "is_root_device": True,
                        "is_read_only": False,
                    }
                ],
                "machine-config": {
                    "vcpu_count": 2,
                    "mem_size_mib": 2048,
                    "ht_enabled": False,
                },
                "ai_lsc": {
                    "tool_id": tool["id"],
                    "tool_name": tool.get("name", tool["id"]),
                    "vm_name": vm_name,
                    "launch_cmd": init_arg,
                    "default_port": port,
                },
            }

            # Only attach a TAP interface if the tool exposes a port —
            # pure CLIs (port=None) get a network-less VM.
            if port:
                config["network-interfaces"] = [
                    {
                        "iface_id": "eth0",
                        "host_dev_name": f"fc-tap-{tool['id']}",
                        "guest_mac": self._fc_mac(tool["id"]),
                    }
                ]

            configs[vm_name] = config

        return configs

    @staticmethod
    def _fc_mac(tool_id: str) -> str:
        """Derive a deterministic guest MAC from a tool id.

        Uses the bytes of the tool id (zero-padded / truncated) so the
        same tool always gets the same MAC across reboots.
        """
        digest = tool_id.encode("utf-8")[:3].ljust(3, b"\x00")
        octets = ["52", "54"] + [f"{b:02x}" for b in digest]
        return ":".join(octets)

    def write_firecracker(
        self,
        spec: dict,
    ) -> Path:
        """Write Firecracker VM configs and a launch script to disk.

        Creates:

        * ``<exports_root>/firecracker/`` -- per-VM ``vm-config.json`` files
        * ``<exports_root>/firecracker-launch.sh`` -- shell script that
          spawns one Firecracker VMM per VM and waits for them to exit

        The on-disk JSON is stripped to *only* the Firecracker API
        schema (``boot-source`` / ``drives`` / ``machine-config`` /
        ``network-interfaces``).  The ``ai_lsc`` metadata block produced
        by :meth:`generate_firecracker_configs` is dropped before write
        so the VMM doesn't reject unknown fields.

        Returns the path of the launch script.
        """
        fc_dir = self.exports_root / "firecracker"
        fc_dir.mkdir(parents=True, exist_ok=True)

        configs = self.generate_firecracker_configs(spec)
        vm_names: list[str] = []
        # Keys that the Firecracker VMM actually understands.  Anything
        # else (like our ai_lsc metadata block) is dropped from the
        # on-disk JSON.
        _FC_SCHEMA_KEYS = {
            "boot-source", "drives", "machine-config",
            "network-interfaces", "balloon", "logger", "metrics",
            "vsock", "mmds",
        }

        # Write per-VM config files (schema-stripped)
        for vm_name, config in configs.items():
            clean_config = {
                k: v for k, v in config.items()
                if k in _FC_SCHEMA_KEYS
            }
            cfg_path = fc_dir / f"{vm_name}.json"
            cfg_path.write_text(
                json.dumps(clean_config, indent=2),
                encoding="utf-8",
            )
            vm_names.append(vm_name)

        # Generate launch script
        script_lines = [
            "#!/usr/bin/env bash",
            "# AI-LSC Firecracker microVM Launcher",
            f"# Generated: {datetime.now().isoformat()}",
            f"# VMs: {len(vm_names)}",
            "# Backend: firecracker",
            "",
            "set -euo pipefail",
            "",
            '# AI-LSC base directory (override with AI_LSC_BASE_DIR env var)',
            'BASE_DIR="${AI_LSC_BASE_DIR:-/mnt/AI}"',
            'export BASE_DIR',
            "",
            'FC_DIR="$(cd "$(dirname "$0")" && pwd)/firecracker"',
            'FC_SOCKET_DIR="$(mktemp -d)"',
            "",
            "if ! command -v firecracker >/dev/null 2>&1; then",
            '    echo "[AI-LSC] firecracker binary not found on PATH." >&2',
            '    echo "[AI-LSC] Install via: curl -fsSL https://firecracker-microvm.github.io/firecracker/getting-started.html" >&2',
            "    exit 1",
            "fi",
            "",
            'if [ ! -f "' + self._FC_KERNEL_PATH.format(base_dir="$BASE_DIR") + '" ]; then',
            '    echo "[AI-LSC] Kernel image not found at ' + self._FC_KERNEL_PATH.format(base_dir="$BASE_DIR") + '" >&2',
            '    echo "[AI-LSC] Download vmlinux from the firecracker release assets." >&2',
            "    exit 1",
            "fi",
            "",
            'echo "[AI-LSC] Launching {n} Firecracker microVMs..."'.format(
                n=len(vm_names)
            ),
            "",
            "PIDS=()",
        ]

        for vm_name in vm_names:
            tool_id = vm_name.removeprefix("ai-lsc-")
            script_lines.extend([
                "",
                f"# ── {vm_name} ─────────────────────────────────────────",
                f'SOCKET="$FC_SOCKET_DIR/{vm_name}.sock"',
                f'API_CFG="$FC_DIR/{vm_name}.json"',
                f'firecracker --api-sock "$SOCKET" --no-api --config-file "$API_CFG" &',
                f"PIDS+=($!)",
                f'echo "  started {vm_name} (pid ${{PIDS[-1]}})"',
                "",
                f"# Create TAP device for {vm_name} if needed",
                f'TAP_NAME="fc-tap-{tool_id}"',
                'if ! ip link show "$TAP_NAME" >/dev/null 2>&1; then',
                '    ip tuntap add "$TAP_NAME" mode tap 2>/dev/null || '
                'echo "  (skipped TAP creation — needs root)"',
                '    ip link set "$TAP_NAME" up 2>/dev/null || true',
                "fi",
            ])

        script_lines.extend([
            "",
            'echo "[AI-LSC] All microVMs launched."',
            'echo "[AI-LSC] Use \'pgrep -f firecracker\' to verify."',
            "",
            "# -- Stop command --",
            "echo ''",
            "echo 'To stop all microVMs:'",
            f"for p in ${{PIDS[@]}}; do",
            f"    echo \"  kill $p\"",
            f"done",
            'echo "Or: pkill -f firecracker"',
        ])

        launch_script = self.exports_root / "firecracker-launch.sh"
        launch_script.write_text("\n".join(script_lines), encoding="utf-8")
        launch_script.chmod(0o755)

        return launch_script

    # ── Unified write (auto-selects backend) ──────────────────────────

    def write(
        self,
        spec: dict,
        backend_type: str = "podman",
    ) -> Path:
        """Write deployment files for the specified backend.

        Parameters
        ----------
        spec :
            Stack specification dict (from ``build_stack_spec``).
        backend_type :
            One of ``"podman"``, ``"docker"``, ``"lxc"``, or
            ``"firecracker"``.

        Returns
        -------
        Path to the primary output file.
        """
        if backend_type == "lxc":
            return self.write_lxc(spec)
        if backend_type == "firecracker":
            return self.write_firecracker(spec)
        return self.write_compose(spec, backend_type=backend_type)
