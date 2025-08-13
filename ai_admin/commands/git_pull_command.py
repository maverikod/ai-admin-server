"""Git pull command for fetching and merging changes from remote repositories."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError
from ai_admin.commands.git_utils import ensure_git_auth, is_github_repo


class GitPullCommand(Command):
    """Pull changes from remote Git repositories.
    
    This command supports:
    - Pull from specific remote and branch
    - Rebase instead of merge
    - Fast-forward only
    - Squash commits
    - Pull with tags
    """
    
    name = "git_pull"
    
    async def execute(
        self,
        current_directory: str,
        remote: str = "origin",
        branch: Optional[str] = None,
        rebase: bool = False,
        fast_forward_only: bool = False,
        squash: bool = False,
        tags: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        progress: bool = False,
        no_edit: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Pull changes from remote repository.
        
        Args:
            current_directory: Current working directory where to execute git commands
            remote: Remote repository name (default: origin)
            branch: Branch to pull (optional, uses current branch if not specified)
            rebase: Use rebase instead of merge
            fast_forward_only: Only allow fast-forward merges
            squash: Squash commits into one
            tags: Pull tags
            verbose: Show detailed output
            quiet: Suppress output
            progress: Show progress
            no_edit: Don't open editor for merge commit message
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
            
            # Build git pull command
            cmd = ["git", "pull"]
            
            if rebase:
                cmd.append("--rebase")
            
            if fast_forward_only:
                cmd.append("--ff-only")
            
            if squash:
                cmd.append("--squash")
            
            if tags:
                cmd.append("--tags")
            
            if verbose:
                cmd.append("--verbose")
            
            if quiet:
                cmd.append("--quiet")
            
            if progress:
                cmd.append("--progress")
            
            if no_edit:
                cmd.append("--no-edit")
            
            # Add remote and branch
            if branch:
                cmd.extend([remote, branch])
            else:
                cmd.append(remote)
            
            # Execute git pull
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git pull failed: {result.stderr}",
                    code="GIT_PULL_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get pull information
            pull_info = await self._get_pull_info(repository_path, remote)
            
            return SuccessResult(data={
                "message": f"Successfully pulled from {remote}",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "pull_info": pull_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git pull: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_pull_info(self, repo_path: str, remote: str) -> Dict[str, Any]:
        """Get information about the pull operation."""
        try:
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
            
            # Get ahead/behind info
            ahead_behind_cmd = ["git", "rev-list", "--left-right", "--count", f"{remote}/{current_branch}...HEAD"]
            ahead_behind_result = subprocess.run(
                ahead_behind_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            ahead_behind = {"ahead": 0, "behind": 0}
            if ahead_behind_result.returncode == 0 and ahead_behind_result.stdout.strip():
                parts = ahead_behind_result.stdout.strip().split()
                if len(parts) >= 2:
                    ahead_behind = {
                        "ahead": int(parts[1]),
                        "behind": int(parts[0])
                    }
            
            return {
                "current_branch": current_branch,
                "remote": remote,
                "remote_url": remote_url,
                "last_commit": commit_info,
                "working_directory_status": len(status_lines),
                "status_lines": status_lines[:10],  # Limit to first 10 lines
                "ahead_behind": ahead_behind
            }
            
        except Exception:
            return {
                "current_branch": "unknown",
                "remote": remote,
                "remote_url": "unknown",
                "last_commit": {},
                "working_directory_status": 0,
                "status_lines": [],
                "ahead_behind": {"ahead": 0, "behind": 0}
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Pull changes from remote Git repositories",
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
                    "description": "Branch to pull (optional, uses current branch if not specified)"
                },
                "rebase": {
                    "type": "boolean",
                    "description": "Use rebase instead of merge",
                    "default": False
                },
                "fast_forward_only": {
                    "type": "boolean",
                    "description": "Only allow fast-forward merges",
                    "default": False
                },
                "squash": {
                    "type": "boolean",
                    "description": "Squash commits into one",
                    "default": False
                },
                "tags": {
                    "type": "boolean",
                    "description": "Pull tags",
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
                "progress": {
                    "type": "boolean",
                    "description": "Show progress",
                    "default": False
                },
                "no_edit": {
                    "type": "boolean",
                    "description": "Don't open editor for merge commit message",
                    "default": False
                },
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository (optional, defaults to current_directory)"
                }
            },
            "examples": [
                {
                    "description": "Pull from origin",
                    "params": {
                        "current_directory": ".",
                        "remote": "origin"
                    }
                },
                {
                    "description": "Pull specific branch",
                    "params": {
                        "current_directory": ".",
                        "remote": "origin",
                        "branch": "main"
                    }
                },
                {
                    "description": "Pull with rebase",
                    "params": {
                        "current_directory": ".",
                        "remote": "origin",
                        "rebase": True
                    }
                },
                {
                    "description": "Fast-forward only pull",
                    "params": {
                        "current_directory": ".",
                        "remote": "origin",
                        "fast_forward_only": True
                    }
                },
                {
                    "description": "Pull with tags",
                    "params": {
                        "current_directory": ".",
                        "remote": "origin",
                        "tags": True
                    }
                }
            ]
        } 