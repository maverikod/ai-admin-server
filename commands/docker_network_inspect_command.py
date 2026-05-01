from ai_admin.core.custom_exceptions import InternalError
"""Docker network inspect command.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import json
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.docker_security_adapter import DockerSecurityAdapter

class DockerNetworkInspectCommand(BaseUnifiedCommand):
    """Inspect Docker network."""

    name = "docker_network_inspect"

    def __init__(self):
        """Initialize Docker network inspect command."""
        super().__init__()
        self.security_adapter = DockerSecurityAdapter()

    async def execute(
        self,
        network_name: str,
        format_output: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker network inspect command with unified security.

        Args:
            network_name: Name of the network to inspect
            format_output: Output format (json, go template)
            user_roles: List of user roles for security validation

        Returns:
            Success result with network inspection information
        """
        # Validate inputs
        if not network_name:
            return ErrorResult(message="Network name is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            network_name=network_name,
            format_output=format_output,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker network inspect command."""
        return "docker:network_inspect"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker network inspect command logic."""
        return await self._inspect_network(**kwargs)

    async def _inspect_network(
        self,
        network_name: str,
        format_output: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Inspect Docker network."""
        try:
            # Build Docker command
            cmd = ["docker", "network", "inspect"]

            # Add format if specified
            if format_output:
                cmd.extend(["--format", format_output])

            # Add network name
            cmd.append(network_name)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise InternalError(f"Failed to inspect Docker network: {result.stderr}")

            # Parse output
            try:
                if format_output:
                    # Custom format output
                    parsed_output = result.stdout.strip()
                else:
                    # JSON output
                    parsed_output = json.loads(result.stdout)
            except json.JSONDecodeError:
                parsed_output = result.stdout.strip()

            return {
                "message": f"Inspected Docker network '{network_name}'",
                "network_name": network_name,
                "format_output": format_output,
                "inspection_data": parsed_output,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise InternalError(f"Docker network inspect command timed out: {str(e)}")
        except InternalError as e:
            raise InternalError(f"Docker network inspect failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker network inspect command parameters."""
        return {
            "type": "object",
            "properties": {
                "network_name": {
                    "type": "string",
                    "description": "Name of the network to inspect",
                },
                "format_output": {
                    "type": "string",
                    "description": "Output format (json, go template)",
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
