"""Docker images compare command."""

from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import CustomError

"""Docker images comparison command.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import requests
import json
from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.docker_security_adapter import DockerSecurityAdapter


class DockerImagesCompareCommand(BaseUnifiedCommand):
    """Compare local Docker images with remote Docker Hub images.

    This command compares local Docker images with their remote counterparts
    on Docker Hub, showing differences in tags, sizes, and update status.
    """

    name = "docker_images_compare"

    def __init__(self):
        """Initialize Docker images compare command."""
        super().__init__()
        self.security_adapter = DockerSecurityAdapter()

    async def execute(
        self,
        image_name: Optional[str] = None,
        include_all_local: bool = False,
        check_updates: bool = True,
        include_dangling: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker images comparison with unified security.

        Args:
            image_name: Specific image name to compare
            include_all_local: Include all local images
            check_updates: Check for updates on Docker Hub
            include_dangling: Include dangling images
            user_roles: List of user roles for security validation

        Returns:
            Success result with comparison information
        """
        # Use unified security approach
        return await super().execute(
            image_name=image_name,
            include_all_local=include_all_local,
            check_updates=check_updates,
            include_dangling=include_dangling,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker images compare command."""
        return "docker:images_compare"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker images comparison logic."""
        return await self._compare_images(**kwargs)

    async def _compare_images(
        self,
        image_name: Optional[str] = None,
        include_all_local: bool = False,
        check_updates: bool = True,
        include_dangling: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Compare local and remote Docker images."""
        try:
            # Get local images
            local_cmd = ["docker", "images", "--format", "json"]
            if include_dangling:
                local_cmd.append("-a")

            if image_name:
                local_cmd.append(image_name)

            local_result = subprocess.run(
                local_cmd, capture_output=True, text=True, timeout=30
            )

            if local_result.returncode != 0:
                raise CustomError(f"Failed to get local images: {local_result.stderr}")

            # Parse local images
            local_images = []
            for line in local_result.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        local_images.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            # Compare with remote if requested
            comparison_results = []
            if check_updates:
                for local_image in local_images:
                    repo_name = local_image.get("Repository", "")
                    tag = local_image.get("Tag", "latest")

                    if repo_name and not repo_name.startswith("<none>"):
                        try:
                            # Get remote image info
                            remote_info = await self._get_remote_image_info(
                                repo_name, tag
                            )

                            comparison = {
                                "repository": repo_name,
                                "tag": tag,
                                "local": {
                                    "id": local_image.get("ID"),
                                    "created": local_image.get("CreatedAt"),
                                    "size": local_image.get("Size"),
                                },
                                "remote": remote_info,
                                "has_update": remote_info.get("last_updated")
                                != local_image.get("CreatedAt"),
                            }
                            comparison_results.append(comparison)
                        except CustomError as e:
                            comparison_results.append(
                                {
                                    "repository": repo_name,
                                    "tag": tag,
                                    "local": {
                                        "id": local_image.get("ID"),
                                        "created": local_image.get("CreatedAt"),
                                        "size": local_image.get("Size"),
                                    },
                                    "remote": None,
                                    "error": str(e),
                                }
                            )

            return {
                "message": f"Compared {len(local_images)} local images",
                "local_images": local_images,
                "comparison_results": comparison_results,
                "local_count": len(local_images),
                "compared_count": len(comparison_results),
                "image_name": image_name,
                "include_all_local": include_all_local,
                "check_updates": check_updates,
                "include_dangling": include_dangling,
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Docker images comparison timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Docker images comparison failed: {str(e)}")

    async def _get_remote_image_info(self, repo_name: str, tag: str) -> Dict[str, Any]:
        """Get remote image information from Docker Hub."""
        try:
            api_url = f"https://hub.docker.com/v2/repositories/{repo_name}/tags/{tag}"
            response = requests.get(api_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "last_updated": data.get("last_updated"),
                    "images": data.get("images", []),
                    "size": data.get("full_size"),
                }
            else:
                return {"error": f"Remote image not found: {response.status_code}"}

        except requests.RequestException as e:
            return {"error": f"Failed to get remote info: {str(e)}"}

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker images compare command parameters."""
        return {
            "type": "object",
            "properties": {
                "image_name": {
                    "type": "string",
                    "description": "Specific image name to compare",
                },
                "include_all_local": {
                    "type": "boolean",
                    "description": "Include all local images",
                    "default": False,
                },
                "check_updates": {
                    "type": "boolean",
                    "description": "Check for updates on Docker Hub",
                    "default": True,
                },
                "include_dangling": {
                    "type": "boolean",
                    "description": "Include dangling images",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
