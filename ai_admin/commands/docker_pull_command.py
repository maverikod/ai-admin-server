"""Docker pull image command."""

from ai_admin.core.custom_exceptions import CustomError

"""Docker pull command for downloading images from registries.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""


import subprocess

from typing import Dict, Any, Optional, List

from datetime import datetime

from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from ai_admin.security.docker_security_adapter import DockerSecurityAdapter

class DockerPullCommand:
    
    
    """Pull Docker images from registries like Docker Hub.
    
        This command downloads Docker images from container registries with
        support for multiple platforms and authentication.
        """
    
    
    name = "docker_pull"
    
    
    def __init__(self):
        """Initialize Docker pull command with unified security."""
        super().__init__()
        self.docker_security_adapter = DockerSecurityAdapter()
    
    
    def _get_default_operation(self) -> str:
        """Get default operation name for Docker pull command."""
        return "docker:pull"
    
    
    async def execute(
        self,
        image_name: str,
        tag: str = "latest",
        all_tags: bool = False,
        disable_content_trust: bool = False,
        quiet: bool = False,
        platform: Optional[str] = None,
        use_queue: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker pull command with unified security.
    
            Args:
                image_name: Name of the image to pull (e.g., 'nginx', 'username/myapp')
                tag: Tag to pull (default: 'latest')
                all_tags: Pull all tags of the image
                disable_content_trust: Skip image signature verification (default: False)
                quiet: Suppress verbose output
                platform: Target platform (e.g., 'linux/amd64', 'linux/arm64')
                use_queue: Use background queue for long-running operations
                user_roles: List of user roles for security validation
    
            Returns:
                Success result with pull information
            """
        # Validate inputs
        if not image_name:
            return ErrorResult(message="Image name is required", code="VALIDATION_ERROR")
    
        # Use unified security approach
        return await super().execute(
            image_name=image_name,
            tag=tag,
            all_tags=all_tags,
            disable_content_trust=disable_content_trust,
            quiet=quiet,
            platform=platform,
            use_queue=use_queue,
            user_roles=user_roles,
            **kwargs,
        )
    
    
    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker pull command logic."""
        return await self._pull_image(**kwargs)
    
    
    async def _pull_image(
        self,
        image_name: str,
        tag: str = "latest",
        all_tags: bool = False,
        disable_content_trust: bool = False,
        quiet: bool = False,
        platform: Optional[str] = None,
        use_queue: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Pull Docker image."""
        try:
            # Use queue for long-running operations if requested
            if use_queue:
                from ai_admin.task_queue.task_queue import TaskQueueManager, Task, TaskType
    
                queue_manager = TaskQueueManager()
    
                # Create task
                task = Task(
                    task_type=TaskType.DOCKER_PULL,
                    params={
                        "image_name": image_name,
                        "tag": tag,
                        "all_tags": all_tags,
                        "disable_content_trust": disable_content_trust,
                        "quiet": quiet,
                        "platform": platform,
                    },
                )
    
                # Add to global queue
                task_id = await queue_manager.add_task(task)
    
                return {
                    "status": "queued",
                    "message": "Docker pull task added to queue",
                    "task_id": task_id,
                    "image_name": image_name,
                    "tag": tag if not all_tags else "all",
                }
    
            # Construct full image name
            if all_tags:
                full_image_name = image_name
            else:
                full_image_name = f"{image_name}:{tag}"
    
            # Build Docker pull command
            cmd = ["docker", "pull"]
    
            # Add options
            if all_tags:
                cmd.append("--all-tags")
    
            if disable_content_trust:
                cmd.append("--disable-content-trust")
    
            if quiet:
                cmd.append("--quiet")
    
            if platform:
                cmd.extend(["--platform", platform])
    
            # Add image name
            cmd.append(full_image_name)
    
            # Execute pull command
            start_time = datetime.utcnow()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            end_time = datetime.utcnow()
            pull_duration = (end_time - start_time).total_seconds()
    
            if result.returncode != 0:
                raise CustomError(f"Failed to pull Docker image: {result.stderr}")
    
            # Parse output for size information
            size_info = {}
            layers_info = []
    
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "Pulling from" in line:
                        size_info["registry"] = line.split("Pulling from ")[1].split()[0]
                    elif "Digest:" in line:
                        size_info["digest"] = line.split("Digest: ")[1]
                    elif "Status:" in line and "Downloaded" in line:
                        # Extract size information
                        if "MB" in line or "GB" in line:
                            size_info["downloaded_size"] = line.split("Downloaded ")[1].split()[0]
                    elif "Status:" in line and "Pulling fs layer" in line:
                        layers_info.append("fs_layer")
                    elif "Status:" in line and "Downloading" in line:
                        layers_info.append("downloading")
                    elif "Status:" in line and "Extracting" in line:
                        layers_info.append("extracting")
    
            return {
                "message": f"Successfully pulled image '{full_image_name}'",
                "image_name": full_image_name,
                "registry": size_info.get("registry", "unknown"),
                "digest": size_info.get("digest", "unknown"),
                "pull_duration_seconds": pull_duration,
                "size_info": size_info,
                "layers_info": layers_info,
                "options": {
                    "all_tags": all_tags,
                    "disable_content_trust": disable_content_trust,
                    "quiet": quiet,
                    "platform": platform,
                },
                "command": " ".join(cmd),
                "timestamp": end_time.isoformat(),
            }
    
        except CustomError as e:
            raise CustomError(f"Docker pull failed: {str(e)}")
    
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker pull command parameters."""
        return {
            "type": "object",
            "properties": {
                "image_name": {
                    "type": "string",
                    "description": "Name of the image to pull (e.g., 'nginx', 'username/myapp')",
                    "pattern": "^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*$",
                    "examples": ["nginx", "myusername/myapp", "registry.com/namespace/app"],
                },
                "tag": {
                    "type": "string",
                    "description": "Tag to pull",
                    "default": "latest",
                    "examples": ["latest", "v1.0.0", "dev", "prod"],
                },
                "all_tags": {"type": "boolean", "description": "Pull all tags of the image", "default": False},
                "disable_content_trust": {
                    "type": "boolean",
                    "description": "Skip image signature verification",
                    "default": False,
                },
                "quiet": {"type": "boolean", "description": "Suppress verbose output", "default": False},
                "platform": {
                    "type": "string",
                    "description": "Target platform (e.g., 'linux/amd64', 'linux/arm64')",
                    "examples": ["linux/amd64", "linux/arm64", "linux/arm/v7"],
                },
                "use_queue": {
                    "type": "boolean",
                    "description": "Use background queue for long-running operations",
                    "default": True,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                    "examples": [["admin"], ["developer", "docker:pull"]],
                },
            },
            "required": ["image_name"],
            "additionalProperties": False,
        }
    