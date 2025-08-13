import subprocess
import json
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

class DockerNetworkConnectCommand(Command):
    """Connect container to Docker network."""
    
    name = "docker_network_connect"
    
    async def execute(self, 
                     network_name: str,
                     container_name: str,
                     ip_address: Optional[str] = None,
                     alias: Optional[str] = None,
                     **kwargs):
        """Execute Docker network connect command.
        
        Args:
            network_name: Name of the network to connect to
            container_name: Name or ID of the container to connect
            ip_address: Static IP address for the container
            alias: Network alias for the container
            
        Returns:
            Success or error result
        """
        try:
            return await self._connect_container(network_name, container_name, ip_address, alias)
        except Exception as e:
            return ErrorResult(
                message=f"Docker network connect command failed: {str(e)}",
                code="DOCKER_NETWORK_CONNECT_ERROR",
                details={"error": str(e), "network_name": network_name, "container_name": container_name}
            )
    
    async def _connect_container(self, network_name: str, container_name: str, 
                               ip_address: Optional[str], alias: Optional[str]) -> SuccessResult:
        """Connect container to network."""
        try:
            cmd = ["docker", "network", "connect"]
            
            if ip_address:
                cmd.extend(["--ip", ip_address])
            
            if alias:
                cmd.extend(["--alias", alias])
            
            cmd.extend([network_name, container_name])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to connect container '{container_name}' to network '{network_name}': {result.stderr}",
                    code="DOCKER_NETWORK_CONNECT_FAILED",
                    details={"network_name": network_name, "container_name": container_name, "stderr": result.stderr}
                )
            
            return SuccessResult(data={
                "message": f"Successfully connected container '{container_name}' to network '{network_name}'",
                "network_name": network_name,
                "container_name": container_name,
                "ip_address": ip_address,
                "alias": alias,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker network connect command timed out",
                code="DOCKER_NETWORK_CONNECT_TIMEOUT",
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
                    "description": "Name of the network to connect to"
                },
                "container_name": {
                    "type": "string",
                    "description": "Name or ID of the container to connect"
                },
                "ip_address": {
                    "type": "string",
                    "description": "Static IP address for the container"
                },
                "alias": {
                    "type": "string",
                    "description": "Network alias for the container"
                }
            },
            "required": ["network_name", "container_name"],
            "additionalProperties": False
        } 