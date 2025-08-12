"""Base command class for AI Admin Server."""

from typing import Any, Dict
from abc import ABC, abstractmethod
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class AIAdminCommand(Command):
    """Base class for AI Admin server commands.
    
    This class provides a foundation for creating custom commands
    that can be automatically discovered by the server.
    """
    
    # Override this in subclasses
    name: str = "ai_admin_command"
    
    @abstractmethod
    async def execute(self, **kwargs) -> SuccessResult:
        """Execute the command.
        
        Args:
            **kwargs: Command parameters
            
        Returns:
            Command execution result
        """
        pass
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters.
        
        Returns:
            JSON schema for parameters
        """
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True
        }


# Backward compatibility
EmptyCommand = AIAdminCommand 