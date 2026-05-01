from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError, NetworkError
"""Ollama run command for running model inference.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import aiohttp

from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.ollama_security_adapter import OllamaSecurityAdapter

class OllamaRunCommand(BaseUnifiedCommand):
    """Command to run Ollama model inference."""

    name = "ollama_run"
    
    def __init__(self):
        """Initialize Ollama run command."""
        super().__init__()
        self.ollama_security_adapter = OllamaSecurityAdapter()

    async def execute(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        use_queue: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Ollama run command with unified security.
        
        Args:
            prompt: Input prompt for the model
            model_name: Name of the model to use
            model: Alternative model parameter
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            use_queue: Whether to use queue for processing
            user_roles: List of user roles for security validation
            
        Returns:
            Success result with inference output
        """
        # Use unified security approach
        return await super().execute(
            prompt=prompt,
            model_name=model_name,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            use_queue=use_queue,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Ollama run command."""
        return "ollama:run"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Ollama run command logic."""
        return await self._run_inference(**kwargs)

    async def _run_inference(
        self,
        prompt: str,
        model_name: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        use_queue: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run model inference."""
        try:
            # Use model_name or model parameter
            actual_model = model_name or model or "llama2"
            
            server_url = "http://localhost:11434"
            
            payload = {
                "model": actual_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300),  # 5 minutes for inference
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        
                        return {
                            "message": f"Successfully generated response using model '{actual_model}'",
                            "model": actual_model,
                            "prompt": prompt,
                            "response": response_text,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "use_queue": use_queue,
                            "tokens_used": result.get("eval_count", 0),
                            "generation_time": result.get("total_duration", 0),
                        }
                    else:
                        error_text = await response.text()
                        raise CustomError(f"Inference failed with status {response.status}: {error_text}")

        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error during inference: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Ollama run command failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Ollama run command parameters."""
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Input prompt for the model",
                },
                "model_name": {
                    "type": "string",
                    "description": "Name of the model to use",
                },
                "model": {
                    "type": "string",
                    "description": "Alternative model parameter",
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
            "required": ["prompt"],
            "additionalProperties": False,
        }