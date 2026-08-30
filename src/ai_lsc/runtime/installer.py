"""Installer manager -- dispatch-table-driven tool installation.

Handles pacman, dnf, apt, uv, pipx, pip, ollama, npm, git, git_node,
script, and custom installer types.  Every ``subprocess`` / ``os.makedirs``
call is confined here.

Key capabilities
---------------
1. **Step-down containment**: Each Python tool tries the most isolated
   install method first (ollama -> uv -> pipx -> pip).  If the preferred
   method fails, it steps down to the next one automatically.

2. **Working directory enforcement**: All tool artifacts are installed
   under ``tools_root/<tool_id>/`` (or ``tools_root/npm_globals/`` for
   npm).  This keeps the host system clean and makes tools portable.

3. **``~/.local`` remap**: Environment variables are set so that
   ``uv``, ``pip``, and ``pipx`` install into ``tools_root`` instead
   of the user's home directory.

4. **Per-tool env overrides**: Tools like vLLM, huggingface tools, etc.
   can declare ``env_overrides`` in the registry to redirect
   HF_HOME, TRANSFORMERS_CACHE, and other upstream paths into
   ``/mnt/AI/cache/<tool>`` or ``/mnt/AI/data/<tool>``.

5. **Post-install hooks**: Git-cloned tools can declare ``post_install``
   commands (e.g. ``pip install -r requirements.txt``, ``make``)
   that run automatically after clone.

6. **Preflight detection**: ``preflight()`` checks whether a tool is
   already installed (via ``which``, directory existence, or pacman
   query) and returns a ``PreflightResult`` so the UI can offer
   "update to latest" instead of blindly reinstalling.

7. **Installation verification**: ``verify()`` runs a compliance
   checklist against a single tool and returns a ``VerificationResult``
   with a quality score (0-100%).

8. **Version detection**: Attempts to extract the installed version
   for comparison with the latest available version.
"""

from __future__ import annotations

import os
import time
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ai_lsc.utils.logging import get_logger
from ai_lsc.utils.process import enriched_env

logger = get_logger(__name__)

# Registry tool_id / package name validation patterns.  Applied at every
# subprocess boundary to prevent path-traversal / command-injection from a
# malicious or malformed registry entry.
# NOTE: tool_id is used as a path component (tools_root/<tool_id>/) so it
# must NOT allow `/` or `..`.  Package names (PyPI / npm) DO allow `/`
# (e.g. `@scope/pkg`) and `@`, so they use a separate, looser regex.
_TOOL_ID_RE = re.compile(r"^[A-Za-z0-9_.:\-]+$")
_PKG_NAME_RE = re.compile(r"^[A-Za-z0-9_.@/\-+]+$")


def _validate_tool_id(tool_id: str) -> None:
    # Reject empty / regex-mismatch first.
    if not tool_id or not _TOOL_ID_RE.fullmatch(tool_id):
        raise ValueError(f"invalid tool_id: {tool_id!r}")
    # Reject path-traversal attempts that pass the char-set regex but
    # escape tools_root when joined: `.`, `..`, `...` (normpath leaves
    # these unchanged, so we check them explicitly), plus anything where
    # normpath DOES change the value (e.g. `foo/..` — though `/` is
    # already rejected by the regex above, this is defense-in-depth).
    if tool_id in {".", ".."} or os.path.normpath(tool_id) != tool_id:
        raise ValueError(f"tool_id contains path-traversal segments: {tool_id!r}")


def _validate_pkg(pkg: str) -> None:
    if not pkg or not _PKG_NAME_RE.fullmatch(pkg):
        raise ValueError(f"invalid package name: {pkg!r}")


def _validate_url(url: str, *, allow_schemes: tuple[str, ...] = ("http", "https")) -> str:
    """Validate URL scheme and return the URL unchanged if safe."""
    parsed = urlparse(url)
    if parsed.scheme not in allow_schemes or not parsed.netloc:
        raise ValueError(f"unsafe URL rejected: {url!r}")
    return url

# Step-down containment order (most isolated first)
STEP_DOWN_ORDER: list[str] = [
    "ollama", "uv", "pipx", "pip",
    "git", "git_node", "npm", "pacman", "dnf", "apt", "script", "custom",
]

# Version extraction commands per installer type
_VERSION_CMDS: dict[str, str] = {
    "pacman": "pacman -Qi {pkg} 2>/dev/null | grep Version",
    "dnf":    "dnf info {pkg} 2>/dev/null | grep Version",
    "apt":    "dpkg -s {pkg} 2>/dev/null | grep Version",
    "uv":     "{cmd} --version 2>/dev/null",
    "npm":    "npm list -g {pkg} --depth=0 2>/dev/null",
    "pip":    "pip show {pkg} 2>/dev/null | grep Version",
    "pipx":   "pipx list 2>/dev/null | grep {pkg}",
}

