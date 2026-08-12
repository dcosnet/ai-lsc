"""
AI-LSC — Registry schema validation.

Validates that registry entries conform to the expected schema.  This is
intended for CI / developer tooling, not for hot-path runtime checks
(so a small upfront cost is acceptable).

Usage::

    from ai_lsc.registry.validator import validate_registry

    errors = validate_registry(registry_data)
    if errors:
        for e in errors:
            print(f"  - {e}")
"""

from __future__ import annotations

import re
from typing import Any

# Fields that every registry entry must contain.
_REQUIRED_FIELDS: set[str] = {
    "name", "level", "layer", "role", "category",
    "installer", "launcher", "deps", "description", "flags",
    "license",
}

# Valid values for certain fields — must match InstallerType / LauncherType enums.
_VALID_INSTALLER_TYPES: set[str] = {
    "ollama", "uv", "pipx", "pip", "npm",
    "git", "git_node", "pacman", "dnf", "apt",
    "script", "custom",
}
_VALID_LAUNCHER_TYPES: set[str] = {
    "systemd", "tmux", "desktop", "lxc",
}

# Optional installer fields (allowed but not required).
_OPTIONAL_INSTALLER_FIELDS: set[str] = {
    "type", "pkg", "cmd", "post_install", "update_cmd", "env_overrides",
}
_OPTIONAL_LAUNCHER_FIELDS: set[str] = {
    "type", "cmd", "default_port",
}
_OPTIONAL_FILESYSTEM_FIELDS: set[str] = {
    "install", "config", "cache", "data", "logs", "runtime", "models",
}

# H-15: every registry entry's `flags` block must declare all 7 boolean
# keys.  Layer files that pre-date the schema expansion only declare the
# first three (has_cli/has_gui/has_web); they fail this check until the
# missing keys are backfilled.
_REQUIRED_FLAG_KEYS: set[str] = {
    "has_cli", "has_gui", "has_web",
    "is_ollama",
    "is_passive", "is_mcp", "is_skills_collection",
}

# License SPDX IDs recognized by the license catalog
# (registry/licenses.py CATALOG).  Populated lazily to avoid a circular
# import (licenses.py imports nothing from validator.py, but importing
# it at module-load time here is fine).
try:
    from ai_lsc.registry.licenses import CATALOG as _LICENSE_CATALOG
    _KNOWN_LICENSE_SPDX_IDS: set[str] = set(_LICENSE_CATALOG.keys())
except ImportError:
    # During bootstrap before licenses.py exists, fall back to empty.
    _KNOWN_LICENSE_SPDX_IDS = set()

# SaaS-only tool blocklist — these tool_ids (and case-insensitive
# variants) are rejected by the validator.  The user's policy is that
# SaaS-only tools (closed-source desktop apps with restrictive ToS,
# hosted LLM routers with no local binary, managed inference services)
# do not belong in AI-LSC.  Tools that CAN call a SaaS endpoint but
# don't have to (claude_code, aider, openhands, fabric, codex) are
# allowed — their launchers force ANTHROPIC_BASE_URL /
# OPENAI_BASE_URL to http://127.0.0.1:{port} so SaaS routing is
# broken by default.  See ADR-001 + CHANGES.md for the rationale.
#
# lm_studio / lmstudio: BLOCKED for aggressive ToS — the user
# considers LM Studio's Terms of Service restrictive enough to be
# equivalent to a SaaS offering, so it is auto-banned regardless of
# any per-tool acceptance the user might try to grant.
SAAS_BLOCKLIST: frozenset[str] = frozenset({
    "openrouter",
    "lm_studio", "lmstudio",
    "groq",
    "together_ai", "together",
    "fireworks_ai", "fireworks",
    "replicate",
    "runpod",
    "modal",
    "anyscale",
    "perplexity",
    "cohere",
    "mistral_api",
    "deepseek_api",
    "openai_api",
    "huggingface_inference",
})

