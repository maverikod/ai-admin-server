from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Ollama status command for checking server status.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import aiohttp

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter

class OllamaStatusCommand(BaseUnifiedCommand):
    """Command to check Ollama server status."""

    name = "ollama_status"
    
    def __init__(self):
        """Initialize Ollama status command."""
        super().__init__()
        self.ollama_security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        action: str = "status",
        server: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        ssl_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama status check.
        
        Args:
            action: Status action (status, health, version)
            server: Server URL to check
            user_roles: List of user roles for security validation
            ssl_config: SSL configuration
            
        Returns:
            Success result with status information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            server=server,
            user_roles=user_roles,
            ssl_config=ssl_config,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama status command."""
        return "ollama:status"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama status command logic."""
        action = kwargs.get("action", "status")
        
        if action == "status":
            return await self._check_status(**kwargs)
        elif action == "health":
            return await self._check_health(**kwargs)
        elif action == "version":
            return await self._get_version(**kwargs)
        else:
            raise CustomError(f"Unknown status action: {action}")

    async def _check_status(
        self,
        server: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Check Ollama server status."""
        try:
            server_url = server or "http://localhost:11434"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{server_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        models = result.get("models", [])
                        return {
                            "message": f"Ollama server is running at {server_url}",
                            "action": "status",
                            "server": server_url,
                            "status": "running",
                            "models_count": len(models),
                            "models": models,
                        }
                    else:
                        return {
                            "message": f"Ollama server at {server_url} returned status {response.status}",
                            "action": "status",
                            "server": server_url,
                            "status": "error",
                            "error": f"HTTP {response.status}",
                        }

        except aiohttp.ClientError as e:
            return {
                "message": f"Ollama server at {server_url} is not accessible",
                "action": "status",
                "server": server_url,
                "status": "offline",
                "error": str(e),
            }
        except CustomError as e:
            raise CustomError(f"Ollama status check failed: {str(e)}")

    async def _check_health(
        self,
        server: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Check Ollama server health."""
        try:
            server_url = server or "http://localhost:11434"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{server_url}/api/ps",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        active_models = result.get("models", [])
                        return {
                            "message": f"Ollama server health check passed",
                            "action": "health",
                            "server": server_url,
                            "health": "healthy",
                            "active_models": len(active_models),
                            "models": active_models,
                        }
                    else:
                        return {
                            "message": f"Ollama server health check failed",
                            "action": "health",
                            "server": server_url,
                            "health": "unhealthy",
                            "error": f"HTTP {response.status}",
                        }

        except aiohttp.ClientError as e:
            return {
                "message": f"Ollama server health check failed",
                "action": "health",
                "server": server_url,
                "health": "unreachable",
                "error": str(e),
            }
        except CustomError as e:
            raise CustomError(f"Ollama health check failed: {str(e)}")

    async def _get_version(
        self,
        server: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get Ollama server version."""
        try:
            server_url = server or "http://localhost:11434"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{server_url}/api/version",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "message": f"Ollama server version information",
                            "action": "version",
                            "server": server_url,
                            "version": result.get("version", "unknown"),
                            "details": result,
                        }
                    else:
                        return {
                            "message": f"Failed to get Ollama version",
                            "action": "version",
                            "server": server_url,
                            "version": "unknown",
                            "error": f"HTTP {response.status}",
                        }

        except aiohttp.ClientError as e:
            return {
                "message": f"Failed to get Ollama version",
                "action": "version",
                "server": server_url,
                "version": "unknown",
                "error": str(e),
            }
        except CustomError as e:
            raise CustomError(f"Ollama version check failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Ollama status command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Status action (status, health, version)",
                    "default": "status",
                    "enum": ["status", "health", "version"],
                },
                "server": {
                    "type": "string",
                    "description": "Server URL to check",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
                "ssl_config": {
                    "type": "object",
                    "description": "SSL configuration",
                },
            },
            "additionalProperties": False,
        }