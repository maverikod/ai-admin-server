"""Docker logs command for viewing container logs."""

import subprocess
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError

class DockerLogsCommand(Command):
    """View Docker container logs."""
    
    name = "docker_logs"
    
    async def execute(self, 
                     container_name: str,
                     follow: bool = False,
                     tail: Optional[int] = None,
                     since: Optional[str] = None,
                     until: Optional[str] = None,
                     timestamps: bool = False,
                     **kwargs):
        """Execute Docker logs command.
        
        Args:
            container_name: Name or ID of the container
            follow: Follow log output
            tail: Number of lines to show from the end
            since: Show logs since timestamp (e.g., '2023-01-02T13:23:37')
            until: Show logs before timestamp
            timestamps: Show timestamps
            
        Returns:
            Success or error result
        """
        try:
            # Validate inputs
            if not container_name:
                raise ValidationError("Container name is required")
            
            return await self._get_logs(container_name, follow, tail, since, until, timestamps)
        except Exception as e:
            return ErrorResult(
                message=f"Docker logs command failed: {str(e)}",
                code="DOCKER_LOGS_ERROR",
                details={"error": str(e), "container_name": container_name}
            )
    
    async def _get_logs(self, container_name: str, follow: bool, tail: Optional[int], 
                       since: Optional[str], until: Optional[str], timestamps: bool) -> SuccessResult:
        """Get Docker container logs."""
        try:
            cmd = ["docker", "logs"]
            
            # Add options
            if follow:
                cmd.append("-f")
            
            if tail:
                cmd.extend(["--tail", str(tail)])
            
            if since:
                cmd.extend(["--since", since])
            
            if until:
                cmd.extend(["--until", until])
            
            if timestamps:
                cmd.append("-t")
            
            cmd.append(container_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to get logs for container '{container_name}': {result.stderr}",
                    code="DOCKER_LOGS_FAILED",
                    details={"container_name": container_name, "stderr": result.stderr}
                )
            
            logs = result.stdout
            
            return SuccessResult(data={
                "message": f"Successfully retrieved logs for container '{container_name}'",
                "container_name": container_name,
                "logs": logs,
                "follow": follow,
                "tail": tail,
                "since": since,
                "until": until,
                "timestamps": timestamps,
                "log_lines": len(logs.splitlines()) if logs else 0,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker logs command timed out",
                code="DOCKER_LOGS_TIMEOUT",
                details={"container_name": container_name}
            ) 