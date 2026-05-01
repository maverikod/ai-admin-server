from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError, NetworkError
"""Ollama memory command for managing model memory.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import aiohttp

from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter

class OllamaMemoryCommand(BaseUnifiedCommand):
    """Command to manage Ollama model memory."""

    name = "ollama_memory"
    
    def __init__(self):
        """Initialize Ollama memory command."""
        super().__init__()
        self.ollama_security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        action: str = "show",
        model_name: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        ssl_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama memory management.
        
        Args:
            action: Memory action (show, clear, stats)
            model_name: Name of the model
            user_roles: List of user roles for security validation
            ssl_config: SSL configuration
            
        Returns:
            Success result with memory information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            model_name=model_name,
            user_roles=user_roles,
            ssl_config=ssl_config,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama memory command."""
        return "ollama:memory"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama memory command logic."""
        action = kwargs.get("action", "show")
        
        if action == "show":
            return await self._show_memory(**kwargs)
        elif action == "clear":
            return await self._clear_memory(**kwargs)
        elif action == "stats":
            return await self._get_memory_stats(**kwargs)
        else:
            raise CustomError(f"Unknown memory action: {action}")

    async def _show_memory(
        self,
        model_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Show memory usage for a model."""
        try:
            server_url = "http://localhost:11434"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{server_url}/api/ps",
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        models = result.get("models", [])
                        
                        if model_name:
                            # Filter for specific model
                            models = [m for m in models if m.get("name") == model_name]
                        
                        return {
                            "message": f"Memory usage for {len(models)} model(s)",
                            "action": "show",
                            "model_name": model_name,
                            "models": models,
                            "count": len(models),
                        }
                    else:
                        error_text = await response.text()
                        raise CustomError(f"Memory show failed with status {response.status}: {error_text}")

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during memory show: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama memory show failed: {str(e)}")

    async def _clear_memory(
        self,
        model_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Clear memory for a model."""
        try:
            server_url = "http://localhost:11434"
            
            # Clear memory by stopping the model
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{server_url}/api/generate",
                    json={"model": model_name} if model_name else {},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status in [200, 204]:
                        return {
                            "message": f"Successfully cleared memory for model '{model_name or 'all'}'",
                            "action": "clear",
                            "model_name": model_name,
                        }
                    else:
                        error_text = await response.text()
                        raise CustomError(f"Memory clear failed with status {response.status}: {error_text}")

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during memory clear: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama memory clear failed: {str(e)}")

    async def _get_memory_stats(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            server_url = "http://localhost:11434"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{server_url}/api/ps",
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        models = result.get("models", [])
                        
                        total_memory = sum(m.get("size", 0) for m in models)
                        total_models = len(models)
                        
                        return {
                            "message": f"Memory statistics for {total_models} models",
                            "action": "stats",
                            "total_models": total_models,
                            "total_memory": total_memory,
                            "models": models,
                        }
                    else:
                        error_text = await response.text()
                        raise CustomError(f"Memory stats failed with status {response.status}: {error_text}")

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during memory stats: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama memory stats failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Ollama memory command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Memory action (show, clear, stats)",
                    "default": "show",
                    "enum": ["show", "clear", "stats"],
                },
                "model_name": {
                    "type": "string",
                    "description": "Name of the model",
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