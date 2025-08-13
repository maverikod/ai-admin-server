import json
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.ollama_base import ollama_config

class OllamaShowCommand(Command):
    """Show detailed information about Ollama models."""
    
    name = "ollama_show"
    
    async def execute(self, 
                     model_name: str,
                     **kwargs):
        """Execute Ollama show command.
        
        Args:
            model_name: Name of the model to show information for
            
        Returns:
            Success or error result with model information
        """
        try:
            return await self._show_model(model_name)
                
        except Exception as e:
            return ErrorResult(
                message=f"Ollama show command failed: {str(e)}",
                code="OLLAMA_SHOW_ERROR",
                details={"model_name": model_name, "error": str(e)}
            )
    
    async def _show_model(self, model_name: str) -> SuccessResult:
        """Show detailed information about a model via API."""
        try:
            server_url = ollama_config.get_ollama_url()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server_url}/api/show",
                    json={"name": model_name},
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract key information
                        model_info = {
                            "name": data.get("name", model_name),
                            "model": data.get("model", ""),
                            "modified_at": data.get("modified_at", ""),
                            "size": data.get("size", 0),
                            "digest": data.get("digest", ""),
                            "details": data.get("details", {}),
                            "parameters": data.get("parameters", ""),
                            "template": data.get("template", ""),
                            "system": data.get("system", ""),
                            "license": data.get("license", ""),
                            "capabilities": data.get("capabilities", []),
                            "layers_count": len(data.get("layers", [])),
                            "total_size_mb": round(data.get("size", 0) / 1024 / 1024, 2),
                            "total_size_gb": round(data.get("size", 0) / 1024 / 1024 / 1024, 2)
                        }
                        
                        return SuccessResult(data={
                            "message": f"Model information retrieved for {model_name}",
                            "model_name": model_name,
                            "info": model_info,
                            "raw_data": data,
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        error_text = await response.text()
                        return ErrorResult(
                            message=f"Failed to get model information: HTTP {response.status}",
                            code="SHOW_FAILED",
                            details={
                                "model_name": model_name,
                                "status": response.status,
                                "error": error_text
                            }
                        )
                        
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get model information: {str(e)}",
                code="SHOW_ERROR",
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
                    "description": "Name of the Ollama model to show information for"
                }
            },
            "required": ["model_name"],
            "additionalProperties": False
        } 