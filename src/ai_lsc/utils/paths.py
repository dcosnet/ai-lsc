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
                "base_dir":         Path("/mnt/AI"),
                "tools_root":       Path("/mnt/AI/tools"),         # standalone CLI utilities
                "runtime_root":     Path("/mnt/AI/runtime"),       # native binaries + per-tool venvs
                "models_root":      Path("/mnt/AI/models"),        # parent of hot/ and cold/
                "models_hot":       Path("/mnt/AI/models/hot"),    # active weights (SSD)
                "models_cold":      Path("/mnt/AI/models/cold"),   # archived weights (HDD)
                "corpus_root":      Path("/mnt/AI/corpus"),        # parent of hot/ and cold/
                "datasets_root":    Path("/mnt/AI/datasets"),      # parent of wordlists/, huggingface/, github/
                "pipelines_root":   Path("/mnt/AI/pipelines"),     # ETL / chunking / routing scripts
                "configs_root":     Path("/mnt/AI/configs"),     # app state + templated configs
                "registry_root":    Path("/mnt/AI/registry"),      # app-internal: ecosystem.json + manifests/
                "agents_root":      Path("/mnt/AI/agents"),        # configs and chains for autonomous actors
                "skills_root":      Path("/mnt/AI/skills"),        # 3rd-party integrations and tool wrappers
                "projects_root":    Path("/mnt/AI/projects"),      # parent of active/, labs/, vault/
                "blueprints_root":  Path("/mnt/AI/blueprints"),    # Dockerfiles / build contexts for Podman exports
                "workspaces_root":  Path("/mnt/AI/workspaces"),    # Jupyter, OpenNotebook, etc.
                "dashboards_root":  Path("/mnt/AI/dashboards"),    # web UIs (Dashy, Open-WebUI, Hermes WebUI, etc.)
                "exports_root":     Path("/mnt/AI/exports"),       # parent of oci-images/
                "scripts_root":     Path("/mnt/AI/scripts"),       # system admin / maintenance automation
                "logs_root":        Path("/mnt/AI/logs"),
                "backends_root":    Path("/mnt/AI/backends"),      # S3/MinIO/Ceph connection profiles
                "distfiles_root":   Path("/mnt/AI/distfiles"),     # permanent local mirror of source tarballs
                "config_root":      Path("/mnt/AI/configs"),     # app state + templated configs
            }
    """
    root = Path(base_dir) if base_dir is not None else Path(BASE_DIR)
    return {
        "base_dir":         root,
        "tools_root":       root / "tools",
        "runtime_root":     root / "runtime",
        "models_root":      root / "models",
        "models_hot":       root / "models" / "hot",
        "models_cold":      root / "models" / "cold",
        "corpus_root":      root / "corpus",
        "datasets_root":    root / "datasets",
        "pipelines_root":   root / "pipelines",
        "registry_root":    root / "registry",
        "agents_root":      root / "agents",
        "skills_root":      root / "skills",
        "projects_root":    root / "projects",
        "blueprints_root":  root / "blueprints",
        "workspaces_root":  root / "workspaces",
        "dashboards_root":  root / "dashboards",
        "exports_root":     root / "exports",
        "scripts_root":     root / "scripts",
        "logs_root":        root / "logs",
        "backends_root":    root / "backends",
        "distfiles_root":   root / "distfiles",
        "configs_root":     root / "configs",
        # App-state + templated app configs (controller_config.json,
        # pipeline_state.json, license_approvals.json).  Per-tool config
        # subdirs (configs/<tool>/) are created on demand by
        # InstallerManager.  Legacy installs used base_dir/config or
        # base_dir root — main_window migrates those on startup.
        "config_root":      root / "configs",
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
