from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError, InternalError
"""Ollama copy command for copying models.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import aiohttp

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter

class OllamaCopyCommand(BaseUnifiedCommand):
    """Command to copy Ollama models."""

    name = "ollama_copy"
    
    def __init__(self):
        """Initialize Ollama copy command."""
        super().__init__()
        self.security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        action: str = "copy",
        source: str = "",
        destination: str = "",
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama copy command with unified security.
        
        Args:
            action: Copy action (copy, list)
            source: Source model name
            destination: Destination model name
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with copy information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            source=source,
            destination=destination,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama copy command."""
        return "ollama:copy"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama copy command logic."""
        action = kwargs.get("action", "copy")
        
        if action == "copy":
            return await self._copy_model(**kwargs)
        elif action == "list":
            return await self._list_models(**kwargs)
        else:
            raise CustomError(f"Unknown copy action: {action}")

    async def _copy_model(
        self,
        source: str = "",
        destination: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        """Copy a model via API."""
        try:
            if not source or not destination:
                raise CustomError("Source and destination model names are required")

            server_url = "http://localhost:11434"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server_url}/api/copy",
                    json={"source": source, "destination": destination},
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "message": f"Successfully copied model '{source}' to '{destination}'",
                            "action": "copy",
                            "source": source,
                            "destination": destination,
                            "result": result,
                        }
                    else:
                        error_text = await response.text()
                        raise CustomError(f"Copy failed with status {response.status}: {error_text}")

        except aiohttp.ClientError as e:
            raise InternalError(f"Network error during copy: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama copy command failed: {str(e)}")

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
            raise InternalError(f"Network error during list: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama list command failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Ollama copy command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Copy action (copy, list)",
                    "default": "copy",
                    "enum": ["copy", "list"],
                },
                "source": {
                    "type": "string",
                    "description": "Source model name",
                },
                "destination": {
                    "type": "string",
                    "description": "Destination model name",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }