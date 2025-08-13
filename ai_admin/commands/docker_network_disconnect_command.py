import subprocess
import json
from typing import Dict, Any
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

class DockerNetworkDisconnectCommand(Command):
    """Disconnect container from Docker network."""
    
    name = "docker_network_disconnect"
    
    async def execute(self, 
                     network_name: str,
                     container_name: str,
                     force: bool = False,
                     **kwargs):
        """Execute Docker network disconnect command.
        
        Args:
            network_name: Name of the network to disconnect from
            container_name: Name or ID of the container to disconnect
            force: Force disconnection even if container is running
            
        Returns:
            Success or error result
        """
        try:
            return await self._disconnect_container(network_name, container_name, force)
        except Exception as e:
            return ErrorResult(
                message=f"Docker network disconnect command failed: {str(e)}",
                code="DOCKER_NETWORK_DISCONNECT_ERROR",
                details={"error": str(e), "network_name": network_name, "container_name": container_name}
            )
    
    async def _disconnect_container(self, network_name: str, container_name: str, force: bool) -> SuccessResult:
        """Disconnect container from network."""
        try:
            cmd = ["docker", "network", "disconnect"]
            
            if force:
                cmd.append("--force")
            
            cmd.extend([network_name, container_name])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to disconnect container '{container_name}' from network '{network_name}': {result.stderr}",
                    code="DOCKER_NETWORK_DISCONNECT_FAILED",
                    details={"network_name": network_name, "container_name": container_name, "stderr": result.stderr}
                )
            
            return SuccessResult(data={
                "message": f"Successfully disconnected container '{container_name}' from network '{network_name}'",
                "network_name": network_name,
                "container_name": container_name,
                "force": force,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker network disconnect command timed out",
                code="DOCKER_NETWORK_DISCONNECT_TIMEOUT",
                details={"network_name": network_name, "container_name": container_name}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "network_name": {
                    "type": "string",
                    "description": "Name of the network to disconnect from"
                },
                "container_name": {
                    "type": "string",
                    "description": "Name or ID of the container to disconnect"
                },
                "force": {
                    "type": "boolean",
                    "default": False,
                    "description": "Force disconnection even if container is running"
                }
            },
            "required": ["network_name", "container_name"],
            "additionalProperties": False
        } 