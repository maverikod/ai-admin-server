"""Docker containers command for listing containers."""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError


class DockerContainersCommand(Command):
    """List Docker containers on the local system.
    
    This command displays information about Docker containers including
    container ID, image, command, created time, status, ports, and names.
    """
    
    name = "docker_containers"
    
    async def execute(
        self,
        all_containers: bool = False,
        size: bool = False,
        quiet: bool = False,
        no_trunc: bool = False,
        format_output: str = "table",
        filter_status: Optional[str] = None,
        filter_ancestor: Optional[str] = None,
        filter_name: Optional[str] = None,
        filter_label: Optional[str] = None,
        **kwargs
    ) -> SuccessResult:
        """Execute Docker containers command.
        
        Args:
            all_containers: Show all containers (default shows just running)
            size: Display total file sizes
            quiet: Only display container IDs
            no_trunc: Don't truncate output
            format_output: Output format (table, json)
            filter_status: Filter by container status (created, running, paused, restarting, removing, exited, dead)
            filter_ancestor: Filter by image name or ID
            filter_name: Filter by container name
            filter_label: Filter by label
            
        Returns:
            Success result with containers information
        """
        try:
            # Build Docker ps command
            cmd = ["docker", "ps"]
            
            # Add options
            if all_containers:
                cmd.append("-a")
            
            if size:
                cmd.append("-s")
            
            if quiet:
                cmd.append("-q")
            
            if no_trunc:
                cmd.append("--no-trunc")
            
            # Add format for structured output
            if format_output == "json":
                cmd.extend(["--format", "json"])
            else:
                # Use JSON format for reliable parsing
                cmd.extend(["--format", "json"])
            
            # Add filters
            if filter_status:
                cmd.extend(["--filter", f"status={filter_status}"])
            
            if filter_ancestor:
                cmd.extend(["--filter", f"ancestor={filter_ancestor}"])
            
            if filter_name:
                cmd.extend(["--filter", f"name={filter_name}"])
            
            if filter_label:
                cmd.extend(["--filter", f"label={filter_label}"])
            
            # Execute ps command
            start_time = datetime.now()
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            end_time = datetime.now()
            
            if process.returncode != 0:
                error_output = stderr.decode('utf-8')
                raise CommandError(
                    f"Docker containers command failed with exit code {process.returncode}",
                    data={
                        "stderr": error_output,
                        "command": " ".join(cmd),
                        "exit_code": process.returncode
                    }
                )
            
            # Parse output
            output = stdout.decode('utf-8').strip()
            
            if quiet:
                # For quiet mode, return list of container IDs
                container_ids = [line.strip() for line in output.split('\n') if line.strip()]
                return SuccessResult(data={
                    "message": f"Found {len(container_ids)} containers",
                    "format": "list",
                    "containers": container_ids,
                    "count": len(container_ids),
                    "filters": {
                        "all_containers": all_containers,
                        "filter_status": filter_status,
                        "filter_ancestor": filter_ancestor,
                        "filter_name": filter_name,
                        "filter_label": filter_label
                    },
                    "execution_time": (end_time - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                })
            
            if format_output == "json":
                # Parse JSON output
                try:
                    containers = json.loads(output) if output else []
                    if not isinstance(containers, list):
                        containers = [containers]
                except json.JSONDecodeError:
                    containers = []
            else:
                # Parse table output
                containers = self._parse_table_output(output)
            
            return SuccessResult(data={
                "message": f"Found {len(containers)} containers",
                "format": format_output,
                "header": "CONTAINER ID\tIMAGE\tCOMMAND\tCREATED\tSTATUS\tPORTS\tNAMES",
                "containers": containers,
                "count": len(containers),
                "filters": {
                    "all_containers": all_containers,
                    "filter_status": filter_status,
                    "filter_ancestor": filter_ancestor,
                    "filter_name": filter_name,
                    "filter_label": filter_label
                },
                "execution_time": (end_time - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Docker containers command failed: {str(e)}",
                code="DOCKER_CONTAINERS_ERROR",
                details={"error": str(e)}
            )
    
    def _parse_table_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse table output from docker ps command."""
        containers = []
        
        if not output:
            return containers
        
        lines = output.strip().split('\n')
        
        # Skip header line if present
        start_line = 0
        if lines and ('CONTAINER ID' in lines[0] or 'ID' in lines[0]):
            start_line = 1
        
        for line in lines[start_line:]:
            if not line.strip():
                continue
            
            # Split by spaces and handle multi-word fields
            parts = line.split()
            if len(parts) >= 7:
                # Extract fields - last field is names, second to last is ports
                # This is a simplified approach - in real implementation you'd need more sophisticated parsing
                container_info = {
                    "id": parts[0].strip(),
                    "image": parts[1].strip(),
                    "command": parts[2].strip(),
                    "created": parts[3].strip(),
                    "status": parts[4].strip(),
                    "ports": parts[5].strip(),
                    "names": parts[6].strip()
                }
                containers.append(container_info)
            elif len(parts) >= 6:
                # Handle case with fewer columns
                container_info = {
                    "id": parts[0].strip(),
                    "image": parts[1].strip(),
                    "command": parts[2].strip(),
                    "created": parts[3].strip(),
                    "status": parts[4].strip(),
                    "ports": parts[5].strip(),
                    "names": ""
                }
                containers.append(container_info)
        
        return containers
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "all_containers": {
                    "type": "boolean",
                    "description": "Show all containers (default shows just running)",
                    "default": False
                },
                "size": {
                    "type": "boolean",
                    "description": "Display total file sizes",
                    "default": False
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Only display container IDs",
                    "default": False
                },
                "no_trunc": {
                    "type": "boolean",
                    "description": "Don't truncate output",
                    "default": False
                },
                "format_output": {
                    "type": "string",
                    "enum": ["table", "json"],
                    "description": "Output format",
                    "default": "table"
                },
                "filter_status": {
                    "type": "string",
                    "enum": ["created", "running", "paused", "restarting", "removing", "exited", "dead"],
                    "description": "Filter by container status"
                },
                "filter_ancestor": {
                    "type": "string",
                    "description": "Filter by image name or ID"
                },
                "filter_name": {
                    "type": "string",
                    "description": "Filter by container name"
                },
                "filter_label": {
                    "type": "string",
                    "description": "Filter by label"
                }
            },
            "additionalProperties": False
        } 