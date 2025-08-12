"""Git init command for initializing Git repositories."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitInitCommand(Command):
    """Initialize Git repositories.
    
    This command supports:
    - Initialize new repository
    - Bare repository
    - Shared repository
    - Template directory
    """
    
    name = "git_init"
    
    async def execute(
        self,
        repository_path: Optional[str] = None,
        bare: bool = False,
        shared: Optional[str] = None,
        template: Optional[str] = None,
        quiet: bool = False,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize a Git repository.
        
        Args:
            repository_path: Path to repository (optional, defaults to current directory)
            bare: Create a bare repository
            shared: Set repository sharing permissions (umask, group, all, world, everybody, 0xxx)
            template: Specify template directory
            quiet: Suppress output
            verbose: Show detailed output
        """
        try:
            # Determine repository path
            if not repository_path:
                repository_path = os.getcwd()
            
            # Check if directory already has a Git repository
            if os.path.exists(os.path.join(repository_path, ".git")):
                return ErrorResult(
                    message=f"'{repository_path}' is already a Git repository",
                    code="ALREADY_GIT_REPOSITORY",
                    details={"repository_path": repository_path}
                )
            
            # Build git init command
            cmd = ["git", "init"]
            
            if bare:
                cmd.append("--bare")
            
            if shared:
                cmd.extend(["--shared", shared])
            
            if template:
                cmd.extend(["--template", template])
            
            if quiet:
                cmd.append("--quiet")
            
            if verbose:
                cmd.append("--verbose")
            
            # Add repository path
            cmd.append(repository_path)
            
            # Execute git init
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()  # Run from current directory
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git init failed: {result.stderr}",
                    code="GIT_INIT_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get repository information
            repo_info = await self._get_repository_info(repository_path)
            
            return SuccessResult(data={
                "message": f"Successfully initialized Git repository at {repository_path}",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "repository_info": repo_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git init: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_repository_info(self, repo_path: str) -> Dict[str, Any]:
        """Get information about the initialized repository."""
        try:
            # Check if .git directory exists
            git_dir = os.path.join(repo_path, ".git")
            is_bare = not os.path.exists(git_dir)
            
            # Get Git version
            version_cmd = ["git", "--version"]
            version_result = subprocess.run(
                version_cmd,
                capture_output=True,
                text=True
            )
            git_version = version_result.stdout.strip() if version_result.returncode == 0 else "unknown"
            
            # Get repository status
            status_cmd = ["git", "status"]
            status_result = subprocess.run(
                status_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            status_output = status_result.stdout.strip() if status_result.returncode == 0 else ""
            
            # Get initial commit info
            log_cmd = ["git", "log", "--oneline", "-1"]
            log_result = subprocess.run(
                log_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            has_commits = bool(log_result.stdout.strip())
            
            return {
                "is_bare": is_bare,
                "git_version": git_version,
                "has_commits": has_commits,
                "status": status_output[:200] + "..." if len(status_output) > 200 else status_output,
                "git_directory": git_dir if not is_bare else repo_path
            }
            
        except Exception:
            return {
                "is_bare": False,
                "git_version": "unknown",
                "has_commits": False,
                "status": "unknown",
                "git_directory": "unknown"
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Initialize Git repositories",
            "parameters": {
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository (optional, defaults to current directory)"
                },
                "bare": {
                    "type": "boolean",
                    "description": "Create a bare repository",
                    "default": False
                },
                "shared": {
                    "type": "string",
                    "description": "Set repository sharing permissions (umask, group, all, world, everybody, 0xxx)"
                },
                "template": {
                    "type": "string",
                    "description": "Specify template directory"
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Suppress output",
                    "default": False
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Show detailed output",
                    "default": False
                }
            },
            "examples": [
                {
                    "description": "Initialize repository in current directory",
                    "params": {}
                },
                {
                    "description": "Initialize repository in specific path",
                    "params": {
                        "repository_path": "/path/to/repo"
                    }
                },
                {
                    "description": "Create bare repository",
                    "params": {
                        "repository_path": "/path/to/bare-repo",
                        "bare": True
                    }
                },
                {
                    "description": "Initialize shared repository",
                    "params": {
                        "repository_path": "/path/to/shared-repo",
                        "shared": "group"
                    }
                },
                {
                    "description": "Initialize with custom template",
                    "params": {
                        "repository_path": "/path/to/repo",
                        "template": "/path/to/template"
                    }
                }
            ]
        } 