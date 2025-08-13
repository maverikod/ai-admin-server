"""Docker cp command for copying files between host and containers."""

import subprocess
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError

class DockerCpCommand(Command):
    """Copy files between host and Docker container."""
    
    name = "docker_cp"
    
    async def execute(self, 
                     source: str,
                     destination: str,
                     **kwargs):
        """Execute Docker cp command.
        
        Args:
            source: Source path (host path or container:path)
            destination: Destination path (host path or container:path)
            
        Returns:
            Success or error result
        """
        try:
            # Validate inputs
            if not source:
                raise ValidationError("Source path is required")
            if not destination:
                raise ValidationError("Destination path is required")
            
            return await self._copy_files(source, destination)
        except Exception as e:
            return ErrorResult(
                message=f"Docker cp command failed: {str(e)}",
                code="DOCKER_CP_ERROR",
                details={"error": str(e), "source": source, "destination": destination}
            )
    
    async def _copy_files(self, source: str, destination: str) -> SuccessResult:
        """Copy files using Docker cp command."""
        try:
            cmd = ["docker", "cp", source, destination]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to copy from '{source}' to '{destination}': {result.stderr}",
                    code="DOCKER_CP_FAILED",
                    details={"source": source, "destination": destination, "stderr": result.stderr}
                )
            
            return SuccessResult(data={
                "message": f"Successfully copied from '{source}' to '{destination}'",
                "source": source,
                "destination": destination,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker cp command timed out",
                code="DOCKER_CP_TIMEOUT",
                details={"source": source, "destination": destination}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker cp command parameters."""
        return {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source path (host path or container:path)"
                },
                "destination": {
                    "type": "string",
                    "description": "Destination path (host path or container:path)"
                }
            },
            "required": ["source", "destination"]
        } 