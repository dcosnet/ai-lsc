"""
AI-LSC — Centralised path definitions.

Every path in the application is derived from ``BASE_DIR``
using :mod:`pathlib`.  Import these in UI and orchestration code
instead of constructing paths with ``os.path.join`` ad-hoc.
"""

from __future__ import annotations

from pathlib import Path

from ai_lsc.constants import BASE_DIR, REQUIRED_DIRS


def build_path_tree(base_dir: str | Path | None = None) -> dict[str, Path]:
    """Return a dict of well-known absolute paths under *base_dir*.

    The dict keys match the attribute names that ``AILocalStackControl``
    currently assigns in ``__init__``, so migrating consumers is a
    mechanical find-and-replace.

    Parameters
    ----------
    base_dir:
        Override the default ``BASE_DIR``.  Useful for tests.

    Returns
    -------
    dict[str, Path]
        Example::

            {
                "base_dir":      Path("/mnt/AI"),
                "tools_root":   Path("/mnt/AI/tools"),
                "models_root":  Path("/mnt/AI/models"),
                "logs_root":     Path("/mnt/AI/logs"),
                "skills_root":   Path("/mnt/AI/skills"),
                "datasets_root": Path("/mnt/AI/datasets"),
                "config_root":   Path("/mnt/AI/config"),
                "workspaces_root": Path("/mnt/AI/workspaces"),
                "exports_root":  Path("/mnt/AI/exports"),
                "registry_root": Path("/mnt/AI/registry"),
            }
    """
    root = Path(base_dir) if base_dir is not None else Path(BASE_DIR)
    return {
        "base_dir":         root,
        "tools_root":       root / "tools",
        "models_root":      root / "models",
        "logs_root":        root / "logs",
        "skills_root":      root / "skills",
        "datasets_root":    root / "datasets",
        "config_root":      root / "config",
        "workspaces_root":  root / "workspaces",
        "exports_root":     root / "exports",
        "registry_root":    root / "registry",
    }


def resolve_launcher_cmd(
    cmd_template: str,
    base_dir: str | Path | None = None,
    port: int | None = None,
    model_arg: str = "",
) -> str:
    """Resolve ``{placeholder}`` tokens in a launcher command template.

    Recognised placeholders (case-sensitive):
        ``{port}``, ``{base_dir}``, ``{tools_root}``,
        ``{models_root}``, ``{workspaces_root}``, ``{model_arg}``
    """
    paths = build_path_tree(base_dir)
    return (
        cmd_template
        .replace("{port}", str(port or ""))
        .replace("{base_dir}", str(paths["base_dir"]))
        .replace("{tools_root}", str(paths["tools_root"]))
        .replace("{models_root}", str(paths["models_root"]))
        .replace("{workspaces_root}", str(paths["workspaces_root"]))
        .replace("{model_arg}", model_arg)
    )
