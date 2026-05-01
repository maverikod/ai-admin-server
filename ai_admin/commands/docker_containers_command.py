"""Docker containers list and management command."""

from ai_admin.core.custom_exceptions import CustomError

"""Docker containers listing command.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import json
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.docker_security_adapter import DockerSecurityAdapter


class DockerContainersCommand(BaseUnifiedCommand):
    """List Docker containers on the local system.

    This command displays information about Docker containers including
    container ID, image, command, created time, status, ports, and names.
    """

    name = "docker_containers"

    def __init__(self):
        """Initialize Docker containers command."""
        super().__init__()
        self.security_adapter = DockerSecurityAdapter()

    async def execute(
        self,
        all_containers: bool = False,
        size: bool = False,
        quiet: bool = False,
        no_trunc: bool = False,
        format_output: str = "table",
        filter_status: Optional[str] = None,
        filter_ancestor: Optional[str] = None,
        filter_before: Optional[str] = None,
        filter_since: Optional[str] = None,
        filter_label: Optional[Dict[str, str]] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker containers listing with unified security.

        Args:
            all_containers: Show all containers (default shows just running)
            size: Display total file sizes
            quiet: Only display container IDs
            no_trunc: Don't truncate output
            format_output: Output format (table, json, etc.)
            filter_status: Filter by container status
            filter_ancestor: Filter by ancestor image
            filter_before: Filter containers created before this container
            filter_since: Filter containers created since this container
            filter_label: Filter by label
            user_roles: List of user roles for security validation

        Returns:
            Success result with container information
        """
        # Use unified security approach
        return await super().execute(
            all_containers=all_containers,
            size=size,
            quiet=quiet,
            no_trunc=no_trunc,
            format_output=format_output,
            filter_status=filter_status,
            filter_ancestor=filter_ancestor,
            filter_before=filter_before,
            filter_since=filter_since,
            filter_label=filter_label,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker containers command."""
        return "docker:containers"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker containers listing logic."""
        return await self._list_containers(**kwargs)

    async def _list_containers(
        self,
        all_containers: bool = False,
        size: bool = False,
        quiet: bool = False,
        no_trunc: bool = False,
        format_output: str = "table",
        filter_status: Optional[str] = None,
        filter_ancestor: Optional[str] = None,
        filter_before: Optional[str] = None,
        filter_since: Optional[str] = None,
        filter_label: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """List Docker containers."""
        try:
            # Build Docker command
            cmd = ["docker", "ps"]

            # Add options
            if all_containers:
                cmd.append("-a")

            if size:
                cmd.append("-s")

            if quiet:
                cmd.append("-q")

            if no_trunc:
                cmd.append("--no-trunc")

            # Add format
            if format_output != "table":
                cmd.extend(["--format", format_output])

            # Add filters
            if filter_status:
                cmd.extend(["--filter", f"status={filter_status}"])

            if filter_ancestor:
                cmd.extend(["--filter", f"ancestor={filter_ancestor}"])

            if filter_before:
                cmd.extend(["--filter", f"before={filter_before}"])

            if filter_since:
                cmd.extend(["--filter", f"since={filter_since}"])

            if filter_label:
                for key, value in filter_label.items():
                    cmd.extend(["--filter", f"label={key}={value}"])

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Failed to list Docker containers: {result.stderr}")

            # Parse output
            containers = []
            if format_output == "json" or quiet:
                try:
                    containers = (
                        json.loads(result.stdout) if result.stdout.strip() else []
                    )
                except json.JSONDecodeError:
                    containers = [
                        {"id": line.strip()}
                        for line in result.stdout.strip().split("\n")
                        if line.strip()
                    ]
            else:
                # Parse table format
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    headers = lines[0].split()
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= len(headers):
                                container = dict(zip(headers, parts))
                                containers.append(container)

            return {
                "message": f"Found {len(containers)} Docker containers",
                "containers": containers,
                "count": len(containers),
                "all_containers": all_containers,
                "size": size,
                "quiet": quiet,
                "format_output": format_output,
                "filters": {
                    "status": filter_status,
                    "ancestor": filter_ancestor,
                    "before": filter_before,
                    "since": filter_since,
                    "label": filter_label,
                },
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Docker containers command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Docker containers listing failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker containers command parameters."""
        return {
            "type": "object",
            "properties": {
                "all_containers": {
                    "type": "boolean",
                    "description": "Show all containers (default shows just running)",
                    "default": False,
                },
                "size": {
                    "type": "boolean",
                    "description": "Display total file sizes",
                    "default": False,
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Only display container IDs",
                    "default": False,
                },
                "no_trunc": {
                    "type": "boolean",
                    "description": "Don't truncate output",
                    "default": False,
                },
                "format_output": {
                    "type": "string",
                    "description": "Output format",
                    "default": "table",
                },
                "filter_status": {
                    "type": "string",
                    "description": "Filter by container status",
                },
                "filter_ancestor": {
                    "type": "string",
                    "description": "Filter by ancestor image",
                },
                "filter_before": {
                    "type": "string",
                    "description": "Filter containers created before this container",
                },
                "filter_since": {
                    "type": "string",
                    "description": "Filter containers created since this container",
                },
                "filter_label": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Filter by label",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
