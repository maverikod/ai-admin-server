"""Docker network disconnect command."""

from ai_admin.core.custom_exceptions import NetworkError

"""Docker network disconnect command.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""


import subprocess

from typing import Dict, Any, Optional, List

from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from ai_admin.security.docker_security_adapter import DockerSecurityAdapter


class DockerNetworkDisconnectCommand:
    """Disconnect container from Docker network."""

    name = "docker_network_disconnect"

    def __init__(self):
        """Initialize Docker network disconnect command."""
        super().__init__()
        self.security_adapter = DockerSecurityAdapter()

    async def execute(
        self,
        network_name: str,
        container_name: str,
        force: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker network disconnect command with unified security.

        Args:
            network_name: Name of the Docker network
            container_name: Name of the container to disconnect
            force: Force disconnection
            user_roles: List of user roles for security validation

        Returns:
            Success result with disconnection information
        """
        # Validate inputs
        if not network_name or not container_name:
            return ErrorResult(
                message="Network name and container name are required",
                code="VALIDATION_ERROR",
            )

        # Use unified security approach
        return await super().execute(
            network_name=network_name,
            container_name=container_name,
            force=force,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker network disconnect command."""
        return "docker:network_disconnect"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker network disconnect command logic."""
        return await self._disconnect_from_network(**kwargs)

    async def _disconnect_from_network(
        self,
        network_name: str,
        container_name: str,
        force: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Disconnect container from Docker network."""
        try:
            # Build Docker command
            cmd = ["docker", "network", "disconnect"]

            # Add options
            if force:
                cmd.append("--force")

            # Add network and container names
            cmd.append(network_name)
            cmd.append(container_name)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise NetworkError(
                    f"Failed to disconnect container from network: {result.stderr}"
                )

            return {
                "message": f"Disconnected container '{container_name}' from network '{network_name}'",
                "network_name": network_name,
                "container_name": container_name,
                "force": force,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise NetworkError(f"Docker network disconnect command timed out: {str(e)}")
        except NetworkError as e:
            raise NetworkError(f"Docker network disconnect failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker network disconnect command parameters."""
        return {
            "type": "object",
            "properties": {
                "network_name": {
                    "type": "string",
                    "description": "Name of the Docker network",
                },
                "container_name": {
                    "type": "string",
                    "description": "Name of the container to disconnect",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force disconnection",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["network_name", "container_name"],
            "additionalProperties": False,
        }
