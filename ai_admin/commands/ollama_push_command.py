import json
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.ollama_base import ollama_config

class OllamaPushCommand(Command):
    """Push Ollama models to registry."""
    
    name = "ollama_push"
    
    async def execute(self, 
                     model_name: str,
                     **kwargs):
        """Execute Ollama push command.
        
        Args:
            model_name: Name of the model to push to registry
            
        Returns:
            Success or error result
        """
        try:
            return await self._push_model(model_name)
                
        except Exception as e:
            return ErrorResult(
                message=f"Ollama push command failed: {str(e)}",
                code="OLLAMA_PUSH_ERROR",
                details={"model_name": model_name, "error": str(e)}
            )
    
    async def _push_model(self, model_name: str) -> SuccessResult:
        """Push a model to registry via API."""
        try:
            server_url = ollama_config.get_ollama_url()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server_url}/api/push",
                    json={"name": model_name},
                    timeout=600  # 10 minutes timeout for push operation
                ) as response:
                    if response.status == 200:
                        return SuccessResult(data={
                            "message": f"Model {model_name} pushed to registry successfully",
                            "model_name": model_name,
                            "status": "pushed",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        error_text = await response.text()
                        return ErrorResult(
                            message=f"Failed to push model: HTTP {response.status}",
                            code="PUSH_FAILED",
                            details={
                                "model_name": model_name,
                                "status": response.status,
                                "error": error_text
                            }
                        )
                        
        except Exception as e:
            return ErrorResult(
                message=f"Failed to push model: {str(e)}",
                code="PUSH_ERROR",
                details={"model_name": model_name, "error": str(e)}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "description": "Name of the Ollama model to push to registry"
                }
            },
            "required": ["model_name"],
            "additionalProperties": False
        } 