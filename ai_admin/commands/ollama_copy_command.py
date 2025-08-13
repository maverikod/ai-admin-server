import json
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.ollama_base import ollama_config

class OllamaCopyCommand(Command):
    """Copy Ollama models."""
    
    name = "ollama_copy"
    
    async def execute(self, 
                     source: str,
                     destination: str,
                     **kwargs):
        """Execute Ollama copy command.
        
        Args:
            source: Name of the source model
            destination: Name of the destination model
            
        Returns:
            Success or error result
        """
        try:
            return await self._copy_model(source, destination)
                
        except Exception as e:
            return ErrorResult(
                message=f"Ollama copy command failed: {str(e)}",
                code="OLLAMA_COPY_ERROR",
                details={"source": source, "destination": destination, "error": str(e)}
            )
    
    async def _copy_model(self, source: str, destination: str) -> SuccessResult:
        """Copy a model via API."""
        try:
            server_url = ollama_config.get_ollama_url()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server_url}/api/copy",
                    json={"source": source, "destination": destination},
                    timeout=300  # 5 minutes timeout for copy operation
                ) as response:
                    if response.status == 200:
                        return SuccessResult(data={
                            "message": f"Model {source} copied to {destination} successfully",
                            "source": source,
                            "destination": destination,
                            "status": "copied",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        error_text = await response.text()
                        return ErrorResult(
                            message=f"Failed to copy model: HTTP {response.status}",
                            code="COPY_FAILED",
                            details={
                                "source": source,
                                "destination": destination,
                                "status": response.status,
                                "error": error_text
                            }
                        )
                        
        except Exception as e:
            return ErrorResult(
                message=f"Failed to copy model: {str(e)}",
                code="COPY_ERROR",
                details={"source": source, "destination": destination, "error": str(e)}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Name of the source model to copy"
                },
                "destination": {
                    "type": "string",
                    "description": "Name of the destination model"
                }
            },
            "required": ["source", "destination"],
            "additionalProperties": False
        } 