"""Docker pull command for downloading images from registries."""

import asyncio
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class DockerPullCommand(Command):
    """Pull Docker images from registries like Docker Hub.
    
    This command downloads Docker images from container registries with
    support for multiple platforms and authentication.
    """
    
    name = "docker_pull"
    
    async def execute(
        self,
        image_name: str,
        tag: str = "latest",
        all_tags: bool = False,
        disable_content_trust: bool = False,
        quiet: bool = False,
        platform: Optional[str] = None,
        use_queue: bool = True,
        **kwargs
    ) -> SuccessResult:
        """Execute Docker pull command.
        
        Args:
            image_name: Name of the image to pull (e.g., 'nginx', 'username/myapp')
            tag: Tag to pull (default: 'latest')
            all_tags: Pull all tags of the image
            disable_content_trust: Skip image signature verification (default: False)
            quiet: Suppress verbose output
            platform: Target platform (e.g., 'linux/amd64', 'linux/arm64')
            
        Returns:
            Success result with pull information
        """
        try:
            # Validate inputs
            if not image_name:
                raise ValidationError("Image name is required")
            
            # Use queue for long-running operations
            if use_queue:
                from ai_admin.queue.task_queue import Task, TaskType, TaskStatus
                from ai_admin.queue.queue_manager import queue_manager
                
                # Create task
                task = Task(
                    task_type=TaskType.DOCKER_PULL,
                    params={
                        "image_name": image_name,
                        "tag": tag,
                        "all_tags": all_tags,
                        "disable_content_trust": disable_content_trust,
                        "quiet": quiet,
                        "platform": platform
                    }
                )
                
                # Add to global queue
                task_id = await queue_manager.add_task(task)
                
                return SuccessResult(data={
                    "status": "queued",
                    "message": "Docker pull task added to queue",
                    "task_id": task_id,
                    "image_name": image_name,
                    "tag": tag if not all_tags else "all"
                })
            
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
            start_time = datetime.now()
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            end_time = datetime.now()
            pull_duration = (end_time - start_time).total_seconds()
            
            if process.returncode != 0:
                error_output = stderr.decode('utf-8')
                raise CommandError(
                    f"Docker pull failed with exit code {process.returncode}",
                    data={
                        "stderr": error_output,
                        "stdout": stdout.decode('utf-8'),
                        "command": " ".join(cmd),
                        "exit_code": process.returncode
                    }
                )
            
            # Parse output for digest and size information
            output_lines = stdout.decode('utf-8').splitlines()
            digest = None
            size_info = []
            layers_info = []
            
            for line in output_lines:
                if "digest:" in line:
                    digest = line.split("digest: ")[-1].strip()
                elif "Pulled" in line or "Mounted" in line:
                    size_info.append(line.strip())
                elif "Downloading" in line or "Extracting" in line:
                    layers_info.append(line.strip())
            
            return SuccessResult(data={
                "status": "success",
                "message": "Docker image pulled successfully",
                "image_name": image_name,
                "tag": tag if not all_tags else "all",
                "full_image_name": full_image_name,
                "digest": digest,
                "pull_duration_seconds": pull_duration,
                "size_info": size_info,
                "layers_info": layers_info,
                "options": {
                    "all_tags": all_tags,
                    "disable_content_trust": disable_content_trust,
                    "quiet": quiet,
                    "platform": platform
                },
                "command": " ".join(cmd),
                "timestamp": end_time.isoformat()
            })
            
        except ValidationError as e:
            return ErrorResult(
                message=str(e),
                code="VALIDATION_ERROR"
            )
        except CommandError as e:
            return ErrorResult(
                message=str(e),
                code="PULL_ERROR"
            )
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during Docker pull: {str(e)}",
                code="INTERNAL_ERROR"
            )
    
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
                    "examples": ["nginx", "myusername/myapp", "registry.com/namespace/app"]
                },
                "tag": {
                    "type": "string",
                    "description": "Tag to pull",
                    "default": "latest",
                    "examples": ["latest", "v1.0.0", "dev", "prod"]
                },
                "all_tags": {
                    "type": "boolean",
                    "description": "Pull all tags of the image",
                    "default": False
                },
                "disable_content_trust": {
                    "type": "boolean",
                    "description": "Skip image signature verification",
                    "default": False
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Suppress verbose output",
                    "default": False
                },
                "platform": {
                    "type": "string",
                    "description": "Target platform (e.g., 'linux/amd64', 'linux/arm64')",
                    "examples": ["linux/amd64", "linux/arm64", "linux/arm/v7"]
                }
            },
            "required": ["image_name"],
            "additionalProperties": False
        } 