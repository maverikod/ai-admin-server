from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError, InternalError
"""Ollama generate command for text generation.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter
from ai_admin.ollama.ollama_client import OllamaClient


class OllamaGenerateCommand(BaseUnifiedCommand):
    """Command to generate text using Ollama models."""

    name = "ollama_generate"
    
    def __init__(self):
        """Initialize Ollama generate command."""
        super().__init__()
        self.ollama_security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        model: str,
        prompt: str,
        base_url: Optional[str] = None,
        stream: bool = False,
        format: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        system: Optional[str] = None,
        template: Optional[str] = None,
        context: Optional[List[int]] = None,
        raw: bool = False,
        use_queue: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama generate command.
        
        Args:
            model: Model name to use for generation
            prompt: Input prompt for generation
            base_url: Ollama server base URL
            stream: Whether to stream response
            format: Response format
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            repeat_penalty: Repeat penalty parameter
            system: System prompt
            template: Template for formatting
            context: Previous context
            raw: Whether to use raw mode
            use_queue: Whether to use queue for processing
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with generated text
        """
        # Use unified security approach
        return await super().execute(
            model=model,
            prompt=prompt,
            base_url=base_url,
            stream=stream,
            format=format,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            system=system,
            template=template,
            context=context,
            raw=raw,
            use_queue=use_queue,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama generate command."""
        return "ollama:generate"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama generate command logic."""
        return await self._generate_text(**kwargs)

    async def _generate_text(
        self,
        model: str,
        prompt: str,
        base_url: Optional[str] = None,
        stream: bool = False,
        format: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        system: Optional[str] = None,
        template: Optional[str] = None,
        context: Optional[List[int]] = None,
        raw: bool = False,
        use_queue: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate text using Ollama model."""
        try:
            server_url = base_url or "http://localhost:11434"
            
            # Build options dictionary
            options = {}
            if temperature is not None:
                options["temperature"] = temperature
            if max_tokens is not None:
                options["num_predict"] = max_tokens
            if top_p is not None:
                options["top_p"] = top_p
            if top_k is not None:
                options["top_k"] = top_k
            if repeat_penalty is not None:
                options["repeat_penalty"] = repeat_penalty
            
            async with OllamaClient(base_url=server_url) as client:
                if stream:
                    # Stream response
                    response_parts = []
                    async for response in client.generate(
                        model=model,
                        prompt=prompt,
                        stream=True,
                        format=format,
                        options=options if options else None,
                        system=system,
                        template=template,
                        context=context,
                        raw=raw,
                    ):
                        response_parts.append(response)
                    
                    return {
                        "message": f"Text generated with model '{model}' (streamed)",
                        "model": model,
                        "prompt": prompt,
                        "server_url": server_url,
                        "stream": True,
                        "response_parts": response_parts,
                        "status": "completed",
                    }
                else:
                    # Single response
                    result = await client.generate(
                        model=model,
                        prompt=prompt,
                        stream=False,
                        format=format,
                        options=options if options else None,
                        system=system,
                        template=template,
                        context=context,
                        raw=raw,
                    )
                    
                    return {
                        "message": f"Text generated with model '{model}'",
                        "model": model,
                        "prompt": prompt,
                        "server_url": server_url,
                        "stream": False,
                        "result": result,
                        "status": "completed",
                    }

        except Exception as e:
            raise CustomError(f"Ollama text generation failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Ollama generate command parameters."""
        return {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "Model name to use for generation",
                },
                "prompt": {
                    "type": "string",
                    "description": "Input prompt for generation",
                },
                "base_url": {
                    "type": "string",
                    "description": "Ollama server base URL",
                    "default": "http://localhost:11434",
                },
                "stream": {
                    "type": "boolean",
                    "description": "Whether to stream response",
                    "default": False,
                },
                "format": {
                    "type": "string",
                    "description": "Response format",
                },
                "temperature": {
                    "type": "number",
                    "description": "Sampling temperature",
                    "minimum": 0.0,
                    "maximum": 2.0,
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens to generate",
                    "minimum": 1,
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
                "system": {
                    "type": "string",
                    "description": "System prompt",
                },
                "template": {
                    "type": "string",
                    "description": "Template for formatting",
                },
                "context": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Previous context",
                },
                "raw": {
                    "type": "boolean",
                    "description": "Whether to use raw mode",
                    "default": False,
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
