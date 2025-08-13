import json
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.ollama_base import ollama_config

class OllamaRemoveCommand(Command):
    """Remove Ollama models."""
    
    name = "ollama_remove"
    
    async def execute(self, 
                     model_name: str,
                     **kwargs):
        """Execute Ollama remove command.
        
        Args:
            model_name: Name of the model to remove
            
        Returns:
            Success or error result
        """
        try:
            return await self._remove_model(model_name)
                
        except Exception as e:
            return ErrorResult(
                message=f"Ollama remove command failed: {str(e)}",
                code="OLLAMA_REMOVE_ERROR",
                details={"model_name": model_name, "error": str(e)}
            )
    
    async def _remove_model(self, model_name: str) -> SuccessResult:
        """Remove a model via API."""
        try:
            server_url = ollama_config.get_ollama_url()
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{server_url}/api/delete",
                    json={"name": model_name},
                    timeout=30
                ) as response:
                    if response.status == 200:
                        return SuccessResult(data={
                            "message": f"Model {model_name} removed successfully",
                            "model_name": model_name,
                            "status": "removed",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        error_text = await response.text()
                        return ErrorResult(
                            message=f"Failed to remove model: HTTP {response.status}",
                            code="REMOVE_FAILED",
                            details={
                                "model_name": model_name,
                                "status": response.status,
                                "error": error_text
                            }
                        )
                        
        except Exception as e:
            return ErrorResult(
                message=f"Failed to remove model: {str(e)}",
                code="REMOVE_ERROR",
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
                    "description": "Name of the Ollama model to remove"
                }
            },
            "required": ["model_name"],
            "additionalProperties": False
        } 