"""Docker network connect command."""
from ai_admin.core.custom_exceptions import NetworkError
"""Docker network connect command.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.docker_security_adapter import DockerSecurityAdapter

class DockerNetworkConnectCommand(BaseUnifiedCommand):
    """Connect container to Docker network."""

    name = "docker_network_connect"

    def __init__(self):
        """Initialize Docker network connect command."""
        super().__init__()
        self.security_adapter = DockerSecurityAdapter()

    async def execute(
        self,
        network_name: str,
        container_name: str,
        ip_address: Optional[str] = None,
        alias: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker network connect command with unified security.

        Args:
            network_name: Name of the Docker network
            container_name: Name of the container to connect
            ip_address: IP address for the container in the network
            alias: Network alias for the container
            user_roles: List of user roles for security validation

        Returns:
            Success result with connection information
        """
        # Validate inputs
        if not network_name or not container_name:
            return ErrorResult(message="Network name and container name are required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            network_name=network_name,
            container_name=container_name,
            ip_address=ip_address,
            alias=alias,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker network connect command."""
        return "docker:network_connect"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker network connect command logic."""
        return await self._connect_to_network(**kwargs)

    async def _connect_to_network(
        self,
        network_name: str,
        container_name: str,
        ip_address: Optional[str] = None,
        alias: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Connect container to Docker network."""
        try:
            # Build Docker command
            cmd = ["docker", "network", "connect"]

            # Add options
            if ip_address:
                cmd.extend(["--ip", ip_address])

            if alias:
                cmd.extend(["--alias", alias])

            # Add network and container names
            cmd.append(network_name)
            cmd.append(container_name)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise NetworkError(f"Failed to connect container to network: {result.stderr}")

            return {
                "message": f"Connected container '{container_name}' to network '{network_name}'",
                "network_name": network_name,
                "container_name": container_name,
                "ip_address": ip_address,
                "alias": alias,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise NetworkError(f"Docker network connect command timed out: {str(e)}")
        except NetworkError as e:
            raise NetworkError(f"Docker network connect failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker network connect command parameters."""
        return {
            "type": "object",
            "properties": {
                "network_name": {
                    "type": "string",
                    "description": "Name of the Docker network",
                },
                "container_name": {
                    "type": "string",
                    "description": "Name of the container to connect",
                },
                "ip_address": {
                    "type": "string",
                    "description": "IP address for the container in the network",
                },
                "alias": {
                    "type": "string",
                    "description": "Network alias for the container",
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
