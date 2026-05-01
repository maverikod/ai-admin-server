"""
Compatibility command for MCP Proxy registration.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

from typing import Any, Dict

from mcp_proxy_adapter.commands.base import Command, CommandResult
from mcp_proxy_adapter.commands.command_registry import registry


class GetMethodsCommand(Command):
    """Return registered command metadata for legacy proxy checks."""

    name = "get_methods"
    descr = "Return available command methods for proxy discovery"

    async def execute(self, **kwargs: Any) -> CommandResult:
        """Return all command metadata keyed by command name."""
        commands_info: Dict[str, Any] = registry.get_all_commands_info().get(
            "commands", {}
        )
        return CommandResult(success=True, data=commands_info)

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Schema for get_methods command (no required parameters)."""
        return {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": True,
        }
