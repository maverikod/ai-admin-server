"""Git tag command for managing tags."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitTagCommand(Command):
    """Manage Git tags.
    
    This command supports:
    - List tags
    - Create lightweight tags
    - Create annotated tags
    - Delete tags
    - Push tags to remote
    - Show tag information
    """
    
    name = "git_tag"
    
    async def execute(
        self,
        current_directory: str,
        action: str = "list",
        tag_name: Optional[str] = None,
        commit: Optional[str] = None,
        message: Optional[str] = None,
        force: bool = False,
        delete: bool = False,
        push: bool = False,
        remote: str = "origin",
        all_tags: bool = False,
        sort: Optional[str] = None,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Manage Git tags.
        
        Args:
            current_directory: Current working directory where to execute git commands
            action: Action to perform (list, create, delete, push)
            tag_name: Name of the tag
            commit: Commit to tag (optional, defaults to HEAD)
            message: Tag message (for annotated tags)
            force: Force the operation
            delete: Delete the tag
            push: Push tags to remote
            remote: Remote repository name (default: origin)
            all_tags: List all tags (including remote)
            sort: Sort tags (version, create, refname)
            repository_path: Path to repository (optional, defaults to current_directory)
        """
        try:
            # Validate current_directory
            if not current_directory:
                return ErrorResult(
                    message="current_directory is required",
                    code="MISSING_CURRENT_DIRECTORY",
                    details={}
                )
            
            if not os.path.exists(current_directory):
                return ErrorResult(
                    message=f"Directory '{current_directory}' does not exist",
                    code="DIRECTORY_NOT_FOUND",
                    details={"current_directory": current_directory}
                )
            
            # Determine repository path
            if not repository_path:
                repository_path = current_directory
            
            # Check if directory is a Git repository
            if not os.path.exists(os.path.join(repository_path, ".git")):
                return ErrorResult(
                    message=f"'{repository_path}' is not a Git repository",
                    code="NOT_GIT_REPOSITORY",
                    details={"repository_path": repository_path}
                )
            
            # Build git tag command based on action
            if action == "list":
                cmd = ["git", "tag"]
                
                if all_tags:
                    cmd.append("-a")
                
                if sort:
                    cmd.extend(["--sort", sort])
                
            elif action == "create":
                if not tag_name:
                    return ErrorResult(
                        message="Tag name is required for create action",
                        code="MISSING_TAG_NAME",
                        details={}
                    )
                
                cmd = ["git", "tag"]
                
                if force:
                    cmd.append("-f")
                
                if message:
                    cmd.extend(["-a", "-m", message])
                else:
                    # Use lightweight tag if no message provided
                    pass
                
                cmd.append(tag_name)
                
                if commit:
                    cmd.append(commit)
                
            elif action == "delete":
                if not tag_name:
                    return ErrorResult(
                        message="Tag name is required for delete action",
                        code="MISSING_TAG_NAME",
                        details={}
                    )
                
                cmd = ["git", "tag", "-d", tag_name]
                
            elif action == "push":
                cmd = ["git", "push"]
                
                if force:
                    cmd.append("--force")
                
                cmd.extend([remote, "refs/tags/*"])
                
            else:
                return ErrorResult(
                    message=f"Invalid action: {action}",
                    code="INVALID_ACTION",
                    details={"valid_actions": ["list", "create", "delete", "push"]}
                )
            
            # Execute git tag command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git tag {action} failed: {result.stderr}",
                    code="GIT_TAG_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get tag information
            tag_info = await self._get_tag_info(repository_path, action)
            
            return SuccessResult(data={
                "message": f"Successfully performed {action} action on tags",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "action": action,
                "tag_info": tag_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git tag: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_tag_info(self, repo_path: str, action: str) -> Dict[str, Any]:
        """Get information about tags."""
        try:
            if action == "list":
                # Get all tags
                result = subprocess.run(
                    ["git", "tag", "-l"],
                    capture_output=True,
                    text=True,
                    cwd=repo_path
                )
                
                tags = []
                if result.returncode == 0:
                    tags = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                
                # Get detailed tag information
                tag_details = []
                for tag in tags[:10]:  # Limit to first 10 tags for performance
                    detail_result = subprocess.run(
                        ["git", "show", "--no-patch", "--format=fuller", tag],
                        capture_output=True,
                        text=True,
                        cwd=repo_path
                    )
                    
                    if detail_result.returncode == 0:
                        tag_details.append({
                            "name": tag,
                            "info": detail_result.stdout.strip()
                        })
                
                return {
                    "tags": tags,
                    "total_tags": len(tags),
                    "tag_details": tag_details
                }
            
            elif action == "create":
                # Get the created tag info
                return {
                    "created_tag": "tag_info_available",
                    "message": "Tag created successfully"
                }
            
            elif action == "delete":
                return {
                    "deleted_tag": "tag_info_available",
                    "message": "Tag deleted successfully"
                }
            
            elif action == "push":
                return {
                    "pushed_tags": "tag_info_available",
                    "message": "Tags pushed successfully"
                }
            
            return {"message": "Action completed"}
            
        except Exception:
            return {"message": "Could not retrieve tag information"} 