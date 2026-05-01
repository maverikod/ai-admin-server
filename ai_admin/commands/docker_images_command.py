"""Docker images list command."""

from ai_admin.core.custom_exceptions import CustomError

"""Docker images listing command.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import json
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.docker_security_adapter import DockerSecurityAdapter


class DockerImagesCommand(BaseUnifiedCommand):
    """List Docker images on the local system.

    This command displays information about Docker images including
    repository, tag, image ID, creation time, and size.
    """

    name = "docker_images"

    def __init__(self):
        """Initialize Docker images command."""
        super().__init__()
        self.security_adapter = DockerSecurityAdapter()

    async def execute(
        self,
        repository: Optional[str] = None,
        all_images: bool = False,
        quiet: bool = False,
        no_trunc: bool = False,
        format_output: str = "table",
        filter_dangling: Optional[bool] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker images listing with unified security.

        Args:
            repository: Filter by repository name
            all_images: Show all images (including intermediate)
            quiet: Only display image IDs
            no_trunc: Don't truncate output
            format_output: Output format (table, json, etc.)
            filter_dangling: Filter dangling images
            user_roles: List of user roles for security validation

        Returns:
            Success result with images information
        """
        # Use unified security approach
        return await super().execute(
            repository=repository,
            all_images=all_images,
            quiet=quiet,
            no_trunc=no_trunc,
            format_output=format_output,
            filter_dangling=filter_dangling,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker images command."""
        return "docker:images"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker images listing logic."""
        return await self._list_images(**kwargs)

    async def _list_images(
        self,
        repository: Optional[str] = None,
        all_images: bool = False,
        quiet: bool = False,
        no_trunc: bool = False,
        format_output: str = "table",
        filter_dangling: Optional[bool] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """List Docker images."""
        try:
            # Build Docker command
            cmd = ["docker", "images"]

            # Add options
            if all_images:
                cmd.append("-a")

            if quiet:
                cmd.append("-q")

            if no_trunc:
                cmd.append("--no-trunc")

            # Add format
            if format_output != "table":
                cmd.extend(["--format", format_output])

            # Add filters
            if filter_dangling is not None:
                if filter_dangling:
                    cmd.append("--filter")
                    cmd.append("dangling=true")
                else:
                    cmd.append("--filter")
                    cmd.append("dangling=false")

            # Add repository filter
            if repository:
                cmd.append(repository)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Failed to list Docker images: {result.stderr}")

            # Parse output
            images = []
            if format_output == "json" or quiet:
                try:
                    images = json.loads(result.stdout) if result.stdout.strip() else []
                except json.JSONDecodeError:
                    images = [
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
                                image = dict(zip(headers, parts))
                                images.append(image)

            return {
                "message": f"Found {len(images)} Docker images",
                "images": images,
                "count": len(images),
                "repository": repository,
                "all_images": all_images,
                "quiet": quiet,
                "format_output": format_output,
                "filter_dangling": filter_dangling,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Docker images command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Docker images listing failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker images command parameters."""
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Filter by repository name",
                },
                "all_images": {
                    "type": "boolean",
                    "description": "Show all images (including intermediate)",
                    "default": False,
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Only display image IDs",
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
                "filter_dangling": {
                    "type": "boolean",
                    "description": "Filter dangling images",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
