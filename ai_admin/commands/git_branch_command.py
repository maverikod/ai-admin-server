"""Git branch command for managing branches."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitBranchCommand(Command):
    """Manage Git branches.
    
    This command supports:
    - List branches
    - Create new branches
    - Delete branches
    - Rename branches
    - Set upstream
    """
    
    name = "git_branch"
    
    async def execute(
        self,
        action: str = "list",
        branch_name: Optional[str] = None,
        start_point: Optional[str] = None,
        force: bool = False,
        delete: bool = False,
        rename: bool = False,
        new_name: Optional[str] = None,
        set_upstream: Optional[str] = None,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Manage Git branches.
        
        Args:
            action: Action to perform (list, create, delete, rename, set-upstream)
            branch_name: Name of the branch
            start_point: Starting point for new branch (commit, branch, tag)
            force: Force the operation
            delete: Delete the branch
            rename: Rename the branch
            new_name: New name for the branch (when renaming)
            set_upstream: Set upstream branch
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
            
            # Build git branch command based on action
            if action == "list":
                cmd = ["git", "branch"]
                if force:  # -a flag for all branches
                    cmd.append("-a")
                
            elif action == "create":
                if not branch_name:
                    return ErrorResult(
                        message="Branch name is required for create action",
                        code="MISSING_BRANCH_NAME",
                        details={}
                    )
                
                cmd = ["git", "branch"]
                if force:
                    cmd.append("-f")
                
                cmd.append(branch_name)
                if start_point:
                    cmd.append(start_point)
                
            elif action == "delete":
                if not branch_name:
                    return ErrorResult(
                        message="Branch name is required for delete action",
                        code="MISSING_BRANCH_NAME",
                        details={}
                    )
                
                cmd = ["git", "branch"]
                if force:
                    cmd.append("-D")  # Force delete
                else:
                    cmd.append("-d")  # Safe delete
                cmd.append(branch_name)
                
            elif action == "rename":
                if not branch_name or not new_name:
                    return ErrorResult(
                        message="Both branch_name and new_name are required for rename action",
                        code="MISSING_BRANCH_NAMES",
                        details={}
                    )
                
                cmd = ["git", "branch", "-m", branch_name, new_name]
                
            elif action == "set-upstream":
                if not branch_name or not set_upstream:
                    return ErrorResult(
                        message="Both branch_name and set_upstream are required for set-upstream action",
                        code="MISSING_UPSTREAM_INFO",
                        details={}
                    )
                
                cmd = ["git", "branch", "--set-upstream-to", set_upstream, branch_name]
                
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="UNKNOWN_ACTION",
                    details={"valid_actions": ["list", "create", "delete", "rename", "set-upstream"]}
                )
            
            # Execute git branch command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git branch operation failed: {result.stderr}",
                    code="GIT_BRANCH_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get branch information
            branch_info = await self._get_branch_info(repository_path)
            
            return SuccessResult(data={
                "message": f"Successfully executed git branch {action}",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "branch_info": branch_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git branch operation: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_branch_info(self, repo_path: str) -> Dict[str, Any]:
        """Get information about branches."""
        try:
            # Get current branch
            current_cmd = ["git", "branch", "--show-current"]
            current_result = subprocess.run(
                current_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            current_branch = current_result.stdout.strip() if current_result.returncode == 0 else "unknown"
            
            # Get all local branches
            local_cmd = ["git", "branch", "--format=%(refname:short)|%(upstream:short)|%(upstream:track)"]
            local_result = subprocess.run(
                local_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            local_branches = []
            if local_result.returncode == 0:
                for line in local_result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.strip().split('|')
                        branch_info = {
                            "name": parts[0],
                            "current": parts[0] == current_branch,
                            "upstream": parts[1] if len(parts) > 1 and parts[1] else None,
                            "track": parts[2] if len(parts) > 2 and parts[2] else None
                        }
                        local_branches.append(branch_info)
            
            # Get all remote branches
            remote_cmd = ["git", "branch", "-r", "--format=%(refname:short)"]
            remote_result = subprocess.run(
                remote_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            remote_branches = []
            if remote_result.returncode == 0:
                remote_branches = [line.strip() for line in remote_result.stdout.strip().split('\n') if line.strip()]
            
            return {
                "current_branch": current_branch,
                "local_branches": local_branches,
                "remote_branches": remote_branches,
                "total_local": len(local_branches),
                "total_remote": len(remote_branches)
            }
            
        except Exception:
            return {
                "current_branch": "unknown",
                "local_branches": [],
                "remote_branches": [],
                "total_local": 0,
                "total_remote": 0
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Manage Git branches",
            "parameters": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "default": "list",
                    "enum": ["list", "create", "delete", "rename", "set-upstream"]
                },
                "branch_name": {
                    "type": "string",
                    "description": "Name of the branch"
                },
                "start_point": {
                    "type": "string",
                    "description": "Starting point for new branch (commit, branch, tag)"
                },
                "force": {
                    "type": "boolean",
                    "description": "Force the operation",
                    "default": False
                },
                "delete": {
                    "type": "boolean",
                    "description": "Delete the branch",
                    "default": False
                },
                "rename": {
                    "type": "boolean",
                    "description": "Rename the branch",
                    "default": False
                },
                "new_name": {
                    "type": "string",
                    "description": "New name for the branch (when renaming)"
                },
                "set_upstream": {
                    "type": "string",
                    "description": "Set upstream branch"
                },
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository (optional, defaults to current directory)"
                }
            },
            "examples": [
                {
                    "description": "List all branches",
                    "params": {
                        "action": "list",
                        "force": True
                    }
                },
                {
                    "description": "Create new branch",
                    "params": {
                        "action": "create",
                        "branch_name": "feature/new-feature",
                        "start_point": "main"
                    }
                },
                {
                    "description": "Delete branch",
                    "params": {
                        "action": "delete",
                        "branch_name": "old-branch",
                        "force": True
                    }
                },
                {
                    "description": "Rename branch",
                    "params": {
                        "action": "rename",
                        "branch_name": "old-name",
                        "new_name": "new-name"
                    }
                },
                {
                    "description": "Set upstream",
                    "params": {
                        "action": "set-upstream",
                        "branch_name": "feature",
                        "set_upstream": "origin/feature"
                    }
                }
            ]
        } 