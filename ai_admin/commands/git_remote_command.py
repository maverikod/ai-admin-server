"""Git remote command for managing remote repositories."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitRemoteCommand(Command):
    """Manage Git remote repositories.
    
    This command supports:
    - List remotes
    - Add remotes
    - Remove remotes
    - Rename remotes
    - Set URL
    - Show remote details
    """
    
    name = "git_remote"
    
    async def execute(
        self,
        action: str = "list",
        remote_name: Optional[str] = None,
        remote_url: Optional[str] = None,
        new_name: Optional[str] = None,
        fetch: bool = False,
        push: bool = False,
        all: bool = False,
        verbose: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Manage Git remote repositories.
        
        Args:
            action: Action to perform (list, add, remove, rename, set-url, show)
            remote_name: Name of the remote
            remote_url: URL of the remote repository
            new_name: New name for the remote (when renaming)
            fetch: Show fetch URL
            push: Show push URL
            all: Show all URLs
            verbose: Show detailed output
            repository_path: Path to repository (optional, defaults to current directory)
        """
        try:
            # Determine repository path
            if not repository_path:
                repository_path = os.getcwd()
            
            # Check if directory is a Git repository
            if not os.path.exists(os.path.join(repository_path, ".git")):
                return ErrorResult(
                    message=f"'{repository_path}' is not a Git repository",
                    code="NOT_GIT_REPOSITORY",
                    details={"repository_path": repository_path}
                )
            
            # Build git remote command based on action
            if action == "list":
                cmd = ["git", "remote"]
                if verbose:
                    cmd.append("-v")
                
            elif action == "add":
                if not remote_name or not remote_url:
                    return ErrorResult(
                        message="Both remote_name and remote_url are required for add action",
                        code="MISSING_REMOTE_INFO",
                        details={}
                    )
                
                cmd = ["git", "remote", "add", remote_name, remote_url]
                
            elif action == "remove":
                if not remote_name:
                    return ErrorResult(
                        message="remote_name is required for remove action",
                        code="MISSING_REMOTE_NAME",
                        details={}
                    )
                
                cmd = ["git", "remote", "remove", remote_name]
                
            elif action == "rename":
                if not remote_name or not new_name:
                    return ErrorResult(
                        message="Both remote_name and new_name are required for rename action",
                        code="MISSING_REMOTE_NAMES",
                        details={}
                    )
                
                cmd = ["git", "remote", "rename", remote_name, new_name]
                
            elif action == "set-url":
                if not remote_name or not remote_url:
                    return ErrorResult(
                        message="Both remote_name and remote_url are required for set-url action",
                        code="MISSING_REMOTE_INFO",
                        details={}
                    )
                
                cmd = ["git", "remote", "set-url", remote_name, remote_url]
                
            elif action == "show":
                if not remote_name:
                    return ErrorResult(
                        message="remote_name is required for show action",
                        code="MISSING_REMOTE_NAME",
                        details={}
                    )
                
                cmd = ["git", "remote", "show"]
                if verbose:
                    cmd.append("-n")
                cmd.append(remote_name)
                
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="UNKNOWN_ACTION",
                    details={"valid_actions": ["list", "add", "remove", "rename", "set-url", "show"]}
                )
            
            # Execute git remote command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git remote operation failed: {result.stderr}",
                    code="GIT_REMOTE_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get remote information
            remote_info = await self._get_remote_info(repository_path, remote_name)
            
            return SuccessResult(data={
                "message": f"Successfully executed git remote {action}",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "remote_info": remote_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git remote operation: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_remote_info(self, repo_path: str, remote_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about remotes."""
        try:
            # Get all remotes
            list_cmd = ["git", "remote", "-v"]
            list_result = subprocess.run(
                list_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            remotes = []
            if list_result.returncode == 0:
                for line in list_result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            remotes.append({
                                "name": parts[0],
                                "url": parts[1],
                                "type": parts[2].strip('()')
                            })
            
            # Get specific remote details if requested
            remote_details = {}
            if remote_name:
                show_cmd = ["git", "remote", "show", remote_name]
                show_result = subprocess.run(
                    show_cmd,
                    capture_output=True,
                    text=True,
                    cwd=repo_path
                )
                if show_result.returncode == 0:
                    remote_details = {
                        "name": remote_name,
                        "details": show_result.stdout.strip()
                    }
            
            return {
                "remotes": remotes,
                "total_remotes": len(remotes),
                "remote_details": remote_details
            }
            
        except Exception:
            return {
                "remotes": [],
                "total_remotes": 0,
                "remote_details": {}
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Manage Git remote repositories",
            "parameters": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "default": "list",
                    "enum": ["list", "add", "remove", "rename", "set-url", "show"]
                },
                "remote_name": {
                    "type": "string",
                    "description": "Name of the remote"
                },
                "remote_url": {
                    "type": "string",
                    "description": "URL of the remote repository"
                },
                "new_name": {
                    "type": "string",
                    "description": "New name for the remote (when renaming)"
                },
                "fetch": {
                    "type": "boolean",
                    "description": "Show fetch URL",
                    "default": False
                },
                "push": {
                    "type": "boolean",
                    "description": "Show push URL",
                    "default": False
                },
                "all": {
                    "type": "boolean",
                    "description": "Show all URLs",
                    "default": False
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Show detailed output",
                    "default": False
                },
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository (optional, defaults to current directory)"
                }
            },
            "examples": [
                {
                    "description": "List all remotes",
                    "params": {
                        "action": "list",
                        "verbose": True
                    }
                },
                {
                    "description": "Add new remote",
                    "params": {
                        "action": "add",
                        "remote_name": "origin",
                        "remote_url": "https://github.com/user/repo.git"
                    }
                },
                {
                    "description": "Remove remote",
                    "params": {
                        "action": "remove",
                        "remote_name": "old-remote"
                    }
                },
                {
                    "description": "Rename remote",
                    "params": {
                        "action": "rename",
                        "remote_name": "old-name",
                        "new_name": "new-name"
                    }
                },
                {
                    "description": "Set remote URL",
                    "params": {
                        "action": "set-url",
                        "remote_name": "origin",
                        "remote_url": "https://github.com/user/new-repo.git"
                    }
                },
                {
                    "description": "Show remote details",
                    "params": {
                        "action": "show",
                        "remote_name": "origin"
                    }
                }
            ]
        } 