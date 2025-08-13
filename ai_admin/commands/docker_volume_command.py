"""Docker volume command for managing volumes."""

import subprocess
import json
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError

class DockerVolumeCommand(Command):
    """Manage Docker volumes."""
    
    name = "docker_volume"
    
    async def execute(self, 
                     action: str = "list",
                     volume_name: Optional[str] = None,
                     driver: Optional[str] = None,
                     labels: Optional[Dict[str, str]] = None,
                     force: bool = False,
                     **kwargs):
        """Execute Docker volume command.
        
        Args:
            action: Action to perform (list, create, inspect, rm, prune)
            volume_name: Name of the volume (for create, inspect, rm actions)
            driver: Volume driver (for create action)
            labels: Labels for the volume (for create action)
            force: Force removal (for rm action)
            
        Returns:
            Success or error result
        """
        try:
            if action == "list":
                return await self._list_volumes()
            elif action == "create":
                if not volume_name:
                    raise ValidationError("Volume name is required for create action")
                return await self._create_volume(volume_name, driver, labels)
            elif action == "inspect":
                if not volume_name:
                    raise ValidationError("Volume name is required for inspect action")
                return await self._inspect_volume(volume_name)
            elif action == "rm":
                if not volume_name:
                    raise ValidationError("Volume name is required for rm action")
                return await self._remove_volume(volume_name, force)
            elif action == "prune":
                return await self._prune_volumes()
            else:
                raise ValidationError(f"Unknown action: {action}")
                
        except Exception as e:
            return ErrorResult(
                message=f"Docker volume command failed: {str(e)}",
                code="DOCKER_VOLUME_ERROR",
                details={"error": str(e), "action": action}
            )
    
    async def _list_volumes(self) -> SuccessResult:
        """List all Docker volumes."""
        try:
            cmd = ["docker", "volume", "ls", "--format", "json"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to list volumes: {result.stderr}",
                    code="DOCKER_VOLUME_LIST_FAILED",
                    details={"stderr": result.stderr}
                )
            
            # Parse JSON output
            volumes = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        volume_info = json.loads(line)
                        volumes.append(volume_info)
                    except json.JSONDecodeError:
                        continue
            
            return SuccessResult(data={
                "message": f"Found {len(volumes)} volumes",
                "volumes": volumes,
                "count": len(volumes),
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker volume list command timed out",
                code="DOCKER_VOLUME_TIMEOUT",
                details={}
            )
    
    async def _create_volume(self, volume_name: str, driver: Optional[str], labels: Optional[Dict[str, str]]) -> SuccessResult:
        """Create a new Docker volume."""
        try:
            cmd = ["docker", "volume", "create"]
            
            if driver:
                cmd.extend(["--driver", driver])
            
            if labels:
                for key, value in labels.items():
                    cmd.extend(["--label", f"{key}={value}"])
            
            cmd.append(volume_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to create volume '{volume_name}': {result.stderr}",
                    code="DOCKER_VOLUME_CREATE_FAILED",
                    details={"volume_name": volume_name, "stderr": result.stderr}
                )
            
            return SuccessResult(data={
                "message": f"Successfully created volume '{volume_name}'",
                "volume_name": volume_name,
                "driver": driver,
                "labels": labels,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker volume create command timed out",
                code="DOCKER_VOLUME_TIMEOUT",
                details={"volume_name": volume_name}
            )
    
    async def _inspect_volume(self, volume_name: str) -> SuccessResult:
        """Inspect a Docker volume."""
        try:
            cmd = ["docker", "volume", "inspect", volume_name]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to inspect volume '{volume_name}': {result.stderr}",
                    code="DOCKER_VOLUME_INSPECT_FAILED",
                    details={"volume_name": volume_name, "stderr": result.stderr}
                )
            
            try:
                volume_info = json.loads(result.stdout)
            except json.JSONDecodeError:
                return ErrorResult(
                    message="Failed to parse volume inspect output",
                    code="DOCKER_VOLUME_PARSE_ERROR",
                    details={"volume_name": volume_name, "stdout": result.stdout}
                )
            
            return SuccessResult(data={
                "message": f"Volume '{volume_name}' inspection completed",
                "volume_name": volume_name,
                "volume_info": volume_info,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker volume inspect command timed out",
                code="DOCKER_VOLUME_TIMEOUT",
                details={"volume_name": volume_name}
            )
    
    async def _remove_volume(self, volume_name: str, force: bool) -> SuccessResult:
        """Remove a Docker volume."""
        try:
            cmd = ["docker", "volume", "rm"]
            
            if force:
                cmd.append("--force")
            
            cmd.append(volume_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to remove volume '{volume_name}': {result.stderr}",
                    code="DOCKER_VOLUME_RM_FAILED",
                    details={"volume_name": volume_name, "stderr": result.stderr}
                )
            
            return SuccessResult(data={
                "message": f"Successfully removed volume '{volume_name}'",
                "volume_name": volume_name,
                "force": force,
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker volume rm command timed out",
                code="DOCKER_VOLUME_TIMEOUT",
                details={"volume_name": volume_name}
            )
    
    async def _prune_volumes(self) -> SuccessResult:
        """Remove unused volumes."""
        try:
            cmd = ["docker", "volume", "prune", "--force"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to prune volumes: {result.stderr}",
                    code="DOCKER_VOLUME_PRUNE_FAILED",
                    details={"stderr": result.stderr}
                )
            
            return SuccessResult(data={
                "message": "Successfully pruned unused volumes",
                "raw_output": result.stdout,
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker volume prune command timed out",
                code="DOCKER_VOLUME_TIMEOUT",
                details={}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker volume command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["list", "create", "inspect", "rm", "prune"],
                    "default": "list"
                },
                "volume_name": {
                    "type": "string",
                    "description": "Name of the volume"
                },
                "driver": {
                    "type": "string",
                    "description": "Volume driver"
                },
                "labels": {
                    "type": "object",
                    "description": "Labels for the volume",
                    "additionalProperties": {"type": "string"}
                },
                "force": {
                    "type": "boolean",
                    "description": "Force removal",
                    "default": False
                }
            },
            "required": []
        } 