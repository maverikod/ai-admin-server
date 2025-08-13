"""Git fetch command for fetching changes from remote repositories."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitFetchCommand(Command):
    """Fetch changes from remote Git repositories.
    
    This command supports:
    - Fetch from specific remote
    - Fetch specific branches
    - Fetch all remotes
    - Fetch tags
    - Prune remote-tracking branches
    - Deepen history
    """
    
    name = "git_fetch"
    
    async def execute(
        self,
        current_directory: str,
        remote: Optional[str] = None,
        branch: Optional[str] = None,
        all_remotes: bool = False,
        tags: bool = False,
        prune: bool = False,
        prune_tags: bool = False,
        depth: Optional[int] = None,
        quiet: bool = False,
        verbose: bool = False,
        progress: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Fetch changes from remote repository.
        
        Args:
            current_directory: Current working directory where to execute git commands
            remote: Remote repository name (optional, defaults to all remotes)
            branch: Branch to fetch (optional)
            all_remotes: Fetch from all remotes
            tags: Fetch tags
            prune: Prune remote-tracking branches
            prune_tags: Prune remote-tracking tags
            depth: Depth for shallow fetch
            quiet: Suppress output
            verbose: Show detailed output
            progress: Show progress
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
            
            # Build git fetch command
            cmd = ["git", "fetch"]
            
            if all_remotes:
                cmd.append("--all")
            
            if tags:
                cmd.append("--tags")
            
            if prune:
                cmd.append("--prune")
            
            if prune_tags:
                cmd.append("--prune-tags")
            
            if depth:
                cmd.extend(["--depth", str(depth)])
            
            if quiet:
                cmd.append("--quiet")
            
            if verbose:
                cmd.append("--verbose")
            
            if progress:
                cmd.append("--progress")
            
            # Add remote and branch
            if remote:
                if branch:
                    cmd.extend([remote, branch])
                else:
                    cmd.append(remote)
            elif not all_remotes:
                # Default to origin if no remote specified
                cmd.append("origin")
            
            # Execute git fetch
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git fetch failed: {result.stderr}",
                    code="GIT_FETCH_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get fetch results
            fetch_info = await self._get_fetch_info(repository_path)
            
            return SuccessResult(data={
                "message": f"Successfully fetched changes from remote",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "fetch_info": fetch_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git fetch: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_fetch_info(self, repo_path: str) -> Dict[str, Any]:
        """Get information about fetched changes."""
        try:
            # Get remote branches
            result = subprocess.run(
                ["git", "branch", "-r"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            remote_branches = []
            if result.returncode == 0:
                remote_branches = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            # Get tags
            result = subprocess.run(
                ["git", "tag", "-l"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            tags = []
            if result.returncode == 0:
                tags = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            return {
                "remote_branches": remote_branches,
                "tags": tags,
                "total_remote_branches": len(remote_branches),
                "total_tags": len(tags)
            }
            
        except Exception:
            return {
                "remote_branches": [],
                "tags": [],
                "total_remote_branches": 0,
                "total_tags": 0
            } 