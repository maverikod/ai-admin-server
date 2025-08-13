"""Git push command for pushing commits to remote repositories."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError
from ai_admin.commands.git_utils import ensure_git_auth, is_github_repo


class GitPushCommand(Command):
    """Push Git commits to remote repositories.
    
    This command supports:
    - Push to specific remote and branch
    - Force push
    - Push all branches
    - Push tags
    - Set upstream
    """
    
    name = "git_push"
    
    async def execute(
        self,
        current_directory: str,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        force_with_lease: bool = False,
        all_branches: bool = False,
        tags: bool = False,
        set_upstream: bool = False,
        dry_run: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Push Git commits to remote repository.
        
        Args:
            current_directory: Current working directory where to execute git commands
            remote: Remote repository name (default: origin)
            branch: Branch to push (optional, uses current branch if not specified)
            force: Force push (overwrites remote history)
            force_with_lease: Force push with lease (safer than force)
            all_branches: Push all branches
            tags: Push tags
            set_upstream: Set upstream branch
            dry_run: Show what would be pushed without actually pushing
            verbose: Show detailed output
            quiet: Suppress output
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
            
            # Setup Git authentication if it's a GitHub repository
            if is_github_repo(repository_path):
                ensure_git_auth(repository_path)
            
            # Build git push command
            cmd = ["git", "push"]
            
            if force:
                cmd.append("--force")
            elif force_with_lease:
                cmd.append("--force-with-lease")
            
            if all_branches:
                cmd.append("--all")
            
            if tags:
                cmd.append("--tags")
            
            if set_upstream:
                cmd.append("--set-upstream")
            
            if dry_run:
                cmd.append("--dry-run")
            
            if verbose:
                cmd.append("--verbose")
            
            if quiet:
                cmd.append("--quiet")
            
            # Add remote and branch
            if branch:
                cmd.extend([remote, branch])
            else:
                cmd.append(remote)
            
            # Execute git push
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git push failed: {result.stderr}",
                    code="GIT_PUSH_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get push information
            push_info = await self._get_push_info(repository_path, remote)
            
            return SuccessResult(data={
                "message": f"Successfully pushed to {remote}",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "push_info": push_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git push: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_push_info(self, repo_path: str, remote: str) -> Dict[str, Any]:
        """Get information about the push operation."""
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
            

        # Get current branch
            branch_cmd = ["git", "branch", "--show-current"]
            branch_result = subprocess.run(
                branch_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            # Get remote URL
            url_cmd = ["git", "remote", "get-url", remote]
            url_result = subprocess.run(
                url_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            remote_url = url_result.stdout.strip() if url_result.returncode == 0 else "unknown"
            
            # Get last commit info
            commit_cmd = ["git", "log", "-1", "--pretty=format:%H|%s|%an|%cd"]
            commit_result = subprocess.run(
                commit_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            commit_info = {}
            if commit_result.returncode == 0 and commit_result.stdout.strip():
                parts = commit_result.stdout.strip().split('|')
                if len(parts) >= 4:
                    commit_info = {
                        "hash": parts[0],
                        "message": parts[1],
                        "author": parts[2],
                        "date": parts[3]
                    }
            
            # Get status
            status_cmd = ["git", "status", "--porcelain"]
            status_result = subprocess.run(
                status_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            status_lines = []
            if status_result.returncode == 0:
                status_lines = [line.strip() for line in status_result.stdout.strip().split('\n') if line.strip()]
            
            return {
                "current_branch": current_branch,
                "remote": remote,
                "remote_url": remote_url,
                "last_commit": commit_info,
                "working_directory_status": len(status_lines),
                "status_lines": status_lines[:10]  # Limit to first 10 lines
            }
            
        except Exception:
            return {
                "current_branch": "unknown",
                "remote": remote,
                "remote_url": "unknown",
                "last_commit": {},
                "working_directory_status": 0,
                "status_lines": []
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Push Git commits to remote repositories",
            "parameters": {
                "current_directory": {
                    "type": "string",
                    "description": "Current working directory where to execute git commands",
                    "required": True
                },
                "remote": {
                    "type": "string",
                    "description": "Remote repository name",
                    "default": "origin"
                },
                "branch": {
                    "type": "string",
                    "description": "Branch to push (optional, uses current branch if not specified)"
                },
                "force": {
                    "type": "boolean",
                    "description": "Force push (overwrites remote history)",
                    "default": False
                },
                "force_with_lease": {
                    "type": "boolean",
                    "description": "Force push with lease (safer than force)",
                    "default": False
                },
                "all_branches": {
                    "type": "boolean",
                    "description": "Push all branches",
                    "default": False
                },
                "tags": {
                    "type": "boolean",
                    "description": "Push tags",
                    "default": False
                },
                "set_upstream": {
                    "type": "boolean",
                    "description": "Set upstream branch",
                    "default": False
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Show what would be pushed without actually pushing",
                    "default": False
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Show detailed output",
                    "default": False
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Suppress output",
                    "default": False
                },
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository (optional, defaults to current_directory)"
                }
            },
            "examples": [
                {
                    "description": "Push current branch to origin",
                    "params": {
                        "current_directory": ".",
                        "remote": "origin"
                    }
                },
                {
                    "description": "Push specific branch",
                    "params": {
                        "current_directory": ".",
                        "remote": "origin",
                        "branch": "main"
                    }
                },
                {
                    "description": "Force push",
                    "params": {
                        "current_directory": ".",
                        "remote": "origin",
                        "force": True
                    }
                },
                {
                    "description": "Push all branches and tags",
                    "params": {
                        "current_directory": ".",
                        "remote": "origin",
                        "all_branches": True,
                        "tags": True
                    }
                },
                {
                    "description": "Set upstream and push",
                    "params": {
                        "current_directory": ".",
                        "remote": "origin",
                        "set_upstream": True
                    }
                }
            ]
        } 