import subprocess
import json
from typing import Dict, Any, List
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

class DockerNetworkInspectCommand(Command):
    """Inspect Docker network."""
    
    name = "docker_network_inspect"
    
    async def execute(self, 
                     network_name: str,
                     format_output: str = "json",
                     **kwargs):
        """Execute Docker network inspect command.
        
        Args:
            network_name: Name or ID of the network to inspect
            format_output: Output format (json, pretty)
            
        Returns:
            Success or error result
        """
        try:
            return await self._inspect_network(network_name, format_output)
        except Exception as e:
            return ErrorResult(
                message=f"Docker network inspect command failed: {str(e)}",
                code="DOCKER_NETWORK_INSPECT_ERROR",
                details={"error": str(e), "network_name": network_name}
            )
    
    async def _inspect_network(self, network_name: str, format_output: str) -> SuccessResult:
        """Inspect Docker network."""
        try:
            cmd = ["docker", "network", "inspect"]
            
            if format_output == "pretty":
                cmd.append("--pretty")
            
            cmd.append(network_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to inspect Docker network '{network_name}': {result.stderr}",
                    code="DOCKER_NETWORK_INSPECT_FAILED",
                    details={"network_name": network_name, "stderr": result.stderr}
                )
            
            # Parse output
            network_info = None
            if format_output == "json":
                try:
                    network_info = json.loads(result.stdout)
                    # If it's a list with one item, extract it
                    if isinstance(network_info, list) and len(network_info) == 1:
                        network_info = network_info[0]
                except json.JSONDecodeError:
                    return ErrorResult(
                        message="Failed to parse JSON output from network inspect",
                        code="JSON_PARSE_ERROR",
                        details={"raw_output": result.stdout}
                    )
            else:
                network_info = result.stdout
            
            return SuccessResult(data={
                "message": f"Successfully inspected network '{network_name}'",
                "network_name": network_name,
                "network_info": network_info,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker network inspect command timed out",
                code="DOCKER_NETWORK_INSPECT_TIMEOUT",
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
                    "description": "Name or ID of the network to inspect"
                },
                "format_output": {
                    "type": "string",
                    "enum": ["json", "pretty"],
                    "default": "json",
                    "description": "Output format"
                }
            },
            "required": ["network_name"],
            "additionalProperties": False
        } 