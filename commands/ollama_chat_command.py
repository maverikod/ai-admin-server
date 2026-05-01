from mcp_proxy_adapter.commands.result import SuccessResult
from mcp_proxy_adapter.core.errors import CommandError as CustomError, InternalError
"""Ollama chat command for conversational AI.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter
from ai_admin.ollama.ollama_client import OllamaClient


class OllamaChatCommand(BaseUnifiedCommand):
    """Command to chat with Ollama models using conversation format."""

    name = "ollama_chat"
    
    def __init__(self):
        """Initialize Ollama chat command."""
        super().__init__()
        self.ollama_security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        model: str,
        messages: List[Dict[str, str]],
        base_url: Optional[str] = None,
        stream: bool = False,
        format: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        use_queue: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama chat command.
        
        Args:
            model: Model name to use for chat
            messages: List of message dictionaries with 'role' and 'content'
            base_url: Ollama server base URL
            stream: Whether to stream response
            format: Response format
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            repeat_penalty: Repeat penalty parameter
            use_queue: Whether to use queue for processing
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with chat response
        """
        # Use unified security approach
        return await super().execute(
            model=model,
            messages=messages,
            base_url=base_url,
            stream=stream,
            format=format,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            use_queue=use_queue,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama chat command."""
        return "ollama:chat"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama chat command logic."""
        return await self._chat_with_model(**kwargs)

    async def _chat_with_model(
        self,
        model: str,
        messages: List[Dict[str, str]],
        base_url: Optional[str] = None,
        stream: bool = False,
        format: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        repeat_penalty: Optional[float] = None,
        use_queue: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Chat with Ollama model."""
        try:
            server_url = base_url or "http://localhost:11434"
            
            # Validate messages format
            if not messages or not isinstance(messages, list):
                raise CustomError("Messages must be a non-empty list")
            
            for i, message in enumerate(messages):
                if not isinstance(message, dict) or 'role' not in message or 'content' not in message:
                    raise CustomError(f"Message {i} must have 'role' and 'content' fields")
                if message['role'] not in ['user', 'assistant', 'system']:
                    raise CustomError(f"Message {i} role must be 'user', 'assistant', or 'system'")
            
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
                    async for response in client.chat(
                        model=model,
                        messages=messages,
                        stream=True,
                        format=format,
                        options=options if options else None,
                    ):
                        response_parts.append(response)
                    
                    return {
                        "message": f"Chat completed with model '{model}' (streamed)",
                        "model": model,
                        "messages": messages,
                        "server_url": server_url,
                        "stream": True,
                        "response_parts": response_parts,
                        "status": "completed",
                    }
                else:
                    # Single response
                    result = await client.chat(
                        model=model,
                        messages=messages,
                        stream=False,
                        format=format,
                        options=options if options else None,
                    )
                    
                    return {
                        "message": f"Chat completed with model '{model}'",
                        "model": model,
                        "messages": messages,
                        "server_url": server_url,
                        "stream": False,
                        "result": result,
                        "status": "completed",
                    }

        except Exception as e:
            raise CustomError(f"Ollama chat failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Ollama chat command parameters."""
        return {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "Model name to use for chat",
                },
                "messages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {
                                "type": "string",
                                "enum": ["user", "assistant", "system"],
                                "description": "Message role"
                            },
                            "content": {
                                "type": "string",
                                "description": "Message content"
                            }
                        },
                        "required": ["role", "content"],
                        "additionalProperties": False
                    },
                    "description": "List of message dictionaries with 'role' and 'content'",
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
            "required": ["model", "messages"],
            "additionalProperties": False,
        }
