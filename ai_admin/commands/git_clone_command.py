"""Git clone command for cloning repositories."""

import os
import subprocess
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitCloneCommand(Command):
    """Clone Git repositories from various sources.
    
    This command supports cloning from:
    - GitHub (HTTPS/SSH)
    - GitLab
    - Bitbucket
    - Local repositories
    - Custom Git servers
    """
    
    name = "git_clone"
    
    async def execute(
        self,
        current_directory: str,
        repository_url: str,
        target_directory: Optional[str] = None,
        branch: Optional[str] = None,
        depth: Optional[int] = None,
        recursive: bool = False,
        quiet: bool = False,
        **kwargs
    ):
        """
        Clone a Git repository.
        
        Args:
            current_directory: Current working directory where to execute git commands
            repository_url: URL of the repository to clone
            target_directory: Directory to clone into (optional)
            branch: Specific branch to clone (optional)
            depth: Depth for shallow clone (optional)
            recursive: Clone submodules recursively
            quiet: Suppress output
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
            
            # Validate repository URL
            if not repository_url:
                raise ValidationError("Repository URL is required")
            
            # Determine target directory
            if not target_directory:
                # Extract repository name from URL
                repo_name = repository_url.split('/')[-1]
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                target_directory = repo_name
            
            # Ensure target directory doesn't exist
            target_path = os.path.join(current_directory, target_directory)
            if os.path.exists(target_path):
                return ErrorResult(
                    message=f"Target directory '{target_path}' already exists",
                    code="DIRECTORY_EXISTS",
                    details={"target_directory": target_path}
                )
            
            # Build git clone command
            cmd = ["git", "clone"]
            
            if branch:
                cmd.extend(["-b", branch])
            
            if depth:
                cmd.extend(["--depth", str(depth)])
            
            if recursive:
                cmd.append("--recursive")
            
            if quiet:
                cmd.append("--quiet")
            
            cmd.extend([repository_url, target_directory])
            
            # Execute git clone
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=current_directory
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git clone failed: {result.stderr}",
                    code="GIT_CLONE_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get repository info
            repo_info = await self._get_repository_info(target_path)
            
            return SuccessResult(data={
                "message": f"Successfully cloned repository to '{target_path}'",
                "repository_url": repository_url,
                "target_directory": os.path.abspath(target_path),
                "branch": branch or "default",
                "repository_info": repo_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git clone: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_repository_info(self, repo_path: str) -> Dict[str, Any]:
        """Get information about the cloned repository."""
        try:
            # Get current branch
            branch_cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
            branch_result = subprocess.run(
                branch_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            # Get commit hash
            commit_cmd = ["git", "rev-parse", "HEAD"]
            commit_result = subprocess.run(
                commit_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            commit_hash = commit_result.stdout.strip() if commit_result.returncode == 0 else "unknown"
            
            # Get remote origin
            remote_cmd = ["git", "remote", "get-url", "origin"]
            remote_result = subprocess.run(
                remote_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            remote_url = remote_result.stdout.strip() if remote_result.returncode == 0 else "unknown"
            
            return {
                "current_branch": current_branch,
                "commit_hash": commit_hash,
                "remote_url": remote_url,
                "path": os.path.abspath(repo_path)
            }
            
        except Exception:
            return {"error": "Could not get repository info"}
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Clone Git repositories from various sources",
            "parameters": {
                "current_directory": {
                    "type": "string",
                    "description": "Current working directory where to execute git commands",
                    "required": True
                },
                "repository_url": {
                    "type": "string",
                    "description": "URL of the repository to clone",
                    "required": True
                },
                "target_directory": {
                    "type": "string",
                    "description": "Directory to clone into (optional)"
                },
                "branch": {
                    "type": "string",
                    "description": "Specific branch to clone (optional)"
                },
                "depth": {
                    "type": "integer",
                    "description": "Depth for shallow clone (optional)"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Clone submodules recursively",
                    "default": False
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Suppress output",
                    "default": False
                }
            },
            "examples": [
                {
                    "description": "Clone a GitHub repository",
                    "params": {
                        "current_directory": ".",
                        "repository_url": "https://github.com/user/repo.git",
                        "target_directory": "my-repo"
                    }
                },
                {
                    "description": "Clone specific branch",
                    "params": {
                        "current_directory": ".",
                        "repository_url": "https://github.com/user/repo.git",
                        "branch": "develop"
                    }
                },
                {
                    "description": "Shallow clone",
                    "params": {
                        "current_directory": ".",
                        "repository_url": "https://github.com/user/repo.git",
                        "depth": 1
                    }
                }
            ]
        } 