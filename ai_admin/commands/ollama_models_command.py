from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError, NetworkError
"""Ollama models command for managing models.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import aiohttp

from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter
from ai_admin.ollama.ollama_client import OllamaClient

class OllamaModelsCommand(BaseUnifiedCommand):
    """Command to manage Ollama models."""

    name = "ollama_models"
    
    def __init__(self):
        """Initialize Ollama models command."""
        super().__init__()
        self.ollama_security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        action: str = "list",
        model_name: Optional[str] = None,
        prompt: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        ssl_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama models command.
        
        Args:
            action: Models action (list, pull, remove, show)
            model_name: Name of the model
            prompt: Prompt for model interaction
            user_roles: List of user roles for security validation
            ssl_config: SSL configuration
            
        Returns:
            Success result with models information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            model_name=model_name,
            prompt=prompt,
            user_roles=user_roles,
            ssl_config=ssl_config,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama models command."""
        return "ollama:models"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama models command logic."""
        action = kwargs.get("action", "list")
        
        if action == "list":
            return await self._list_models(**kwargs)
        elif action == "pull":
            return await self._pull_model(**kwargs)
        elif action == "remove":
            return await self._remove_model(**kwargs)
        elif action == "show":
            return await self._show_model(**kwargs)
        else:
            raise CustomError(f"Unknown models action: {action}")

    async def _list_models(
        self,
        base_url: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """List available models."""
        try:
            server_url = base_url or "http://localhost:11434"
            
            async with OllamaClient(base_url=server_url) as client:
                models = await client.list_models()
                
                # Convert OllamaModel objects to dictionaries
                models_data = []
                for model in models:
                    models_data.append({
                        "name": model.name,
                        "size": model.size,
                        "digest": model.digest,
                        "modified_at": model.modified_at,
                        "family": model.family,
                        "format": model.format,
                        "families": model.families,
                        "parameter_size": model.parameter_size,
                        "quantization_level": model.quantization_level,
                    })
                
                return {
                    "message": f"Found {len(models_data)} models",
                    "action": "list",
                    "models": models_data,
                    "count": len(models_data),
                    "server_url": server_url,
                }

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during models list: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama models list failed: {str(e)}")

    async def _pull_model(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        insecure: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Pull a model from registry."""
        try:
            if not model_name:
                raise CustomError("Model name is required for pull action")

            server_url = base_url or "http://localhost:11434"
            
            async with OllamaClient(base_url=server_url) as client:
                # Collect all progress updates
                progress_updates = []
                async for progress in client.pull_model(model_name, insecure=insecure, stream=True):
                    progress_updates.append(progress)
                
                return {
                    "message": f"Successfully pulled model '{model_name}'",
                    "action": "pull",
                    "model_name": model_name,
                    "server_url": server_url,
                    "insecure": insecure,
                    "progress_updates": progress_updates,
                    "status": "completed",
                }

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during model pull: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama model pull failed: {str(e)}")

    async def _remove_model(
        self,
        model_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Remove a model."""
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
                        raise CustomError(f"Model remove failed with status {response.status}: {error_text}")

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during model remove: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama model remove failed: {str(e)}")

    async def _show_model(
        self,
        model_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Show model information."""
        try:
            if not model_name:
                raise CustomError("Model name is required for show action")

            server_url = "http://localhost:11434"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server_url}/api/show",
                    json={"name": model_name},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "message": f"Model information for '{model_name}'",
                            "action": "show",
                            "model_name": model_name,
                            "model_info": result,
                        }
                    else:
                        error_text = await response.text()
                        raise CustomError(f"Model show failed with status {response.status}: {error_text}")

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during model show: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama model show failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Ollama models command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Models action (list, pull, remove, show)",
                    "default": "list",
                    "enum": ["list", "pull", "remove", "show"],
                },
                "model_name": {
                    "type": "string",
                    "description": "Name of the model",
                },
                "prompt": {
                    "type": "string",
                    "description": "Prompt for model interaction",
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