import subprocess
import json
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

class DockerNetworkLsCommand(Command):
    """List Docker networks."""
    
    name = "docker_network_ls"
    
    async def execute(self, 
                     format_output: str = "table",
                     filter_network: Optional[str] = None,
                     quiet: bool = False,
                     **kwargs):
        """Execute Docker network ls command.
        
        Args:
            format_output: Output format (table, json, quiet)
            filter_network: Filter networks by name or ID
            quiet: Only display network IDs
            
        Returns:
            Success or error result
        """
        try:
            return await self._list_networks(format_output, filter_network, quiet)
        except Exception as e:
            return ErrorResult(
                message=f"Docker network ls command failed: {str(e)}",
                code="DOCKER_NETWORK_LS_ERROR",
                details={"error": str(e)}
            )
    
    async def _list_networks(self, format_output: str, filter_network: Optional[str], quiet: bool) -> SuccessResult:
        """List Docker networks."""
        try:
            cmd = ["docker", "network", "ls"]
            
            if format_output == "json":
                cmd.append("--format")
                cmd.append("json")
            elif quiet:
                cmd.append("--quiet")
            
            if filter_network:
                cmd.append("--filter")
                cmd.append(f"name={filter_network}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to list Docker networks: {result.stderr}",
                    code="DOCKER_NETWORK_LS_FAILED",
                    details={"stderr": result.stderr}
                )
            
            # Parse output
            networks = []
            if format_output == "json":
                # Parse JSON output
                try:
                    networks = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Handle multiple JSON objects
                    networks = []
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            networks.append(json.loads(line))
            else:
                # Parse table output
                output_lines = result.stdout.strip().split('\n')
                if len(output_lines) > 1:  # Skip header
                    for line in output_lines[1:]:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 4:
                                network_info = {
                                    "network_id": parts[0],
                                    "name": parts[1],
                                    "driver": parts[2],
                                    "scope": parts[3]
                                }
                                networks.append(network_info)
            
            return SuccessResult(data={
                "message": f"Found {len(networks)} Docker networks",
                "networks": networks,
                "count": len(networks),
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker network ls command timed out",
                code="DOCKER_NETWORK_LS_TIMEOUT",
                details={}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "format_output": {
                    "type": "string",
                    "enum": ["table", "json", "quiet"],
                    "default": "table",
                    "description": "Output format"
                },
                "filter_network": {
                    "type": "string",
                    "description": "Filter networks by name or ID"
                },
                "quiet": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only display network IDs"
                }
            },
            "additionalProperties": False
        } 