from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Docker start command for starting containers.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.docker_security_adapter import DockerSecurityAdapter

class DockerStartCommand(BaseUnifiedCommand):
    """Start Docker container."""

    name = "docker_start"

    def __init__(self):
        """Initialize Docker start command."""
        super().__init__()
        self.security_adapter = DockerSecurityAdapter()

    async def execute(
        self,
        container_name: str,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker start command with unified security.

        Args:
            container_name: Name or ID of the container to start
            user_roles: List of user roles for security validation

        Returns:
            Success result with start information
        """
        # Validate inputs
        if not container_name:
            return ErrorResult(message="Container name is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            container_name=container_name,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker start command."""
        return "docker:start"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker start command logic."""
        return await self._start_container(**kwargs)

    async def _start_container(
        self,
        container_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Start Docker container."""
        try:
            # Build Docker command
            cmd = ["docker", "start", container_name]

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Failed to start Docker container: {result.stderr}")

            return {
                "message": f"Successfully started container '{container_name}'",
                "container_name": container_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Docker start command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Docker start failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker start command parameters."""
        return {
            "type": "object",
            "properties": {
                "container_name": {
                    "type": "string",
                    "description": "Name or ID of the container to start",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["container_name"],
            "additionalProperties": False,
        }
