from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Docker logs command for viewing container logs.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand

class DockerLogsCommand(BaseUnifiedCommand):
    """View Docker container logs."""

    name = "docker_logs"

    def __init__(self):
        """Initialize Docker logs command."""
        super().__init__()

    async def execute(
        self,
        container_name: str,
        follow: bool = False,
        tail: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        timestamps: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker logs command with unified security.

        Args:
            container_name: Name or ID of the container
            follow: Follow log output
            tail: Number of lines to show from the end
            since: Show logs since timestamp
            until: Show logs until timestamp
            timestamps: Show timestamps
            user_roles: List of user roles for security validation

        Returns:
            Success result with logs information
        """
        # Validate inputs
        if not container_name:
            return ErrorResult(message="Container name is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            container_name=container_name,
            follow=follow,
            tail=tail,
            since=since,
            until=until,
            timestamps=timestamps,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker logs command."""
        return "docker:logs"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker logs command logic."""
        return await self._get_logs(**kwargs)

    async def _get_logs(
        self,
        container_name: str,
        follow: bool = False,
        tail: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        timestamps: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get Docker container logs."""
        try:
            # Build Docker command
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

            # Add container name
            cmd.append(container_name)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Failed to get Docker logs: {result.stderr}")

            return {
                "message": f"Retrieved logs for container '{container_name}'",
                "container_name": container_name,
                "follow": follow,
                "tail": tail,
                "since": since,
                "until": until,
                "timestamps": timestamps,
                "logs": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Docker logs command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Docker logs failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker logs command parameters."""
        return {
            "type": "object",
            "properties": {
                "container_name": {
                    "type": "string",
                    "description": "Name or ID of the container",
                },
                "follow": {
                    "type": "boolean",
                    "description": "Follow log output",
                    "default": False,
                },
                "tail": {
                    "type": "integer",
                    "description": "Number of lines to show from the end",
                },
                "since": {
                    "type": "string",
                    "description": "Show logs since timestamp",
                },
                "until": {
                    "type": "string",
                    "description": "Show logs until timestamp",
                },
                "timestamps": {
                    "type": "boolean",
                    "description": "Show timestamps",
                    "default": False,
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
