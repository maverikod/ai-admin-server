"""Docker start command for starting stopped containers."""

import subprocess
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError

class DockerStartCommand(Command):
    """Start Docker container."""
    
    name = "docker_start"
    
    async def execute(self, 
                     container_name: str,
                     **kwargs):
        """Execute Docker start command.
        
        Args:
            container_name: Name or ID of the container to start
            
        Returns:
            Success or error result
        """
        try:
            # Validate inputs
            if not container_name:
                raise ValidationError("Container name is required")
            
            return await self._start_container(container_name)
        except Exception as e:
            return ErrorResult(
                message=f"Docker start command failed: {str(e)}",
                code="DOCKER_START_ERROR",
                details={"error": str(e), "container_name": container_name}
            )
    
    async def _start_container(self, container_name: str) -> SuccessResult:
        """Start Docker container."""
        try:
            cmd = ["docker", "start", container_name]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to start container '{container_name}': {result.stderr}",
                    code="DOCKER_START_FAILED",
                    details={"container_name": container_name, "stderr": result.stderr}
                )
            
            container_id = result.stdout.strip()
            
            return SuccessResult(data={
                "message": f"Successfully started container '{container_name}'",
                "container_name": container_name,
                "container_id": container_id,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker start command timed out",
                code="DOCKER_START_TIMEOUT",
                details={"container_name": container_name}
            ) 