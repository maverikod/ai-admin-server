"""Docker stop command for stopping running containers."""

import subprocess
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError

class DockerStopCommand(Command):
    """Stop Docker container."""
    
    name = "docker_stop"
    
    async def execute(self, 
                     container_name: str,
                     timeout: Optional[int] = None,
                     **kwargs):
        """Execute Docker stop command.
        
        Args:
            container_name: Name or ID of the container to stop
            timeout: Timeout in seconds before killing the container
            
        Returns:
            Success or error result
        """
        try:
            # Validate inputs
            if not container_name:
                raise ValidationError("Container name is required")
            
            return await self._stop_container(container_name, timeout)
        except Exception as e:
            return ErrorResult(
                message=f"Docker stop command failed: {str(e)}",
                code="DOCKER_STOP_ERROR",
                details={"error": str(e), "container_name": container_name}
            )
    
    async def _stop_container(self, container_name: str, timeout: Optional[int]) -> SuccessResult:
        """Stop Docker container."""
        try:
            cmd = ["docker", "stop"]
            
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
                    message=f"Failed to stop container '{container_name}': {result.stderr}",
                    code="DOCKER_STOP_FAILED",
                    details={"container_name": container_name, "stderr": result.stderr}
                )
            
            container_id = result.stdout.strip()
            
            return SuccessResult(data={
                "message": f"Successfully stopped container '{container_name}'",
                "container_name": container_name,
                "container_id": container_id,
                "timeout": timeout,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker stop command timed out",
                code="DOCKER_STOP_TIMEOUT",
                details={"container_name": container_name}
            ) 