# SaaS provider hostnames that must never appear in a launcher cmd or
# installer cmd (excluding git/git_node which clone source code, not
# SaaS).  Matches http(s)://host where host is a known SaaS provider.
_SAAS_HOST_RE = re.compile(
    r"https?://(?:"
    r"api\.openrouter\.ai|"
    r"api\.openai\.com|"
    r"api\.anthropic\.com|"
    r"api\.groq\.com|"
    r"api\.together\.xyz|"
    r"api\.fireworks\.ai|"
    r"api\.replicate\.com|"
    r"api\.perplexity\.ai|"
    r"api\.cohere\.ai|"
    r"api\.mistral\.ai|"
    r"api\.deepseek\.com|"
    r"generativelanguage\.googleapis\.com|"
    r"api\.lmsstudio\.com|"
    r"api\.lmstudio\.ai|"
    r"endpoint\.huggingface\.com"
    r")",
    re.IGNORECASE,
)


def _check_entry(tool_id: str, entry: dict[str, Any]) -> list[str]:
    """Return a list of validation error strings for a single entry."""
    errors: list[str] = []

    # SaaS-only tool blocklist — reject before any other check so the
    # error message is the first thing the user sees.  Case-insensitive.
    if tool_id.lower() in SAAS_BLOCKLIST:
        errors.append(
            f"{tool_id}: tool_id is on the SaaS-only blocklist — "
            f"AI-LSC policy excludes SaaS-only tools (closed-source "
            f"desktop apps with restrictive ToS, hosted LLM routers "
            f"with no local binary, managed inference services). "
            f"Use a local alternative (ollama, vllm, litellm, etc.) "
            f"instead.  See CHANGES.md → 'SaaS-only tool blocklist' "
            f"for the rationale."
        )
        # Continue running the other checks so the user sees every
        # problem with the entry in one pass.

    # Missing required fields
    missing = _REQUIRED_FIELDS - entry.keys()
    if missing:
        errors.append(f"{tool_id}: missing fields {sorted(missing)}")

    # Level must be 1–13
    level = entry.get("level")
    if isinstance(level, int) and not (1 <= level <= 13):
        errors.append(f"{tool_id}: level {level} out of range 1-13")
    elif not isinstance(level, int):
        errors.append(f"{tool_id}: level is not an int ({level!r})")

    # Installer type
    inst = entry.get("installer", {})
    if isinstance(inst, dict):
        itype = inst.get("type")
        if itype and itype not in _VALID_INSTALLER_TYPES:
            errors.append(
                f"{tool_id}: unknown installer type {itype!r} "
                f"(valid: {sorted(_VALID_INSTALLER_TYPES)})"
            )
        # Script-type installers must include cmd
        if itype == "script" and not inst.get("cmd"):
            errors.append(
                f"{tool_id}: installer type 'script' requires 'cmd'"
            )
        # Warn if script cmd doesn't contain {tools_root}
        if itype == "script" and inst.get("cmd"):
            cmd_str = inst["cmd"]
            if "{tools_root}" not in cmd_str and tool_id != "ollama":
                errors.append(
                    f"{tool_id}: script installer cmd should reference "
                    f"{{{{tools_root}}}} to avoid polluting system dirs"
                )
        # SaaS host check — reject installers that reference a known
        # SaaS provider URL (excluding git/git_node which clone source
        # code, not SaaS endpoints).
        if itype not in ("git", "git_node"):
            for field in ("cmd", "pkg"):
                val = inst.get(field, "")
                if isinstance(val, str) and _SAAS_HOST_RE.search(val):
                    errors.append(
                        f"{tool_id}: installer.{field} references a "
                        f"SaaS provider URL — AI-LSC policy excludes "
                        f"SaaS-only tools.  Use a local alternative "
                        f"instead.  See CHANGES.md → 'SaaS-only tool "
                        f"blocklist' for the rationale."
                    )

    # Launcher type
    launch = entry.get("launcher", {})
    if isinstance(launch, dict):
        ltype = launch.get("type")
        if ltype and ltype not in _VALID_LAUNCHER_TYPES:
            errors.append(
                f"{tool_id}: unknown launcher type {ltype!r} "
                f"(valid: {sorted(_VALID_LAUNCHER_TYPES)})"
            )
        # SaaS host check — reject launchers that reference a known
        # SaaS provider URL.  Localhost URLs (127.0.0.1, localhost,
        # 0.0.0.0) are always allowed.
        lcmd = launch.get("cmd", "")
        if isinstance(lcmd, str):
            saas_match = _SAAS_HOST_RE.search(lcmd)
            has_localhost = any(
                host in lcmd
                for host in ("127.0.0.1", "localhost", "0.0.0.0")
            )
            if saas_match and not has_localhost:
                errors.append(
                    f"{tool_id}: launcher.cmd references a SaaS "
                    f"provider URL ({saas_match.group(0)!r}) without "
                    f"a localhost override.  AI-LSC policy requires "
                    f"localhost-only endpoints.  See CHANGES.md → "
                    f"'SaaS-only tool blocklist' for the rationale."
                )

    # Filesystem spec (optional but validated if present)
    fs = entry.get("filesystem", {})
    if isinstance(fs, dict):
        unknown_fs = set(fs.keys()) - _OPTIONAL_FILESYSTEM_FIELDS
        if unknown_fs:
            errors.append(
                f"{tool_id}: unknown filesystem fields {sorted(unknown_fs)}"
            )

    # deps must be a list of strings
    deps = entry.get("deps")
    if not isinstance(deps, list):
        errors.append(f"{tool_id}: deps is not a list")
    else:
        non_str = [d for d in deps if not isinstance(d, str)]
        if non_str:
            errors.append(
                f"{tool_id}: deps contains non-string items: {non_str}"
            )

    # flags must be a dict of bools declaring every required key.
    flags = entry.get("flags", {})
    if not isinstance(flags, dict):
        errors.append(f"{tool_id}: flags is not a dict")
    else:
        non_bool = {k: v for k, v in flags.items()
                    if not isinstance(v, bool)}
        if non_bool:
            errors.append(
                f"{tool_id}: flags contain non-bool values: "
                f"{list(non_bool.keys())}"
            )
        # H-15: enforce the full 8-key schema.
        missing_flags = _REQUIRED_FLAG_KEYS - flags.keys()
        if missing_flags:
            errors.append(
                f"{tool_id}: flags missing required keys: "
                f"{sorted(missing_flags)}"
            )
        unknown_flags = set(flags.keys()) - _REQUIRED_FLAG_KEYS
        if unknown_flags:
            errors.append(
                f"{tool_id}: flags contain unknown keys: "
                f"{sorted(unknown_flags)}"
            )

    # license must be a non-empty string matching a known SPDX ID in
    # the license catalog.  Unknown SPDX IDs are a warning (the gate
    # treats them as Proprietary) but missing/empty license is an error.
    license_spdx = entry.get("license", "")
    if not license_spdx or not isinstance(license_spdx, str):
        errors.append(
            f"{tool_id}: missing or invalid 'license' field — "
            f"must be an SPDX ID (e.g. 'MIT', 'Apache-2.0', "
            f"'GPL-3.0', 'Proprietary', 'Anthropic-ToS').  See "
            f"registry/licenses.py CATALOG for the full list."
        )
    elif license_spdx not in _KNOWN_LICENSE_SPDX_IDS:
        errors.append(
            f"{tool_id}: license {license_spdx!r} is not in the "
            f"license catalog (registry/licenses.py).  Add it there "
            f"first so the LicenseGate knows its category and summary."
        )

    return errors


def validate_registry(data: dict[str, Any]) -> list[str]:
    """Validate an entire registry dict.

    Returns a (possibly empty) list of human-readable error strings.
    An empty list means the registry is valid.
    """
    errors: list[str] = []
    for tool_id, entry in data.items():
        if not isinstance(entry, dict):
            errors.append(f"{tool_id}: entry is not a dict ({type(entry)})")
            continue
        errors.extend(_check_entry(tool_id, entry))
    return errors
