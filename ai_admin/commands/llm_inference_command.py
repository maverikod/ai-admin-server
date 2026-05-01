from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError
"""LLM inference command for running language model inference.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import asyncio
from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.llm_security_adapter import LLMSecurityAdapter

class LLMInferenceCommand(BaseUnifiedCommand):
    """Command to run LLM inference with various backends."""

    name = "llm_inference"
    
    def __init__(self):
        """Initialize LLM inference command."""
        super().__init__()
        self.security_adapter = LLMSecurityAdapter()

    async def execute(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        backend: str = "local",  # local, vast, openai
        max_tokens: int = 1000,
        temperature: float = 0.7,
        vast_instance_id: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute LLM inference.
        
        Args:
            prompt: Input prompt for the model
            model: Model name to use
            backend: Backend to use (local, vast, openai)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            vast_instance_id: Vast.ai instance ID for remote inference
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with inference output
        """
        # Use unified security approach
        return await super().execute(
            prompt=prompt,
            model=model,
            backend=backend,
            max_tokens=max_tokens,
            temperature=temperature,
            vast_instance_id=vast_instance_id,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for LLM inference command."""
        return "llm:inference"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute LLM inference command logic."""
        backend = kwargs.get("backend", "local")
        
        if backend == "local":
            return await self._local_inference(**kwargs)
        elif backend == "vast":
            return await self._vast_inference(**kwargs)
        elif backend == "openai":
            return await self._openai_inference(**kwargs)
        else:
            raise CustomError(f"Unsupported backend: {backend}")

    async def _local_inference(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run local LLM inference."""
        try:
            # Simulate local inference (replace with actual local model)
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Mock response for demonstration
            response = f"Local inference response for prompt: {prompt[:50]}..."
            
            return {
                "message": "Local LLM inference completed",
                "backend": "local",
                "model": model,
                "prompt": prompt,
                "response": response,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "tokens_used": len(prompt.split()) + 20,  # Mock token count
            }

        except CustomError as e:
            raise CustomError(f"Local inference failed: {str(e)}")

    async def _vast_inference(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        vast_instance_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run Vast.ai LLM inference."""
        try:
            if not vast_instance_id:
                raise CustomError("Vast instance ID is required for Vast.ai inference")

            # Simulate Vast.ai API call
            await asyncio.sleep(0.2)  # Simulate network delay
            
            # Mock response for demonstration
            response = f"Vast.ai inference response for prompt: {prompt[:50]}..."
            
            return {
                "message": "Vast.ai LLM inference completed",
                "backend": "vast",
                "model": model,
                "prompt": prompt,
                "response": response,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "vast_instance_id": vast_instance_id,
                "tokens_used": len(prompt.split()) + 25,  # Mock token count
            }

        except CustomError as e:
            raise CustomError(f"Vast.ai inference failed: {str(e)}")

    async def _openai_inference(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run OpenAI LLM inference."""
        try:
            # Simulate OpenAI API call
            await asyncio.sleep(0.3)  # Simulate network delay
            
            # Mock response for demonstration
            response = f"OpenAI inference response for prompt: {prompt[:50]}..."
            
            return {
                "message": "OpenAI LLM inference completed",
                "backend": "openai",
                "model": model,
                "prompt": prompt,
                "response": response,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "tokens_used": len(prompt.split()) + 30,  # Mock token count
            }

        except CustomError as e:
            raise CustomError(f"OpenAI inference failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for LLM inference command parameters."""
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Input prompt for the model",
                },
                "model": {
                    "type": "string",
                    "description": "Model name to use",
                    "default": "gpt-3.5-turbo",
                },
                "backend": {
                    "type": "string",
                    "description": "Backend to use (local, vast, openai)",
                    "default": "local",
                    "enum": ["local", "vast", "openai"],
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens to generate",
                    "default": 1000,
                },
                "temperature": {
                    "type": "number",
                    "description": "Sampling temperature",
                    "default": 0.7,
                },
                "vast_instance_id": {
                    "type": "string",
                    "description": "Vast.ai instance ID for remote inference",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["prompt"],
            "additionalProperties": False,
        }