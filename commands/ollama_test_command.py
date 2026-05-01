from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError, InternalError
"""Ollama test command for testing connection to Ollama server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter
from ai_admin.ollama.ollama_client import OllamaClient


class OllamaTestCommand(BaseUnifiedCommand):
    """Command to test connection to Ollama server."""

    name = "ollama_test"
    
    def __init__(self):
        """Initialize Ollama test command."""
        super().__init__()
        self.ollama_security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama test command.
        
        Args:
            base_url: Ollama server base URL
            timeout: Connection timeout in seconds
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with connection test information
        """
        # Use unified security approach
        return await super().execute(
            base_url=base_url,
            timeout=timeout,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama test command."""
        return "ollama:test"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama test command logic."""
        return await self._test_connection(**kwargs)

    async def _test_connection(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Dict[str, Any]:
        """Test connection to Ollama server."""
        try:
            server_url = base_url or "http://localhost:11434"
            
            async with OllamaClient(base_url=server_url, timeout=timeout) as client:
                result = await client.test_connection()
                
                return {
                    "message": f"Ollama connection test completed",
                    "server_url": server_url,
                    "timeout": timeout,
                    "result": result,
                    "status": "completed",
                }

        except Exception as e:
            raise CustomError(f"Ollama connection test failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Ollama test command parameters."""
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "description": "Ollama server base URL",
                    "default": "http://localhost:11434",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Connection timeout in seconds",
                    "default": 30,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
