"""
Test command for discovery verification.
"""

from typing import Dict, Any
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult


class TestDiscoveryCommand(Command):
    """Test command to verify auto-discovery."""
    
    name = "test_discovery"
    
    async def execute(self, **kwargs) -> SuccessResult:
        """Execute test discovery command.
        
        Args:
            **kwargs: Additional parameters
            
        Returns:
            SuccessResult: Test result
        """
        return SuccessResult(data={
            "message": "Test discovery command executed successfully",
            "command_name": self.name,
            "discovery_working": True,
            "timestamp": "2025-08-12T21:05:00Z"
        })
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters.
        
        Returns:
            Dict[str, Any]: JSON schema
        """
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True
        } 