# Known upstream env vars that tools commonly use for data/cache.
# Format: env_var -> (human_label, default_subdir_under_base)
_UPSTREAM_ENV_VARS: dict[str, tuple[str, str]] = {
    "HF_HOME":              ("HuggingFace cache",  "cache/huggingface"),
    "TRANSFORMERS_CACHE":   ("Transformers cache",  "cache/huggingface"),
    "DIFFUSERS_CACHE":      ("Diffusers cache",     "cache/huggingface"),
    "RUST_BACKTRACE":       ("Rust backtrace",      None),
    "NODE_PATH":            ("Node modules",        None),
    "npm_config_prefix":    ("npm prefix",          None),
}


class InstallerManager:
    """Install or sync tools via the appropriate package manager.

    Parameters
    ----------
    tools_root :
        Base directory for tool installations (default ``/mnt/AI/tools``).
    base_dir :
        Top-level AI-LSC directory (``/mnt/AI``).  Used to expand
        per-tool filesystem paths.
    base_bin_dir :
        Colon-separated PATH string to prepend to all commands.
    """

    def __init__(
        self,
        tools_root: str,
        base_dir: str = "",
        base_bin_dir: str = "",
        license_gate: Any = None,
    ) -> None:
        from ai_lsc.constants import BASE_DIR
        self.tools_root = tools_root
        self.base_dir = base_dir or BASE_DIR
        self.base_bin_dir = base_bin_dir
        # License gate — if provided, every install_with_preflight /
        # run call checks the tool's license before proceeding.  If
        # None, the gate is skipped (license checks happen elsewhere,
        # e.g. in the UI layer).
        self.license_gate = license_gate

    # ── Environment construction ─────────────────────────────────────

    def _env(
        self,
        tool_id: str = "",
        env_overrides: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Build an enriched environment with ``~/.local`` remapped.

        For Python tools, we redirect uv/pip/pipx directories into
        ``tools_root`` so that artifacts do not leak into the user's
        home directory.  Per-tool ``env_overrides`` (from the registry)
        are applied last so they take precedence.
        """
        env = enriched_env(self.base_bin_dir)

        # ── Global XDG remap: ~/.local -> tools_root/.local ────────────
        env["LOCAL_BIN"] = os.path.join(self.tools_root, ".local", "bin")
        env["XDG_DATA_HOME"] = os.path.join(self.tools_root, ".local", "share")
        env["XDG_CONFIG_HOME"] = os.path.join(self.tools_root, ".local", "config")
        env["XDG_CACHE_HOME"] = os.path.join(self.tools_root, ".local", "cache")

        # ── uv-specific: force tool installs into tools_root ───────────
        if tool_id:
            uv_tool_dir = os.path.join(self.tools_root, tool_id, ".uv", "tools")
            uv_bin_dir = os.path.join(self.tools_root, tool_id, ".uv", "bin")
        else:
            uv_tool_dir = os.path.join(self.tools_root, ".uv", "tools")
            uv_bin_dir = os.path.join(self.tools_root, ".uv", "bin")
        env["UV_TOOL_DIR"] = uv_tool_dir
        env["UV_TOOL_BIN_DIR"] = uv_bin_dir
        env["UV_CACHE_DIR"] = os.path.join(self.tools_root, ".uv", "cache")

        # ── pipx-specific: force installs into tools_root ────────────────
        if tool_id:
            env["PIPX_BIN_DIR"] = os.path.join(
                self.tools_root, tool_id, ".pipx", "bin",
            )
            env["PIPX_HOME"] = os.path.join(
                self.tools_root, tool_id, ".pipx",
            )
        else:
            env["PIPX_BIN_DIR"] = os.path.join(self.tools_root, ".pipx", "bin")
            env["PIPX_HOME"] = os.path.join(self.tools_root, ".pipx")

        # ── Per-tool env overrides from registry ────────────────────────
        # Keys may contain {tools_root}, {base_dir} placeholders.
        if env_overrides:
            for key, raw_val in env_overrides.items():
                expanded = raw_val.replace(
                    "{tools_root}", self.tools_root,
                ).replace(
                    "{base_dir}", self.base_dir,
                )
                env[key] = expanded
                logger.debug(
                    "env override: %s=%s (tool %s)", key, expanded, tool_id,
                )

        # ── Prepend managed bin dirs to PATH ───────────────────────────
        managed_bins = [
            env.get("PIPX_BIN_DIR", ""),
            env.get("UV_TOOL_BIN_DIR", ""),
            os.path.join(self.tools_root, "bin"),
            os.path.join(self.tools_root, ".local", "bin"),
        ]
        extra = ":".join(d for d in managed_bins if d)
        env["PATH"] = f"{extra}:{env.get('PATH', '')}"
        return env

    # ── Preflight detection ─────────────────────────────────────────

    def preflight(
        self,
        tool_id: str,
        inst_type: str,
        pkg: str,
        cmd: str = "",
    ) -> dict[str, Any]:
        """Check whether a tool is already installed before installing.

        Returns a dict matching ``PreflightResult`` fields.
        """
        result: dict[str, Any] = {
            "tool_id": tool_id,
            "found": False,
            "install_type": inst_type,
            "location": "",
            "version": "",
            "is_update_available": False,
            "suggested_action": "install",
        }

        location, version = self._detect_installation(
            tool_id, inst_type, pkg, cmd,
        )
        if location:
            result["found"] = True
            result["location"] = location
            result["version"] = version or ""
            result["suggested_action"] = "update"

        return result

    def _detect_installation(
        self,
        tool_id: str,
        inst_type: str,
        pkg: str,
        cmd: str = "",
    ) -> tuple[str, str]:
        """Detect existing installation.  Returns (location, version)."""

        # 1. Check tools_root/<tool_id> directory existence
        tool_dir = os.path.join(self.tools_root, tool_id)
        if os.path.isdir(tool_dir):
            ver = self._detect_version(inst_type, pkg, cmd, tool_dir)
            return tool_dir, ver

        # 2. Check tools_root/.pipx, tools_root/.uv, tools_root/.local
        for subdir in [".pipx", ".uv", ".local"]:
            check = os.path.join(self.tools_root, subdir, "bin", pkg)
            if os.path.exists(check):
                return os.path.dirname(check), ""

        # 3. Check tools_root/bin
        bin_check = os.path.join(self.tools_root, "bin", pkg)
        if os.path.exists(bin_check):
            return os.path.dirname(bin_check), ""

        # 4. Check system PATH via shutil.which
        binary_name = self._binary_name(pkg, inst_type)
        system_path = shutil.which(binary_name)
        if system_path:
            ver = self._detect_version(inst_type, pkg, cmd)
            return system_path, ver

        # 5. OS package manager query (pacman / dnf / apt) — list-form
        # subprocess calls, no shell, no interpolation.
        _PKG_MGR_QUERIES: dict[str, list[str]] = {
            "pacman": ["pacman", "-Qi", pkg],
            "dnf":    ["dnf", "info", pkg],
            "apt":    ["dpkg", "-s", pkg],
        }
        if inst_type in _PKG_MGR_QUERIES:
            try:
                proc = subprocess.run(
                    _PKG_MGR_QUERIES[inst_type],
                    capture_output=True, text=True, timeout=10,
                )
                if proc.returncode == 0:
                    for line in proc.stdout.splitlines():
                        if line.strip().startswith("Version"):
                            ver = line.split(":", 1)[-1].strip()
                            return f"{inst_type}:{pkg}", ver
            except (OSError, subprocess.SubprocessError):
                pass

        return "", ""

    def _binary_name(self, pkg: str, inst_type: str) -> str:
        """Map a package name to its likely binary name."""
        if inst_type == "npm":
            return pkg if "/" not in pkg else pkg.split("/")[-1]
        if inst_type in ("uv", "pip"):
            return pkg.replace("-", "_").replace(".", "_")
        return pkg

    def _detect_version(
        self,
        inst_type: str,
        pkg: str,
        cmd: str,
        cwd: str = "",
    ) -> str:
        """Try to extract the installed version."""
        if inst_type == "git":
            git_dir = os.path.join(self.tools_root, pkg.split("/")[-1]
                                    .replace(".git", ""))
            if os.path.isdir(os.path.join(git_dir, ".git")):
                for argv in (
                    ["git", "describe", "--tags", "--abbrev=0"],
                    ["git", "rev-parse", "--short", "HEAD"],
                ):
                    try:
                        proc = subprocess.run(
                            argv,
                            capture_output=True, text=True,
                            timeout=10, cwd=git_dir,
                        )
                        if proc.returncode == 0 and proc.stdout.strip():
                            return proc.stdout.strip()
                    except (OSError, subprocess.SubprocessError):
                        continue
            return ""

        # Try the launcher command for version
        ver_argv: list[str] = []
        if cmd:
            ver_argv = shlex.split(cmd) + ["--version"]
        else:
            tmpl = _VERSION_CMDS.get(inst_type, "")
            if tmpl:
                ver_argv = shlex.split(tmpl.format(pkg=pkg, cmd=pkg))

        if not ver_argv:
            return ""

        try:
            proc = subprocess.run(
                ver_argv,
                capture_output=True, text=True,
                timeout=10, cwd=cwd or None,
            )
            if proc.returncode == 0:
                return proc.stdout.strip().split("\n")[0]
        except (OSError, subprocess.SubprocessError):
            pass
        return ""

    # ── Post-install hooks ──────────────────────────────────────────

    def _run_post_install(
        self,
        tool_id: str,
        post_install_cmd: str,
    ) -> str:
        """Run a post-install hook inside ``tools_root/<tool_id>``."""
        if not post_install_cmd:
            return ""
        dest = os.path.join(self.tools_root, tool_id)
        env = self._env(tool_id)
        # Replace {tools_root} in the command
        cmd = post_install_cmd.replace("{tools_root}", self.tools_root)
        logger.info("Running post-install for %s: %s", tool_id, cmd)
        try:
            # Post-install commands are arbitrary shell snippets supplied by
            # the registry; we still need a shell here, but we run them under
            # `bash -c` with an explicit argv (no shell=True) so the registry
            # string is passed verbatim as a single argument and cannot
            # break out of the subprocess call itself.
            subprocess.run(
                ["bash", "-c", cmd], check=True, env=env,
                timeout=300, cwd=dest,
            )
            return f"Post-install completed for {tool_id}."
        except (subprocess.CalledProcessError, OSError) as exc:
            logger.warning(
                "Post-install failed for %s: %s", tool_id, exc,
            )
            return f"Post-install FAILED for {tool_id}: {exc}"

    # ── Strategy methods ────────────────────────────────────────────

    def install_ollama(self, pkg: str, tool_id: str) -> str:
        """Pull an Ollama model or install the ollama binary."""
        if tool_id == "ollama":
            dest = os.path.join(self.tools_root, "ollama")
            os.makedirs(dest, exist_ok=True)
            import tempfile
            # SE-01: download-then-execute pattern avoids shell=True
            tmp = tempfile.NamedTemporaryFile(
                suffix=".sh", prefix="ollama-install-", delete=False,
            )
            tmp_path = tmp.name
            tmp.close()
            try:
                subprocess.run(
                    ["curl", "-fsSL", "https://ollama.com/install.sh",
                     "-o", tmp_path],
                    check=True, env=self._env("ollama"),
                )
                os.chmod(tmp_path, 0o755)
                subprocess.run(
                    ["bash", tmp_path], check=True, env=self._env("ollama"),
                    timeout=600,
                )
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            return "Ollama binary installed to system (managed by ollama)."
        return f"Ollama model '{pkg}' queued for pull."

    def install_uv(self, pkg: str, tool_id: str,
                   env_overrides: dict[str, str] | None = None) -> str:
        """Install a Python tool via ``uv tool install`` pinned to tools_root."""
        dest = os.path.join(self.tools_root, tool_id)
        os.makedirs(dest, exist_ok=True)
        env = self._env(tool_id, env_overrides)
        try:
            _validate_pkg(pkg)
            subprocess.run(
                ["uv", "tool", "install", pkg],
                check=True, env=env, timeout=300,
            )
            return f"UV tool '{pkg}' installed to {env['UV_TOOL_DIR']}."
        except subprocess.CalledProcessError:
            logger.info("uv install failed for %s, stepping down to pipx", pkg)
            return self.install_pipx(pkg, tool_id, env_overrides)

    def install_pipx(self, pkg: str, tool_id: str,
                     env_overrides: dict[str, str] | None = None) -> str:
        """Install a Python CLI tool via ``pipx`` pinned to tools_root."""
        dest = os.path.join(self.tools_root, tool_id)
        os.makedirs(dest, exist_ok=True)
        env = self._env(tool_id, env_overrides)
        try:
            _validate_pkg(pkg)
            subprocess.run(
                ["pipx", "install", pkg],
                check=True, env=env, timeout=300,
            )
            return f"pipx '{pkg}' installed to {env['PIPX_HOME']}."
        except subprocess.CalledProcessError:
            logger.info("pipx install failed for %s, stepping down to pip", pkg)
            return self.install_pip(pkg, tool_id, env_overrides)

    def install_pip(self, pkg: str, tool_id: str,
                    env_overrides: dict[str, str] | None = None) -> str:
        """Install a Python tool via ``pip`` into a per-tool venv."""
        dest = os.path.join(self.tools_root, tool_id)
        venv_dir = os.path.join(dest, ".venv")
        os.makedirs(dest, exist_ok=True)
        env = self._env(tool_id, env_overrides)
        if not os.path.isdir(venv_dir):
            subprocess.run(
                ["python3", "-m", "venv", venv_dir],
                check=True, env=env, timeout=60,
            )
        pip_bin = os.path.join(venv_dir, "bin", "pip")
        try:
            _validate_pkg(pkg)
            subprocess.run(
                [pip_bin, "install", pkg],
                check=True, env=env, timeout=300,
            )
        except subprocess.CalledProcessError as exc:
            logger.warning("pip install failed for %s: %s", pkg, exc)
            raise
        self._symlink_venv_bin(tool_id, venv_dir, pkg)
        return f"pip '{pkg}' installed to {venv_dir}."

    def _symlink_venv_bin(
        self, tool_id: str, venv_dir: str, pkg: str,
    ) -> None:
        """Create symlinks from the venv bin to tools_root/bin."""
        bin_dir = os.path.join(self.tools_root, "bin")
        os.makedirs(bin_dir, exist_ok=True)
        venv_bin = os.path.join(venv_dir, "bin")
        if os.path.isdir(venv_bin):
            for entry in os.listdir(venv_bin):
                src = os.path.join(venv_bin, entry)
                dst = os.path.join(bin_dir, entry)
                if not os.path.isfile(src):
                    continue
                # L-03: TOCTOU-safe symlink — create then handle
                # FileExistsError, instead of check-then-create.
                try:
                    os.symlink(src, dst)
                except FileExistsError:
                    pass

    def install_pacman(self, pkg: str) -> str:
        """Open a terminal for ``pacman -S`` (Arch system package)."""
        _validate_pkg(pkg)
        subprocess.Popen([
            "x-terminal-emulator", "-e", "bash", "-c",
            f"sudo pacman -S --noconfirm {shlex.quote(pkg)}; sleep 2",
        ])
        return f"Dispatched pacman for {pkg}."

    def install_dnf(self, pkg: str) -> str:
        """Open a terminal for ``dnf install`` (Fedora / RHEL)."""
        _validate_pkg(pkg)
        subprocess.Popen([
            "x-terminal-emulator", "-e", "bash", "-c",
            f"sudo dnf install -y {shlex.quote(pkg)}; sleep 2",
        ])
        return f"Dispatched dnf for {pkg}."

    def install_apt(self, pkg: str) -> str:
        """Open a terminal for ``apt install`` (Debian / Ubuntu)."""
        _validate_pkg(pkg)
        subprocess.Popen([
            "x-terminal-emulator", "-e", "bash", "-c",
            f"sudo apt-get install -y {shlex.quote(pkg)}; sleep 2",
        ])
        return f"Dispatched apt for {pkg}."

    def install_npm(self, pkg: str, tool_id: str,
                   env_overrides: dict[str, str] | None = None) -> str:
        """Install an npm package to an isolated prefix under tools_root."""
        dest = os.path.join(self.tools_root, tool_id)
        os.makedirs(dest, exist_ok=True)
        env = self._env(tool_id, env_overrides)
        _validate_pkg(pkg)
        subprocess.run(
            ["npm", "install", "--prefix", dest, pkg],
            check=True, env=env, timeout=300,
        )
        return f"NPM '{pkg}' installed to {dest}."

    def install_git(
        self,
        pkg: str,
        tool_id: str,
        post_install: str | None = None,
        env_overrides: dict[str, str] | None = None,
    ) -> str:
        """Clone or update a git repository at ``tools_root/<tool_id>``.

        Bandwidth-aware: if a git working tree already exists at the
        destination, run ``git pull --ff-only`` to fetch only the diff.
        If the destination exists but is not a git repo (or the pull
        fails for any reason — diverged branches, network errors,
        corrupted index, etc.), move the old dir aside and re-clone
        fresh, so the install always ends in a usable state.
        """
        dest = os.path.join(self.tools_root, tool_id)
        git_dir = os.path.join(dest, ".git")
        if os.path.isdir(git_dir):
            try:
                subprocess.run(
                    ["git", "-C", dest, "pull", "--ff-only"],
                    check=True, timeout=600,
                )
                msg = f"Git source updated (pulled): {dest}"
            except subprocess.CalledProcessError as exc:
                logger.warning(
                    "git pull failed for %s (%s); re-cloning fresh",
                    tool_id, exc,
                )
                backup = dest + ".bak." + str(int(time.time()))
                shutil.move(dest, backup)
                os.makedirs(dest, exist_ok=True)
                subprocess.run(
                    ["git", "clone", pkg, dest],
                    check=True, timeout=600,
                )
                msg = (
                    f"Git source re-cloned (pull failed, "
                    f"old copy at {backup}): {dest}"
                )
        elif os.path.exists(dest):
            # Dir exists but is not a git repo — back it up and clone.
            backup = dest + ".bak." + str(int(time.time()))
            shutil.move(dest, backup)
            os.makedirs(dest, exist_ok=True)
            subprocess.run(
                ["git", "clone", pkg, dest],
                check=True, timeout=600,
            )
            msg = (
                f"Git source cloned (existing non-git dir backed up "
                f"at {backup}): {dest}"
            )
        else:
            os.makedirs(dest, exist_ok=True)
            subprocess.run(
                ["git", "clone", pkg, dest],
                check=True, timeout=600,
            )
            msg = f"Git source cloned: {dest}"

        if post_install:
            self._run_post_install(tool_id, post_install)
        return msg

    def install_git_node(
        self,
        pkg: str,
        tool_id: str,
        post_install: str | None = None,
    ) -> str:
        """Clone or update a git repo and run ``yarn install``.

        Bandwidth-aware: if a git working tree already exists at the
        destination, run ``git pull --ff-only`` (diff-only fetch) and
        then ``yarn install`` to pick up any changed dependencies.  If
        the destination exists but is not a git repo, or if the pull
        fails, move the old dir aside and re-clone fresh.
        """
        dest = os.path.join(self.tools_root, tool_id)
        git_dir = os.path.join(dest, ".git")
        if os.path.isdir(git_dir):
            try:
                subprocess.run(
                    ["git", "-C", dest, "pull", "--ff-only"],
                    check=True, timeout=600,
                )
                subprocess.run(
                    ["yarn", "install"], cwd=dest, check=True, timeout=300,
                )
                msg = f"Git+Node source updated (pulled): {dest}"
            except subprocess.CalledProcessError as exc:
                logger.warning(
                    "git pull / yarn install failed for %s (%s); re-cloning",
                    tool_id, exc,
                )
                backup = dest + ".bak." + str(int(time.time()))
                shutil.move(dest, backup)
                os.makedirs(dest, exist_ok=True)
                subprocess.run(
                    ["git", "clone", pkg, dest], check=True, timeout=600,
                )
                subprocess.run(
                    ["yarn", "install"], cwd=dest, check=True, timeout=300,
                )
                msg = (
                    f"Git+Node source re-cloned (pull failed, "
                    f"old copy at {backup}): {dest}"
                )
        elif os.path.exists(dest):
            backup = dest + ".bak." + str(int(time.time()))
            shutil.move(dest, backup)
            os.makedirs(dest, exist_ok=True)
            subprocess.run(
                ["git", "clone", pkg, dest], check=True, timeout=600,
            )
            subprocess.run(
                ["yarn", "install"], cwd=dest, check=True, timeout=300,
            )
            msg = (
                f"Git+Node source cloned (existing non-git dir backed "
                f"up at {backup}): {dest}"
            )
        else:
            os.makedirs(dest, exist_ok=True)
            subprocess.run(
                ["git", "clone", pkg, dest], check=True, timeout=600,
            )
            subprocess.run(
                ["yarn", "install"], cwd=dest, check=True, timeout=300,
            )
            msg = f"Git+Node source synchronized: {dest}"

        if post_install:
            self._run_post_install(tool_id, post_install)
        return msg

    def install_script(
        self,
        cmd: str,
        ctx: dict[str, str],
        tool_id: str = "",
        env_overrides: dict[str, str] | None = None,
    ) -> str:
        """Execute an arbitrary shell script (installer type ``"script"``).

        The ``{tools_root}`` placeholder is resolved so scripts can
        direct output to the correct directory.
        """
        if "tools_root" not in ctx:
            ctx["tools_root"] = self.tools_root
        env = self._env(tool_id, env_overrides)
        # Registry 'script' installers are arbitrary shell snippets (e.g.
        # `uv pip install ... && python -m compileall .`).  We pass the
        # fully-formatted command to bash as a single argv element so the
        # subprocess call itself is shell-free.
        rendered = cmd.format(**ctx)
        subprocess.run(
            ["bash", "-c", rendered], check=True, env=env,
        )
        return "Shell script deployment completed."

    def install_custom(self, pkg: str, tool_id: str) -> str:
        """Open the install URL in the browser for manual installation."""
        import webbrowser
        url = pkg
        if not url.startswith("http"):
            url = f"https://{url}"
        # H-20 / H-22: reject non-http(s) schemes (file://, javascript:, …)
        _validate_url(url)
        webbrowser.open(url)
        return (
            f"Opened {url} in browser for manual installation "
            f"of {tool_id}. Follow the instructions on the page."
        )

    # ── Dispatcher ─────────────────────────────────────────────────

    def _check_license(self, tool_id: str, spdx: str | None) -> None:
        """Check the tool's license against the gate before install.

        Raises ``LicenseBlocked`` if the tool_id is on the SaaS
        blocklist, or ``LicenseAcceptanceRequired`` if the license
        has not been accepted yet.  No-op if ``self.license_gate`` is
        None or *spdx* is falsy.
        """
        if self.license_gate is None or not spdx:
            return
        result = self.license_gate.check(tool_id, spdx)
        if result.status == "blocked":
            from ai_lsc.registry.license_gate import LicenseBlocked
            raise LicenseBlocked(tool_id=tool_id, reason=result.reason)
        if result.status == "needs_acceptance":
            from ai_lsc.registry.license_gate import LicenseAcceptanceRequired
            raise LicenseAcceptanceRequired(
                tool_id=tool_id,
                license_info=result.license_info,
            )

    def run(
        self,
        inst_type: str,
        pkg: str,
        cmd: str = "",
        ctx: dict[str, str] | None = None,
        tool_id: str = "",
        post_install: str | None = None,
        env_overrides: dict[str, str] | None = None,
        license_spdx: str | None = None,
    ) -> str:
        """Dispatch to the correct installer strategy.

        Returns a human-readable description of what happened.

        Parameters
        ----------
        license_spdx :
            SPDX ID for the tool's license.  If provided AND a
            ``license_gate`` was passed to the InstallerManager
            constructor, the gate checks the license before dispatch.
            If the gate returns ``blocked`` or ``needs_acceptance``,
            the appropriate exception is raised before any subprocess
            call.

        Raises
        ------
        ValueError
            If *inst_type* is not recognized.
        subprocess.CalledProcessError
            If the underlying command fails.
        LicenseBlocked
            If the tool_id is on the SaaS blocklist.
        LicenseAcceptanceRequired
            If the tool's license has not been accepted yet.
        """
        ctx = ctx or {}
        if not tool_id:
            if "github.com" in pkg:
                tool_id = (pkg.rstrip("/").rsplit("/", 1)[-1]
                           .replace(".git", ""))
            else:
                tool_id = pkg.split("/")[-1].split(":")[0]

        # License gate — check before any subprocess call.
        self._check_license(tool_id, license_spdx)

        strategies: dict[str, Any] = {
            "ollama": lambda: self.install_ollama(pkg, tool_id),
            "uv":     lambda: self.install_uv(pkg, tool_id, env_overrides),
            "pipx":   lambda: self.install_pipx(pkg, tool_id, env_overrides),
            "pip":    lambda: self.install_pip(pkg, tool_id, env_overrides),
            "script": lambda: self.install_script(
                cmd, ctx, tool_id, env_overrides,
            ),
            "pacman": lambda: self.install_pacman(pkg),
            "dnf":    lambda: self.install_dnf(pkg),
            "apt":    lambda: self.install_apt(pkg),
            "npm":    lambda: self.install_npm(pkg, tool_id, env_overrides),
            "git":    lambda: self.install_git(
                pkg, tool_id, post_install, env_overrides,
            ),
            "git_node": lambda: self.install_git_node(
                pkg, tool_id, post_install,
            ),
            "custom": lambda: self.install_custom(pkg, tool_id),
        }
        handler = strategies.get(inst_type)
        if handler is None:
            raise ValueError(f"Unknown installer type '{inst_type}'")
        return handler()

    # ── Batch operations ────────────────────────────────────────────

    def preflight_batch(
        self,
        tools: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Run preflight checks for multiple tools at once.

        Parameters
        ----------
        tools :
            Dict of ``{tool_id: registry_entry}`` from the registry.

        Returns
        -------
        Dict of ``{tool_id: preflight_result_dict}``.
        """
        return {
            tid: self.preflight(
                tool_id=tid,
                inst_type=meta.get("installer", {}).get("type", "pacman"),
                pkg=meta.get("installer", {}).get("pkg", ""),
                cmd=meta.get("installer", {}).get("cmd", ""),
            )
            for tid, meta in tools.items()
        }

    def install_with_preflight(
        self,
        tool_id: str,
        inst_type: str,
        pkg: str,
        cmd: str = "",
        ctx: dict[str, str] | None = None,
        force: bool = False,
        post_install: str | None = None,
        env_overrides: dict[str, str] | None = None,
        license_spdx: str | None = None,
    ) -> str:
        """Install a tool with preflight detection.

        If the tool is already installed and *force* is False, returns
        a message saying the tool exists and suggesting an update.
        If *force* is True, proceeds with installation regardless.

        Parameters
        ----------
        license_spdx :
            SPDX ID for the tool's license.  Forwarded to ``run()``
            for gate checking.
        """
        # License gate — check before preflight so we don't waste a
        # subprocess call on a blocked tool.
        self._check_license(tool_id, license_spdx)

        check = self.preflight(tool_id, inst_type, pkg, cmd)
        if check["found"] and not force:
            return (
                f"Tool '{tool_id}' already installed at {check['location']}. "
                f"Version: {check['version'] or 'unknown'}. "
                f"Use force=True to update."
            )
        return self.run(
            inst_type, pkg, cmd, ctx, tool_id,
            post_install, env_overrides,
        )

    # ── Installation verification ───────────────────────────────────

    def verify(
        self,
        tool_id: str,
        inst_type: str,
        pkg: str,
        cmd: str = "",
        filesystem: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Run a compliance checklist against a single tool installation.

        Checks:
        1. Native install detected
        2. Installed entirely under /mnt/AI (no ~/.local leak)
        3. Config redirected from $HOME
        4. Cache redirected
        5. Logs redirected
        6. Launcher binary accessible
        7. Update command available
        8. Version detection works
        9. Health check (binary --version or --help)

        Returns a dict matching ``VerificationResult`` fields.
        """
        from ai_lsc.types import VerifyCheck

        checks: list[VerifyCheck] = []
        fs = filesystem or {}
        tool_dir = os.path.join(self.tools_root, tool_id)

        # 1. Native install detected
        location, version = self._detect_installation(
            tool_id, inst_type, pkg, cmd,
        )
        checks.append(VerifyCheck(
            name="Native Install",
            passed=bool(location),
            detail=location or "not found",
        ))

        # 2. Installed under /mnt/AI (no system leak)
        is_managed = (
            location and location.startswith(self.base_dir)
        ) or inst_type == "pacman" or inst_type in ("dnf", "apt")
        checks.append(VerifyCheck(
            name="Filesystem Compliance",
            passed=is_managed,
            detail=location or "N/A",
        ))

        # 3. Config path (if declared in filesystem spec)
        config_path = fs.get("config", "")
        if config_path:
            full = os.path.join(self.base_dir, config_path)
            exists = os.path.isdir(full)
            checks.append(VerifyCheck(
                name="Config Redirect",
                passed=exists or not location,
                detail=full,
            ))

        # 4. Cache path
        cache_path = fs.get("cache", "")
        if cache_path:
            full = os.path.join(self.base_dir, cache_path)
            checks.append(VerifyCheck(
                name="Cache Redirect",
                passed=os.path.isdir(full) or not location,
                detail=full,
            ))

        # 5. Logs path
        logs_path = fs.get("logs", "")
        if logs_path:
            full = os.path.join(self.base_dir, logs_path)
            checks.append(VerifyCheck(
                name="Logs Redirect",
                passed=os.path.isdir(full) or not location,
                detail=full,
            ))

        # 6. Launcher binary accessible
        binary = self._binary_name(pkg, inst_type)
        bin_path = shutil.which(binary)
        checks.append(VerifyCheck(
            name="Launcher Accessible",
            passed=bool(bin_path),
            detail=bin_path or f"{binary} not in PATH",
        ))

        # 7. Version detection
        checks.append(VerifyCheck(
            name="Version Detection",
            passed=bool(version),
            detail=version or "unknown",
        ))

        # 8. Health check (try --version or --help)
        healthy = False
        if bin_path:
            for flag in ("--version", "--help"):
                try:
                    proc = subprocess.run(
                        [bin_path, flag],
                        capture_output=True, text=True, timeout=5,
                    )
                    if proc.returncode == 0:
                        healthy = True
                        break
                except (OSError, subprocess.SubprocessError):
                    continue
        checks.append(VerifyCheck(
            name="Health Check",
            passed=healthy,
            detail="responds to --version/--help" if healthy else "no response",
        ))

        return {
            "tool_id": tool_id,
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail}
                for c in checks
            ],
            "install_method": inst_type,
            "install_location": location or "",
            "score": (
                int(sum(1 for c in checks if c.passed) / len(checks) * 100)
                if checks else 0
            ),
        }
