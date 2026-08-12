"""AI-LSC UI pages sub-package.

Re-exports every page widget so consumers can import from a single
location::

    from ai_lsc.ui.pages import ServiceRow, ChatbotConsole
"""

try:
    from ai_lsc.ui.pages.chatbot_console import ChatbotConsole  # noqa: F401
    from ai_lsc.ui.pages.db_manager import DatabaseManager  # noqa: F401
    from ai_lsc.ui.pages.code_analysis_tab import CodeAnalysisTab  # noqa: F401
    from ai_lsc.ui.pages.container_stacks_tab import ContainerStacksTab  # noqa: F401
    from ai_lsc.ui.pages.datasets_tab import DatasetsTab  # noqa: F401
    from ai_lsc.ui.pages.git_worktree_tab import GitWorktreeTab  # noqa: F401
    from ai_lsc.ui.pages.infrastructure_layer_page import (  # noqa: F401
        InfrastructureLayerPage,
    )
    from ai_lsc.ui.pages.service_row import ServiceRow  # noqa: F401
    from ai_lsc.ui.pages.settings_page import SettingsPage  # noqa: F401
    from ai_lsc.ui.pages.skills_console import SkillsConsole  # noqa: F401
    from ai_lsc.ui.pages.ipc_stack_tab import IpcStackTab  # noqa: F401
    from ai_lsc.ui.pages.tools_tab import ToolsTab  # noqa: F401
except ImportError:
    ServiceRow = None  # type: ignore[assignment, misc]
    SkillsConsole = None  # type: ignore[assignment, misc]
    DatasetsTab = None  # type: ignore[assignment, misc]
    ChatbotConsole = None  # type: ignore[assignment, misc]
    ToolsTab = None  # type: ignore[assignment, misc]
    DatabaseManager = None  # type: ignore[assignment, misc]
    IpcStackTab = None  # type: ignore[assignment, misc]
    ContainerStacksTab = None  # type: ignore[assignment, misc]
    InfrastructureLayerPage = None  # type: ignore[assignment, misc]
    SettingsPage = None  # type: ignore[assignment, misc]
    GitWorktreeTab = None  # type: ignore[assignment, misc]
    CodeAnalysisTab = None  # type: ignore[assignment, misc]

__all__ = [
    "ServiceRow",
    "SkillsConsole",
    "DatasetsTab",
    "ChatbotConsole",
    "ToolsTab",
    "DatabaseManager",
    "IpcStackTab",
    "ContainerStacksTab",
    "InfrastructureLayerPage",
    "SettingsPage",
    "GitWorktreeTab",
    "CodeAnalysisTab",
]
