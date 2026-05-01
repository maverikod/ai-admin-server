from ai_admin.core.custom_exceptions import CustomError

"""Docker volume command for managing volumes.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""


import subprocess

import json

from typing import Dict, Any, Optional, List

from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from ai_admin.security.docker_security_adapter import DockerSecurityAdapter


class DockerVolumeCommand:
    """Manage Docker volumes."""

    name = "docker_volume"

    def __init__(self):
        """Initialize Docker volume command."""
        super().__init__()
        self.security_adapter = DockerSecurityAdapter()

    async def execute(
        self,
        action: str = "list",
        volume_name: Optional[str] = None,
        driver: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker volume command with unified security.

        Args:
            action: Volume action (list, create, remove, inspect)
            volume_name: Name of the volume
            driver: Volume driver
            labels: Volume labels
            user_roles: List of user roles for security validation

        Returns:
            Success result with volume information
        """
        # Validate inputs
        if action in ["create", "remove", "inspect"] and not volume_name:
            return ErrorResult(
                message="Volume name is required for this action",
                code="VALIDATION_ERROR",
            )

        # Use unified security approach
        return await super().execute(
            action=action,
            volume_name=volume_name,
            driver=driver,
            labels=labels,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker volume command."""
        return "docker:volume"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker volume command logic."""
        return await self._manage_volume(**kwargs)

    async def _manage_volume(
        self,
        action: str = "list",
        volume_name: Optional[str] = None,
        driver: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Manage Docker volume."""
        try:
            if action == "list":
                return await self._list_volumes()
            elif action == "create":
                return await self._create_volume(volume_name, driver, labels)
            elif action == "remove":
                return await self._remove_volume(volume_name)
            elif action == "inspect":
                return await self._inspect_volume(volume_name)
            else:
                raise CustomError(f"Unknown volume action: {action}")

        except CustomError as e:
            raise CustomError(f"Docker volume {action} failed: {str(e)}")

    async def _list_volumes(self) -> Dict[str, Any]:
        """List Docker volumes."""
        try:
            cmd = ["docker", "volume", "ls", "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Failed to list volumes: {result.stderr}")

            volumes = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        volume = json.loads(line)
                        volumes.append(volume)
                    except json.JSONDecodeError:
                        continue

            return {
                "message": f"Found {len(volumes)} Docker volumes",
                "action": "list",
                "volumes": volumes,
                "count": len(volumes),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Volume list command timed out: {str(e)}")

    async def _create_volume(
        self,
        volume_name: str,
        driver: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create Docker volume."""
        try:
            cmd = ["docker", "volume", "create"]

            if driver:
                cmd.extend(["--driver", driver])

            if labels:
                for key, value in labels.items():
                    cmd.extend(["--label", f"{key}={value}"])

            cmd.append(volume_name)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Failed to create volume: {result.stderr}")

            return {
                "message": f"Successfully created volume '{volume_name}'",
                "action": "create",
                "volume_name": volume_name,
                "driver": driver,
                "labels": labels,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Volume create command timed out: {str(e)}")

    async def _remove_volume(self, volume_name: str) -> Dict[str, Any]:
        """Remove Docker volume."""
        try:
            cmd = ["docker", "volume", "rm", volume_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Failed to remove volume: {result.stderr}")

            return {
                "message": f"Successfully removed volume '{volume_name}'",
                "action": "remove",
                "volume_name": volume_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Volume remove command timed out: {str(e)}")

    async def _inspect_volume(self, volume_name: str) -> Dict[str, Any]:
        """Inspect Docker volume."""
        try:
            cmd = ["docker", "volume", "inspect", volume_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Failed to inspect volume: {result.stderr}")

            volume_data = json.loads(result.stdout)

            return {
                "message": f"Inspected volume '{volume_name}'",
                "action": "inspect",
                "volume_name": volume_name,
                "volume_data": volume_data,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Volume inspect command timed out: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker volume command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Volume action (list, create, remove, inspect)",
                    "default": "list",
                },
                "volume_name": {
                    "type": "string",
                    "description": "Name of the volume",
                },
                "driver": {
                    "type": "string",
                    "description": "Volume driver",
                },
                "labels": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Volume labels",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }


"""Module description."""
