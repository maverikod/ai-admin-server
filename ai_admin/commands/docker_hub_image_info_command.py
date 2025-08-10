"""Docker Hub image info command for detailed image information."""

import asyncio
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError


class DockerHubImageInfoCommand(Command):
    """Get detailed information about a specific Docker Hub image.
    
    This command retrieves comprehensive information about a Docker Hub image
    including metadata, tags, layers, and usage statistics.
    """
    
    name = "docker_hub_image_info"
    
    async def execute(
        self,
        image_name: str,
        tag: Optional[str] = None,
        include_layers: bool = False,
        include_usage: bool = False,
        **kwargs
    ) -> SuccessResult:
        """Execute Docker Hub image info command.
        
        Args:
            image_name: Full image name (e.g., 'library/nginx', 'myuser/myapp')
            tag: Specific tag to get info for (default: latest)
            include_layers: Include layer information
            include_usage: Include usage statistics
            
        Returns:
            Success result with detailed image information
        """
        try:
            # Validate inputs
            if not image_name:
                raise CommandError("Image name is required")
            
            # Normalize image name
            if not '/' in image_name:
                image_name = f"library/{image_name}"
            
            # Default to latest tag if not specified
            if not tag:
                tag = "latest"
            
            start_time = datetime.now()
            
            # Get repository information
            repo_info = await self._get_repository_info(image_name)
            
            # Get tag information
            tag_info = await self._get_tag_info(image_name, tag)
            
            # Get additional information if requested
            layers_info = None
            if include_layers and tag_info:
                layers_info = await self._get_layer_info(image_name, tag)
            
            usage_info = None
            if include_usage:
                usage_info = await self._get_usage_info(image_name)
            
            end_time = datetime.now()
            
            # Compile result
            result = {
                "image_name": image_name,
                "tag": tag,
                "repository": repo_info,
                "tag_info": tag_info,
                "layers": layers_info,
                "usage": usage_info,
                "timestamp": end_time.isoformat(),
                "execution_time_ms": (end_time - start_time).total_seconds() * 1000
            }
            
            return SuccessResult(data=result)
            
        except CommandError as e:
            return ErrorResult(
                message=str(e),
                code="HUB_IMAGE_INFO_ERROR",
                data=getattr(e, 'data', {})
            )
        except requests.RequestException as e:
            return ErrorResult(
                message=f"Network error during Docker Hub API request: {str(e)}",
                code="NETWORK_ERROR"
            )
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error getting Docker Hub image info: {str(e)}",
                code="INTERNAL_ERROR"
            )
    
    async def _get_repository_info(self, image_name: str) -> Dict[str, Any]:
        """Get repository information from Docker Hub."""
        try:
            api_url = f"https://hub.docker.com/v2/repositories/{image_name}/"
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                raise CommandError(
                    f"Failed to get repository info: {response.status_code}",
                    data={"status_code": response.status_code}
                )
            
            data = response.json()
            
            return {
                "name": data.get("name", ""),
                "full_name": data.get("full_name", ""),
                "description": data.get("description", ""),
                "is_official": data.get("is_official", False),
                "is_automated": data.get("is_automated", False),
                "star_count": data.get("star_count", 0),
                "pull_count": data.get("pull_count", 0),
                "last_updated": data.get("last_updated", ""),
                "affiliation": data.get("affiliation", ""),
                "user": data.get("user", ""),
                "namespace": data.get("namespace", ""),
                "repository_type": data.get("repository_type", ""),
                "status": data.get("status", ""),
                "has_starred": data.get("has_starred", False),
                "full_description": data.get("full_description", ""),
                "trust_status": data.get("trust_status", ""),
                "permissions": data.get("permissions", {})
            }
            
        except Exception as e:
            raise CommandError(f"Error getting repository info: {str(e)}")
    
    async def _get_tag_info(self, image_name: str, tag: str) -> Optional[Dict[str, Any]]:
        """Get specific tag information."""
        try:
            api_url = f"https://hub.docker.com/v2/repositories/{image_name}/tags/{tag}/"
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                return None
            
            if response.status_code != 200:
                raise CommandError(
                    f"Failed to get tag info: {response.status_code}",
                    data={"status_code": response.status_code}
                )
            
            data = response.json()
            
            return {
                "name": data.get("name", ""),
                "full_size": data.get("full_size", 0),
                "images": data.get("images", []),
                "id": data.get("id", ""),
                "repository": data.get("repository", 0),
                "creator": data.get("creator", 0),
                "last_updater": data.get("last_updater", 0),
                "last_updated": data.get("last_updated", ""),
                "image_id": data.get("image_id", ""),
                "v2": data.get("v2", True),
                "last_activity": data.get("last_activity", ""),
                "tag_last_pulled": data.get("tag_last_pulled", ""),
                "tag_last_pushed": data.get("tag_last_pushed", ""),
                "media_type": data.get("media_type", ""),
                "content_type": data.get("content_type", ""),
                "digest": data.get("digest", "")
            }
            
        except Exception as e:
            raise CommandError(f"Error getting tag info: {str(e)}")
    
    async def _get_layer_info(self, image_name: str, tag: str) -> Optional[List[Dict[str, Any]]]:
        """Get layer information for the image."""
        try:
            # Get manifest information
            api_url = f"https://hub.docker.com/v2/repositories/{image_name}/tags/{tag}/"
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            images = data.get("images", [])
            
            layers = []
            for image in images:
                layer_info = {
                    "architecture": image.get("architecture", ""),
                    "features": image.get("features", ""),
                    "variant": image.get("variant", ""),
                    "digest": image.get("digest", ""),
                    "os": image.get("os", ""),
                    "os_features": image.get("os_features", ""),
                    "os_version": image.get("os_version", ""),
                    "size": image.get("size", 0),
                    "status": image.get("status", ""),
                    "last_pulled": image.get("last_pulled", ""),
                    "last_pushed": image.get("last_pushed", "")
                }
                layers.append(layer_info)
            
            return layers
            
        except Exception:
            return None
    
    async def _get_usage_info(self, image_name: str) -> Optional[Dict[str, Any]]:
        """Get usage statistics for the image."""
        try:
            # Note: Docker Hub doesn't provide public API for detailed usage stats
            # This is a placeholder for future implementation
            return {
                "note": "Detailed usage statistics are not available via public API",
                "pull_count": "Available in repository info",
                "star_count": "Available in repository info"
            }
            
        except Exception:
            return None
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker Hub image info command parameters."""
        return {
            "type": "object",
            "properties": {
                "image_name": {
                    "type": "string",
                    "description": "Full image name (e.g., 'library/nginx', 'myuser/myapp')",
                    "examples": ["library/nginx", "library/ubuntu", "myuser/myapp", "nginx"]
                },
                "tag": {
                    "type": "string",
                    "description": "Specific tag to get info for",
                    "default": "latest",
                    "examples": ["latest", "1.21", "alpine", "stable"]
                },
                "include_layers": {
                    "type": "boolean",
                    "description": "Include layer information",
                    "default": False
                },
                "include_usage": {
                    "type": "boolean",
                    "description": "Include usage statistics",
                    "default": False
                }
            },
            "required": ["image_name"],
            "additionalProperties": False
        } 