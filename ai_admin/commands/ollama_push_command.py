from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError, NetworkError
"""Ollama push command for pushing models to registry.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import aiohttp

from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter

class OllamaPushCommand(BaseUnifiedCommand):
    """Command to push Ollama models to registry."""

    name = "ollama_push"
    
    def __init__(self):
        """Initialize Ollama push command."""
        super().__init__()
        self.security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        action: str = "push",
        model_name: str = "",
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama push command with unified security.
        
        Args:
            action: Push action (push, list)
            model_name: Name of the model to push
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with push information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            model_name=model_name,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama push command."""
        return "ollama:push"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama push command logic."""
        action = kwargs.get("action", "push")
        
        if action == "push":
            return await self._push_model(**kwargs)
        elif action == "list":
            return await self._list_models(**kwargs)
        else:
            raise CustomError(f"Unknown push action: {action}")

    async def _push_model(
        self,
        model_name: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        """Push a model to registry via API."""
        try:
            if not model_name:
                raise CustomError("Model name is required for push action")

            server_url = "http://localhost:11434"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server_url}/api/push",
                    json={"name": model_name},
                    timeout=aiohttp.ClientTimeout(total=600),  # 10 minutes for large models
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "message": f"Successfully pushed model '{model_name}' to registry",
                            "action": "push",
                            "model_name": model_name,
                            "result": result,
                        }
                    else:
                        error_text = await response.text()
                        raise CustomError(f"Push failed with status {response.status}: {error_text}")

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during push: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama push command failed: {str(e)}")

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
        """Get JSON schema for Ollama push command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Push action (push, list)",
                    "default": "push",
                    "enum": ["push", "list"],
                },
                "model_name": {
                    "type": "string",
                    "description": "Name of the model to push",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }