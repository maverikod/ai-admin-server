"""Docker images compare command for comparing local and remote images."""

import asyncio
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError


class DockerImagesCompareCommand(Command):
    """Compare local Docker images with remote Docker Hub images.
    
    This command compares local Docker images with their remote counterparts
    on Docker Hub, showing differences in tags, sizes, and update status.
    """
    
    name = "docker_images_compare"
    
    async def execute(
        self,
        image_name: Optional[str] = None,
        include_all_local: bool = False,
        check_updates: bool = True,
        include_dangling: bool = False,
        **kwargs
    ) -> SuccessResult:
        """Execute Docker images compare command.
        
        Args:
            image_name: Specific image name to compare (e.g., 'nginx', 'ubuntu')
            include_all_local: Compare all local images
            check_updates: Check for available updates
            include_dangling: Include dangling images in comparison
            
        Returns:
            Success result with comparison information
        """
        try:
            start_time = datetime.now()
            
            # Get local images
            local_images = await self._get_local_images(
                image_name=image_name,
                include_all=include_all_local,
                include_dangling=include_dangling
            )
            
            # Get remote images for comparison
            comparison_results = []
            
            for local_img in local_images:
                repo_name = local_img.get("repository", "")
                if repo_name and repo_name != "<none>":
                    # Get remote info
                    remote_info = await self._get_remote_image_info(repo_name)
                    
                    # Compare versions
                    comparison = self._compare_image_versions(local_img, remote_info)
                    comparison_results.append(comparison)
                else:
                    # Dangling or invalid image
                    comparison_results.append({
                        "local_image": local_img,
                        "remote_info": None,
                        "comparison": {
                            "status": "dangling_or_invalid",
                            "has_remote": False,
                            "update_available": False,
                            "differences": []
                        }
                    })
            
            end_time = datetime.now()
            
            return SuccessResult(data={
                "status": "success",
                "image_name": image_name,
                "total_local_images": len(local_images),
                "compared_images": len(comparison_results),
                "comparison_results": comparison_results,
                "summary": self._generate_summary(comparison_results),
                "timestamp": end_time.isoformat(),
                "execution_time_ms": (end_time - start_time).total_seconds() * 1000
            })
            
        except CommandError as e:
            return ErrorResult(
                message=str(e),
                code="IMAGES_COMPARE_ERROR",
                data=getattr(e, 'data', {})
            )
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error comparing Docker images: {str(e)}",
                code="INTERNAL_ERROR"
            )
    
    async def _get_local_images(
        self,
        image_name: Optional[str] = None,
        include_all: bool = False,
        include_dangling: bool = False
    ) -> List[Dict[str, Any]]:
        """Get local Docker images."""
        try:
            cmd = ["docker", "images", "--format", "json"]
            
            if include_all:
                cmd.append("-a")
            
            if not include_dangling:
                cmd.extend(["--filter", "dangling=false"])
            
            if image_name:
                cmd.append(image_name)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise CommandError(
                    f"Failed to get local images: {stderr.decode('utf-8')}",
                    data={"exit_code": process.returncode}
                )
            
            output = stdout.decode('utf-8').strip()
            images = []
            
            if output:
                for line in output.splitlines():
                    try:
                        image_data = json.loads(line)
                        images.append(image_data)
                    except json.JSONDecodeError:
                        continue
            
            return images
            
        except Exception as e:
            raise CommandError(f"Error getting local images: {str(e)}")
    
    async def _get_remote_image_info(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """Get remote image information from Docker Hub."""
        try:
            # Normalize repository name
            if not '/' in repo_name:
                repo_name = f"library/{repo_name}"
            
            api_url = f"https://hub.docker.com/v2/repositories/{repo_name}/"
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Get tags information
            tags_url = f"https://hub.docker.com/v2/repositories/{repo_name}/tags/"
            tags_response = requests.get(tags_url, headers=headers, timeout=10)
            
            tags = []
            if tags_response.status_code == 200:
                tags_data = tags_response.json()
                for tag in tags_data.get("results", [])[:10]:  # Limit to 10 tags
                    tags.append({
                        "name": tag.get("name", ""),
                        "last_updated": tag.get("last_updated", ""),
                        "full_size": tag.get("full_size", 0)
                    })
            
            return {
                "name": data.get("name", ""),
                "full_name": data.get("full_name", ""),
                "description": data.get("description", ""),
                "is_official": data.get("is_official", False),
                "star_count": data.get("star_count", 0),
                "pull_count": data.get("pull_count", 0),
                "last_updated": data.get("last_updated", ""),
                "tags": tags
            }
            
        except Exception:
            return None
    
    def _compare_image_versions(
        self,
        local_image: Dict[str, Any],
        remote_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare local and remote image versions."""
        if not remote_info:
            return {
                "local_image": local_image,
                "remote_info": None,
                "comparison": {
                    "status": "no_remote_found",
                    "has_remote": False,
                    "update_available": False,
                    "differences": []
                }
            }
        
        local_tag = local_image.get("Tag", "")
        local_created = local_image.get("CreatedAt", "")
        local_size = local_image.get("Size", "")
        
        # Find matching remote tag
        remote_tag_info = None
        for tag in remote_info.get("tags", []):
            if tag.get("name") == local_tag:
                remote_tag_info = tag
                break
        
        differences = []
        update_available = False
        
        if remote_tag_info:
            remote_updated = remote_tag_info.get("last_updated", "")
            remote_size = remote_tag_info.get("full_size", 0)
            
            # Compare timestamps
            if remote_updated and local_created:
                try:
                    # Simple string comparison for timestamps
                    if remote_updated > local_created:
                        differences.append("remote_newer")
                        update_available = True
                except:
                    pass
            
            # Compare sizes
            if remote_size and local_size:
                try:
                    local_size_bytes = self._parse_size(local_size)
                    if remote_size > local_size:
                        differences.append("remote_larger")
                    elif remote_size < local_size:
                        differences.append("local_larger")
                except:
                    pass
        else:
            differences.append("tag_not_found_remote")
        
        return {
            "local_image": local_image,
            "remote_info": remote_info,
            "comparison": {
                "status": "compared",
                "has_remote": True,
                "update_available": update_available,
                "differences": differences,
                "local_tag": local_tag,
                "remote_tag_info": remote_tag_info
            }
        }
    
    def _parse_size(self, size_str: str) -> int:
        """Parse Docker size string to bytes."""
        try:
            if size_str.endswith('MB'):
                return int(float(size_str[:-2]) * 1024 * 1024)
            elif size_str.endswith('GB'):
                return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
            elif size_str.endswith('KB'):
                return int(float(size_str[:-2]) * 1024)
            else:
                return int(size_str)
        except:
            return 0
    
    def _generate_summary(self, comparison_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of comparison results."""
        total = len(comparison_results)
        with_remote = sum(1 for r in comparison_results if r["comparison"]["has_remote"])
        updates_available = sum(1 for r in comparison_results if r["comparison"]["update_available"])
        no_remote = total - with_remote
        
        return {
            "total_images": total,
            "with_remote_counterpart": with_remote,
            "updates_available": updates_available,
            "no_remote_found": no_remote,
            "update_percentage": (updates_available / total * 100) if total > 0 else 0
        }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker images compare command parameters."""
        return {
            "type": "object",
            "properties": {
                "image_name": {
                    "type": "string",
                    "description": "Specific image name to compare",
                    "examples": ["nginx", "ubuntu", "python", "node"]
                },
                "include_all_local": {
                    "type": "boolean",
                    "description": "Compare all local images",
                    "default": False
                },
                "check_updates": {
                    "type": "boolean",
                    "description": "Check for available updates",
                    "default": True
                },
                "include_dangling": {
                    "type": "boolean",
                    "description": "Include dangling images in comparison",
                    "default": False
                }
            },
            "required": [],
            "additionalProperties": False
        } 