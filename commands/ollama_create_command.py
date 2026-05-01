from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError, InternalError
"""Ollama create command for creating models from Modelfile.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter
from ai_admin.ollama.ollama_client import OllamaClient


class OllamaCreateCommand(BaseUnifiedCommand):
    """Command to create Ollama models from Modelfile."""

    name = "ollama_create"
    
    def __init__(self):
        """Initialize Ollama create command."""
        super().__init__()
        self.ollama_security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        model_name: str,
        modelfile: str,
        base_url: Optional[str] = None,
        stream: bool = True,
        use_queue: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama create command.
        
        Args:
            model_name: Name for the new model
            modelfile: Modelfile content
            base_url: Ollama server base URL
            stream: Whether to stream progress
            use_queue: Whether to use queue for processing
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with model creation information
        """
        # Use unified security approach
        return await super().execute(
            model_name=model_name,
            modelfile=modelfile,
            base_url=base_url,
            stream=stream,
            use_queue=use_queue,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama create command."""
        return "ollama:create"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama create command logic."""
        return await self._create_model(**kwargs)

    async def _create_model(
        self,
        model_name: str,
        modelfile: str,
        base_url: Optional[str] = None,
        stream: bool = True,
        use_queue: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create model from Modelfile."""
        try:
            server_url = base_url or "http://localhost:11434"
            
            async with OllamaClient(base_url=server_url) as client:
                if stream:
                    # Stream progress updates
                    progress_updates = []
                    async for progress in client.create_model(
                        model_name=model_name,
                        modelfile=modelfile,
                        stream=True,
                    ):
                        progress_updates.append(progress)
                    
                    return {
                        "message": f"Model '{model_name}' created successfully (streamed)",
                        "model_name": model_name,
                        "server_url": server_url,
                        "stream": True,
                        "progress_updates": progress_updates,
                        "status": "completed",
                    }
                else:
                    # Collect all progress updates
                    progress_updates = []
                    async for progress in client.create_model(
                        model_name=model_name,
                        modelfile=modelfile,
                        stream=True,
                    ):
                        progress_updates.append(progress)
                    
                    return {
                        "message": f"Model '{model_name}' created successfully",
                        "model_name": model_name,
                        "server_url": server_url,
                        "stream": False,
                        "progress_updates": progress_updates,
                        "status": "completed",
                    }

        except Exception as e:
            raise CustomError(f"Ollama model creation failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Ollama create command parameters."""
        return {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "description": "Name for the new model",
                },
                "modelfile": {
                    "type": "string",
                    "description": "Modelfile content",
                },
                "base_url": {
                    "type": "string",
                    "description": "Ollama server base URL",
                    "default": "http://localhost:11434",
                },
                "stream": {
                    "type": "boolean",
                    "description": "Whether to stream progress",
                    "default": True,
                },
                "use_queue": {
                    "type": "boolean",
                    "description": "Whether to use queue for processing",
                    "default": True,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["model_name", "modelfile"],
            "additionalProperties": False,
        }
