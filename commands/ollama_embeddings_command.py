from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError, InternalError
"""Ollama embeddings command for getting text embeddings.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter
from ai_admin.ollama.ollama_client import OllamaClient


class OllamaEmbeddingsCommand(BaseUnifiedCommand):
    """Command to get embeddings from Ollama models."""

    name = "ollama_embeddings"
    
    def __init__(self):
        """Initialize Ollama embeddings command."""
        super().__init__()
        self.ollama_security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        model: str,
        prompt: str,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        use_queue: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama embeddings command.
        
        Args:
            model: Model name to use for embeddings
            prompt: Input prompt for embeddings
            base_url: Ollama server base URL
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            repeat_penalty: Repeat penalty parameter
            use_queue: Whether to use queue for processing
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with embeddings
        """
        # Use unified security approach
        return await super().execute(
            model=model,
            prompt=prompt,
            base_url=base_url,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            use_queue=use_queue,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama embeddings command."""
        return "ollama:embeddings"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama embeddings command logic."""
        return await self._get_embeddings(**kwargs)

    async def _get_embeddings(
        self,
        model: str,
        prompt: str,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        use_queue: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get embeddings from Ollama model."""
        try:
            server_url = base_url or "http://localhost:11434"
            
            # Build options dictionary
            options = {}
            if temperature is not None:
                options["temperature"] = temperature
            if top_p is not None:
                options["top_p"] = top_p
            if top_k is not None:
                options["top_k"] = top_k
            if repeat_penalty is not None:
                options["repeat_penalty"] = repeat_penalty
            
            async with OllamaClient(base_url=server_url) as client:
                result = await client.get_embeddings(
                    model=model,
                    prompt=prompt,
                    options=options if options else None,
                )
                
                return {
                    "message": f"Embeddings generated with model '{model}'",
                    "model": model,
                    "prompt": prompt,
                    "server_url": server_url,
                    "embeddings": result.get("embedding", []),
                    "embedding_length": len(result.get("embedding", [])),
                    "result": result,
                    "status": "completed",
                }

        except Exception as e:
            raise CustomError(f"Ollama embeddings generation failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Ollama embeddings command parameters."""
        return {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "Model name to use for embeddings",
                },
                "prompt": {
                    "type": "string",
                    "description": "Input prompt for embeddings",
                },
                "base_url": {
                    "type": "string",
                    "description": "Ollama server base URL",
                    "default": "http://localhost:11434",
                },
                "temperature": {
                    "type": "number",
                    "description": "Sampling temperature",
                    "minimum": 0.0,
                    "maximum": 2.0,
                },
                "top_p": {
                    "type": "number",
                    "description": "Top-p sampling parameter",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "top_k": {
                    "type": "integer",
                    "description": "Top-k sampling parameter",
                    "minimum": 1,
                },
                "repeat_penalty": {
                    "type": "number",
                    "description": "Repeat penalty parameter",
                    "minimum": 0.0,
                },
                "use_queue": {
                    "type": "boolean",
                    "description": "Whether to use queue for processing",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["model", "prompt"],
            "additionalProperties": False,
        }
