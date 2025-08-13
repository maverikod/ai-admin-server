import subprocess
import json
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

class DockerNetworkCreateCommand(Command):
    """Create Docker network."""
    
    name = "docker_network_create"
    
    async def execute(self, 
                     network_name: str,
                     driver: str = "bridge",
                     subnet: Optional[str] = None,
                     gateway: Optional[str] = None,
                     internal: bool = False,
                     attachable: bool = False,
                     **kwargs):
        """Execute Docker network create command.
        
        Args:
            network_name: Name of the network to create
            driver: Network driver (bridge, host, overlay, etc.)
            subnet: Subnet in CIDR notation (e.g., 172.20.0.0/16)
            gateway: Gateway IP address
            internal: Create internal network (no external access)
            attachable: Enable manual container attachment
            
        Returns:
            Success or error result
        """
        try:
            return await self._create_network(network_name, driver, subnet, gateway, internal, attachable)
        except Exception as e:
            return ErrorResult(
                message=f"Docker network create command failed: {str(e)}",
                code="DOCKER_NETWORK_CREATE_ERROR",
                details={"error": str(e), "network_name": network_name}
            )
    
    async def _create_network(self, network_name: str, driver: str, subnet: Optional[str], 
                            gateway: Optional[str], internal: bool, attachable: bool) -> SuccessResult:
        """Create Docker network."""
        try:
            cmd = ["docker", "network", "create"]
            
            if driver != "bridge":
                cmd.extend(["--driver", driver])
            
            if subnet:
                cmd.extend(["--subnet", subnet])
            
            if gateway:
                cmd.extend(["--gateway", gateway])
            
            if internal:
                cmd.append("--internal")
            
            if attachable:
                cmd.append("--attachable")
            
            cmd.append(network_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to create Docker network '{network_name}': {result.stderr}",
                    code="DOCKER_NETWORK_CREATE_FAILED",
                    details={"network_name": network_name, "stderr": result.stderr}
                )
            
            network_id = result.stdout.strip()
            
            return SuccessResult(data={
                "message": f"Successfully created network '{network_name}'",
                "network_name": network_name,
                "network_id": network_id,
                "driver": driver,
                "subnet": subnet,
                "gateway": gateway,
                "internal": internal,
                "attachable": attachable,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker network create command timed out",
                code="DOCKER_NETWORK_CREATE_TIMEOUT",
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
                    "description": "Name of the network to create"
                },
                "driver": {
                    "type": "string",
                    "default": "bridge",
                    "description": "Network driver (bridge, host, overlay, etc.)"
                },
                "subnet": {
                    "type": "string",
                    "description": "Subnet in CIDR notation (e.g., 172.20.0.0/16)"
                },
                "gateway": {
                    "type": "string",
                    "description": "Gateway IP address"
                },
                "internal": {
                    "type": "boolean",
                    "default": False,
                    "description": "Create internal network (no external access)"
                },
                "attachable": {
                    "type": "boolean",
                    "default": False,
                    "description": "Enable manual container attachment"
                }
            },
            "required": ["network_name"],
            "additionalProperties": False
        } 