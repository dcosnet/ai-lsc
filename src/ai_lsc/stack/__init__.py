"""AI-LSC stack sub-package.

Provides the stack wiring topology — static definitions of how each
tool connects to other tools at the API/protocol level.
"""

from ai_lsc.stack.connections import (
    CONNECTIONS_SCHEMA_VERSION,
    Connection,
    EngineeringContext,
    StackWiring,
    STACK_WIRINGS,
    ToolInterface,
    _CUDA_INTERFACE,
    get_consumers,
    get_providers,
    get_topology,
    validate_wiring,
)

__all__ = [
    "CONNECTIONS_SCHEMA_VERSION",
    "Connection",
    "EngineeringContext",
    "StackWiring",
    "STACK_WIRINGS",
    "ToolInterface",
    "_CUDA_INTERFACE",
    "get_consumers",
    "get_providers",
    "get_topology",
    "validate_wiring",
]