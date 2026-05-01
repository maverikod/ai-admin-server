from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError, NetworkError
"""Ollama remove command for removing models.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import aiohttp

from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter

class OllamaRemoveCommand(BaseUnifiedCommand):
    """Command to remove Ollama models."""

    name = "ollama_remove"
    
    def __init__(self):
        """Initialize Ollama remove command."""
        super().__init__()
        self.security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        action: str = "remove",
        model_name: str = "",
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama remove command with unified security.
        
        Args:
            action: Remove action (remove, list)
            model_name: Name of the model to remove
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with remove information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            model_name=model_name,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama remove command."""
        return "ollama:remove"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama remove command logic."""
        action = kwargs.get("action", "remove")
        
        if action == "remove":
            return await self._remove_model(**kwargs)
        elif action == "list":
            return await self._list_models(**kwargs)
        else:
            raise CustomError(f"Unknown remove action: {action}")

    async def _remove_model(
        self,
        model_name: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        """Remove a model via API."""
        try:
            if not model_name:
                raise CustomError("Model name is required for remove action")

            server_url = "http://localhost:11434"
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{server_url}/api/delete",
                    json={"name": model_name},
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "message": f"Successfully removed model '{model_name}'",
                            "action": "remove",
                            "model_name": model_name,
                            "result": result,
                        }
                    else:
                        error_text = await response.text()
                        raise CustomError(f"Remove failed with status {response.status}: {error_text}")

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during remove: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama remove command failed: {str(e)}")

    async def _list_models(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """List available models."""
        try:
            server_url = "http://localhost:11434"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{server_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        models = result.get("models", [])
                        return {
                            "message": f"Found {len(models)} models",
                            "action": "list",
                            "models": models,
                            "count": len(models),
                        }
                    else:
                        error_text = await response.text()
                        raise CustomError(f"List failed with status {response.status}: {error_text}")

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during list: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama list command failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Ollama remove command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Remove action (remove, list)",
                    "default": "remove",
                    "enum": ["remove", "list"],
                },
                "model_name": {
                    "type": "string",
                    "description": "Name of the model to remove",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }