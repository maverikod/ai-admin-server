"""Docker restart command for restarting containers."""

import subprocess
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError

class DockerRestartCommand(Command):
    """Restart Docker container."""
    
    name = "docker_restart"
    
    async def execute(self, 
                     container_name: str,
                     timeout: Optional[int] = None,
                     **kwargs):
        """Execute Docker restart command.
        
        Args:
            container_name: Name or ID of the container to restart
            timeout: Timeout in seconds before killing the container
            
        Returns:
            Success or error result
        """
        try:
            # Validate inputs
            if not container_name:
                raise ValidationError("Container name is required")
            
            return await self._restart_container(container_name, timeout)
        except Exception as e:
            return ErrorResult(
                message=f"Docker restart command failed: {str(e)}",
                code="DOCKER_RESTART_ERROR",
                details={"error": str(e), "container_name": container_name}
            )
    
    async def _restart_container(self, container_name: str, timeout: Optional[int]) -> SuccessResult:
        """Restart Docker container."""
        try:
            cmd = ["docker", "restart"]
            
            if timeout:
                cmd.extend(["-t", str(timeout)])
            
            cmd.append(container_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to restart container '{container_name}': {result.stderr}",
                    code="DOCKER_RESTART_FAILED",
                    details={"container_name": container_name, "stderr": result.stderr}
                )
            
            container_id = result.stdout.strip()
            
            return SuccessResult(data={
                "message": f"Successfully restarted container '{container_name}'",
                "container_name": container_name,
                "container_id": container_id,
                "timeout": timeout,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker restart command timed out",
                code="DOCKER_RESTART_TIMEOUT",
                details={"container_name": container_name}
            ) 