import subprocess
import json
from typing import Dict, Any
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

class DockerNetworkRmCommand(Command):
    """Remove Docker network."""
    
    name = "docker_network_rm"
    
    async def execute(self, 
                     network_name: str,
                     **kwargs):
        """Execute Docker network rm command.
        
        Args:
            network_name: Name or ID of the network to remove
            
        Returns:
            Success or error result
        """
        try:
            return await self._remove_network(network_name)
        except Exception as e:
            return ErrorResult(
                message=f"Docker network rm command failed: {str(e)}",
                code="DOCKER_NETWORK_RM_ERROR",
                details={"error": str(e), "network_name": network_name}
            )
    
    async def _remove_network(self, network_name: str) -> SuccessResult:
        """Remove Docker network."""
        try:
            cmd = ["docker", "network", "rm", network_name]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to remove Docker network '{network_name}': {result.stderr}",
                    code="DOCKER_NETWORK_RM_FAILED",
                    details={"network_name": network_name, "stderr": result.stderr}
                )
            
            return SuccessResult(data={
                "message": f"Successfully removed network '{network_name}'",
                "network_name": network_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker network rm command timed out",
                code="DOCKER_NETWORK_RM_TIMEOUT",
                details={"network_name": network_name}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "network_name": {
                    "type": "string",
                    "description": "Name or ID of the network to remove"
                }
            },
            "required": ["network_name"],
            "additionalProperties": False
        } 