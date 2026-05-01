"""Docker remove images command."""

from ai_admin.core.custom_exceptions import CustomError

"""Docker remove command for removing images.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""


import subprocess

from typing import Dict, Any, List, Optional

from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from ai_admin.security.docker_security_adapter import DockerSecurityAdapter


class DockerRemoveCommand:
    """Remove Docker images."""

    name = "docker_remove"

    def __init__(self):
        """Initialize Docker remove command."""
        super().__init__()
        self.security_adapter = DockerSecurityAdapter()

    async def execute(
        self,
        images: List[str],
        force: bool = False,
        no_prune: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker remove command with unified security.

        Args:
            images: List of image names or IDs to remove
            force: Force removal
            no_prune: Do not delete untagged parents
            user_roles: List of user roles for security validation

        Returns:
            Success result with removal information
        """
        # Validate inputs
        if not images:
            return ErrorResult(
                message="At least one image is required", code="VALIDATION_ERROR"
            )

        # Use unified security approach
        return await super().execute(
            images=images,
            force=force,
            no_prune=no_prune,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker remove command."""
        return "docker:remove"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker remove command logic."""
        return await self._remove_images(**kwargs)

    async def _remove_images(
        self,
        images: List[str],
        force: bool = False,
        no_prune: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Remove Docker images."""
        try:
            # Build Docker command
            cmd = ["docker", "rmi"]

            # Add options
            if force:
                cmd.append("--force")

            if no_prune:
                cmd.append("--no-prune")

            # Add images
            cmd.extend(images)

            # Execute remove command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise CustomError(f"Failed to remove Docker images: {result.stderr}")

            return {
                "message": f"Successfully removed {len(images)} Docker images",
                "images": images,
                "force": force,
                "no_prune": no_prune,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Docker remove command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Docker remove failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker remove command parameters."""
        return {
            "type": "object",
            "properties": {
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of image names or IDs to remove",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force removal",
                    "default": False,
                },
                "no_prune": {
                    "type": "boolean",
                    "description": "Do not delete untagged parents",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["images"],
            "additionalProperties": False,
        }
