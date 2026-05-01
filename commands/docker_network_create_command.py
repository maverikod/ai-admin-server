from ai_admin.core.custom_exceptions import InternalError
"""Docker network create command.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.docker_security_adapter import DockerSecurityAdapter

class DockerNetworkCreateCommand(BaseUnifiedCommand):
    """Create Docker network."""

    name = "docker_network_create"

    def __init__(self):
        """Initialize Docker network create command."""
        super().__init__()
        self.security_adapter = DockerSecurityAdapter()

    async def execute(
        self,
        network_name: str,
        driver: str = "bridge",
        subnet: Optional[str] = None,
        gateway: Optional[str] = None,
        internal: bool = False,
        ipv6: bool = False,
        labels: Optional[Dict[str, str]] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker network create command with unified security.

        Args:
            network_name: Name of the network to create
            driver: Network driver (bridge, overlay, macvlan, etc.)
            subnet: Subnet in CIDR format
            gateway: Gateway IP address
            internal: Create internal network
            ipv6: Enable IPv6
            labels: Network labels
            user_roles: List of user roles for security validation

        Returns:
            Success result with network creation information
        """
        # Validate inputs
        if not network_name:
            return ErrorResult(message="Network name is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            network_name=network_name,
            driver=driver,
            subnet=subnet,
            gateway=gateway,
            internal=internal,
            ipv6=ipv6,
            labels=labels,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker network create command."""
        return "docker:network_create"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker network create command logic."""
        return await self._create_network(**kwargs)

    async def _create_network(
        self,
        network_name: str,
        driver: str = "bridge",
        subnet: Optional[str] = None,
        gateway: Optional[str] = None,
        internal: bool = False,
        ipv6: bool = False,
        labels: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create Docker network."""
        try:
            # Build Docker command
            cmd = ["docker", "network", "create"]

            # Add options
            if driver != "bridge":
                cmd.extend(["--driver", driver])

            if subnet:
                cmd.extend(["--subnet", subnet])

            if gateway:
                cmd.extend(["--gateway", gateway])

            if internal:
                cmd.append("--internal")

            if ipv6:
                cmd.append("--ipv6")

            if labels:
                for key, value in labels.items():
                    cmd.extend(["--label", f"{key}={value}"])

            # Add network name
            cmd.append(network_name)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise InternalError(f"Failed to create Docker network: {result.stderr}")

            network_id = result.stdout.strip()

            return {
                "message": f"Created Docker network '{network_name}'",
                "network_name": network_name,
                "network_id": network_id,
                "driver": driver,
                "subnet": subnet,
                "gateway": gateway,
                "internal": internal,
                "ipv6": ipv6,
                "labels": labels,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise InternalError(f"Docker network create command timed out: {str(e)}")
        except InternalError as e:
            raise InternalError(f"Docker network create failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker network create command parameters."""
        return {
            "type": "object",
            "properties": {
                "network_name": {
                    "type": "string",
                    "description": "Name of the network to create",
                },
                "driver": {
                    "type": "string",
                    "description": "Network driver",
                    "default": "bridge",
                },
                "subnet": {
                    "type": "string",
                    "description": "Subnet in CIDR format",
                },
                "gateway": {
                    "type": "string",
                    "description": "Gateway IP address",
                },
                "internal": {
                    "type": "boolean",
                    "description": "Create internal network",
                    "default": False,
                },
                "ipv6": {
                    "type": "boolean",
                    "description": "Enable IPv6",
                    "default": False,
                },
                "labels": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Network labels",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["network_name"],
            "additionalProperties": False,
        }
