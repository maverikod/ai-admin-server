import subprocess
import json
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

class LLMInferenceCommand(Command):
    """Execute LLM inference on local or cloud models."""
    
    name = "llm_inference"
    
    async def execute(self, 
                     prompt: str,
                     model: str = "llama2:7b",
                     backend: str = "local",  # local, vast, openai
                     max_tokens: int = 1000,
                     temperature: float = 0.7,
                     vast_instance_id: Optional[str] = None,
                     **kwargs):
        """Execute LLM inference.
        
        Args:
            prompt: Input prompt for the model
            model: Model name (e.g., llama2:7b, gpt-4)
            backend: Backend to use (local, vast, openai)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            vast_instance_id: Vast.ai instance ID for cloud inference
            
        Returns:
            Success or error result with generated text
        """
        try:
            if backend == "local":
                return await self._local_inference(prompt, model, max_tokens, temperature)
            elif backend == "vast":
                return await self._vast_inference(prompt, model, max_tokens, temperature, vast_instance_id)
            elif backend == "openai":
                return await self._openai_inference(prompt, model, max_tokens, temperature)
            else:
                return ErrorResult(
                    message=f"Unsupported backend: {backend}",
                    code="UNSUPPORTED_BACKEND",
                    details={"supported_backends": ["local", "vast", "openai"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"LLM inference failed: {str(e)}",
                code="INFERENCE_ERROR",
                details={"backend": backend, "model": model}
            )
    
    async def _local_inference(self, prompt: str, model: str, max_tokens: int, temperature: float) -> SuccessResult:
        """Execute inference on local Ollama model."""
        try:
            # Prepare Ollama request
            request_data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            
            # Send request to Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=request_data,
                timeout=120
            )
            
            if response.status_code != 200:
                return ErrorResult(
                    message=f"Ollama request failed: {response.text}",
                    code="OLLAMA_REQUEST_FAILED",
                    details={"status_code": response.status_code}
                )
            
            result = response.json()
            
            return SuccessResult(data={
                "message": "Local inference completed",
                "model": model,
                "backend": "local",
                "generated_text": result.get("response", ""),
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "generated_tokens": result.get("eval_count", 0),
                "total_duration": result.get("eval_duration", 0),
                "tokens_per_second": result.get("eval_count", 0) / (result.get("eval_duration", 1) / 1e9),
                "timestamp": datetime.now().isoformat()
            })
            
        except requests.exceptions.RequestException as e:
            return ErrorResult(
                message=f"Failed to connect to Ollama: {str(e)}",
                code="OLLAMA_CONNECTION_FAILED",
                details={"model": model}
            )
    
    async def _vast_inference(self, prompt: str, model: str, max_tokens: int, temperature: float, instance_id: Optional[str]) -> SuccessResult:
        """Execute inference on Vast.ai instance."""
        try:
            if not instance_id:
                return ErrorResult(
                    message="Vast.ai instance ID is required for cloud inference",
                    code="MISSING_INSTANCE_ID",
                    details={"backend": "vast"}
                )
            
            # Get Vast.ai instance connection details
            from ai_admin.commands.vast_instances_command import VastInstancesCommand
            vast_cmd = VastInstancesCommand()
            
            # Get instance info
            instance_info = await vast_cmd._get_instance_info(instance_id)
            if not instance_info:
                return ErrorResult(
                    message=f"Vast.ai instance {instance_id} not found",
                    code="VAST_INSTANCE_NOT_FOUND",
                    details={"instance_id": instance_id}
                )
            
            # Connect to instance and run Ollama inference
            import subprocess
            import json
            
            # Build curl command for Ollama API
            ollama_url = f"http://{instance_info['ip']}:11434/api/generate"
            
            request_data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            
            cmd = [
                "curl", "-s", "-X", "POST",
                ollama_url,
                "-H", "Content-Type: application/json",
                "-d", json.dumps(request_data)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                response_data = json.loads(stdout.decode('utf-8'))
                generated_text = response_data.get('response', '')
                
                return SuccessResult(data={
                    "message": "Vast.ai inference completed successfully",
                    "model": model,
                    "backend": "vast",
                    "instance_id": instance_id,
                    "generated_text": generated_text,
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                error_msg = stderr.decode('utf-8')
                return ErrorResult(
                    message=f"Vast.ai inference failed: {error_msg}",
                    code="VAST_INFERENCE_FAILED",
                    details={"instance_id": instance_id, "model": model, "error": error_msg}
                )
            
        except Exception as e:
            return ErrorResult(
                message=f"Vast.ai inference failed: {str(e)}",
                code="VAST_INFERENCE_FAILED",
                details={"instance_id": instance_id, "model": model, "exception": str(e)}
            )
    
    async def _openai_inference(self, prompt: str, model: str, max_tokens: int, temperature: float) -> SuccessResult:
        """Execute inference using OpenAI API."""
        try:
            import os
            import aiohttp
            import json
            
            # Get OpenAI API key from environment
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return ErrorResult(
                    message="OpenAI API key not configured. Set OPENAI_API_KEY environment variable.",
                    code="OPENAI_API_KEY_MISSING",
                    details={"model": model}
                )
            
            # OpenAI API endpoint
            api_url = "https://api.openai.com/v1/chat/completions"
            
            # Prepare request data
            request_data = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=request_data, headers=headers) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        generated_text = response_data['choices'][0]['message']['content']
                        
                        return SuccessResult(data={
                            "message": "OpenAI inference completed successfully",
                            "model": model,
                            "backend": "openai",
                            "generated_text": generated_text,
                            "prompt": prompt,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "usage": response_data.get('usage', {}),
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        error_text = await response.text()
                        return ErrorResult(
                            message=f"OpenAI API request failed: {response.status} - {error_text}",
                            code="OPENAI_API_ERROR",
                            details={"model": model, "status": response.status, "error": error_text}
                        )
            
        except Exception as e:
            return ErrorResult(
                message=f"OpenAI inference failed: {str(e)}",
                code="OPENAI_INFERENCE_FAILED",
                details={"model": model, "exception": str(e)}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Input prompt for the model",
                    "minLength": 1
                },
                "model": {
                    "type": "string",
                    "description": "Model name (e.g., llama2:7b, gpt-4)",
                    "default": "llama2:7b"
                },
                "backend": {
                    "type": "string",
                    "description": "Backend to use",
                    "enum": ["local", "vast", "openai"],
                    "default": "local"
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens to generate",
                    "minimum": 1,
                    "maximum": 10000,
                    "default": 1000
                },
                "temperature": {
                    "type": "number",
                    "description": "Sampling temperature (0.0-2.0)",
                    "minimum": 0.0,
                    "maximum": 2.0,
                    "default": 0.7
                },
                "vast_instance_id": {
                    "type": "string",
                    "description": "Vast.ai instance ID for cloud inference",
                    "default": None
                }
            },
            "required": ["prompt"],
            "additionalProperties": False
        } 