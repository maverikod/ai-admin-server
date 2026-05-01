"""Canonical MCP adapter custom command registration for ai_admin.

Registers all command classes exported in ai_admin.commands.__all__ via
register_custom_commands_hook (same pattern as code_analysis.hooks).
"""
from __future__ import annotations

import inspect
import logging
from typing import Any

from mcp_proxy_adapter.commands.hooks import register_custom_commands_hook

logger = logging.getLogger(__name__)


def register_ai_admin_commands(registry: Any) -> None:
    """Register ai_admin command classes on the global MCP command registry."""
    import ai_admin.commands as cmdmod

    for name in getattr(cmdmod, "__all__", ()):
        try:
            obj = getattr(cmdmod, name, None)
        except Exception as exc:  # noqa: BLE001
            logger.debug("skip %s: getattr failed: %s", name, exc)
            continue
        if not inspect.isclass(obj):
            continue
        if not name.endswith("Command"):
            continue
        try:
            registry.register(obj, "custom")
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed to register %s: %s", name, exc)


register_custom_commands_hook(register_ai_admin_commands)
