"""Docker rm command for removing containers."""

import subprocess
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError

class DockerRmCommand(Command):
    """Remove Docker container."""
    
    name = "docker_rm"
    
    async def execute(self, 
                     container_name: str,
                     force: bool = False,
                     volumes: bool = False,
                     **kwargs):
        """Execute Docker rm command.
        
        Args:
            container_name: Name or ID of the container to remove
            force: Force removal of running container
            volumes: Remove associated volumes
            
        Returns:
            Success or error result
        """
        try:
            # Validate inputs
            if not container_name:
                raise ValidationError("Container name is required")
            
            return await self._remove_container(container_name, force, volumes)
        except Exception as e:
            return ErrorResult(
                message=f"Docker rm command failed: {str(e)}",
                code="DOCKER_RM_ERROR",
                details={"error": str(e), "container_name": container_name}
            )
    
    async def _remove_container(self, container_name: str, force: bool, volumes: bool) -> SuccessResult:
        """Remove Docker container."""
        try:
            cmd = ["docker", "rm"]
            
            if force:
                cmd.append("-f")
            
            if volumes:
                cmd.append("-v")
            
            cmd.append(container_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to remove container '{container_name}': {result.stderr}",
                    code="DOCKER_RM_FAILED",
                    details={"container_name": container_name, "stderr": result.stderr}
                )
            
            container_id = result.stdout.strip()
            
            return SuccessResult(data={
                "message": f"Successfully removed container '{container_name}'",
                "container_name": container_name,
                "container_id": container_id,
                "force": force,
                "volumes": volumes,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker rm command timed out",
                code="DOCKER_RM_TIMEOUT",
                details={"container_name": container_name}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker rm command parameters."""
        return {
            "type": "object",
            "properties": {
                "container_name": {
                    "type": "string",
                    "description": "Name or ID of the container to remove"
                },
                "force": {
                    "type": "boolean",
                    "description": "Force removal of running container",
                    "default": False
                },
                "volumes": {
                    "type": "boolean",
                    "description": "Remove associated volumes",
                    "default": False
                }
            },
            "required": ["container_name"]
        } 