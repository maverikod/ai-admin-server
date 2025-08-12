"""Git checkout command for switching branches and creating new branches."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitCheckoutCommand(Command):
    """Checkout Git branches and files.
    
    This command supports:
    - Switch to existing branch
    - Create and switch to new branch
    - Checkout specific commit
    - Checkout specific file
    - Detached HEAD mode
    """
    
    name = "git_checkout"
    
    async def execute(
        self,
        current_directory: str,
        target: str,
        create_branch: bool = False,
        force: bool = False,
        files: Optional[List[str]] = None,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Checkout Git branch, commit, or files.
        
        Args:
            current_directory: Current working directory where to execute git commands
            target: Branch name, commit hash, or file path to checkout
            create_branch: Create new branch if it doesn't exist
            force: Force checkout (discard local changes)
            files: Specific files to checkout (optional)
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
            
            # Build git checkout command
            cmd = ["git", "checkout"]
            
            if create_branch:
                cmd.append("-b")
            
            if force:
                cmd.append("-f")
            
            # Add target
            cmd.append(target)
            
            # Add specific files if provided
            if files:
                cmd.extend(files)
            
            # Execute git checkout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git checkout failed: {result.stderr}",
                    code="GIT_CHECKOUT_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get checkout information
            checkout_info = await self._get_checkout_info(repository_path, target)
            
            return SuccessResult(data={
                "message": f"Successfully checked out {target}",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "checkout_info": checkout_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git checkout: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_checkout_info(self, repo_path: str, target: str) -> Dict[str, Any]:
        """Get information about the checkout operation."""
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
            
            # Check if in detached HEAD state
            head_cmd = ["git", "rev-parse", "HEAD"]
            head_result = subprocess.run(
                head_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            head_hash = head_result.stdout.strip() if head_result.returncode == 0 else "unknown"
            
            # Get HEAD status
            head_status_cmd = ["git", "status", "--porcelain"]
            head_status_result = subprocess.run(
                head_status_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            head_status = []
            if head_status_result.returncode == 0:
                head_status = [line.strip() for line in head_status_result.stdout.strip().split('\n') if line.strip()]
            
            # Get commit info if in detached HEAD
            commit_info = {}
            if current_branch == "" or current_branch == "HEAD":
                # In detached HEAD state
                log_cmd = ["git", "log", "-1", "--pretty=format:%H|%s|%an|%cd"]
                log_result = subprocess.run(
                    log_cmd,
                    capture_output=True,
                    text=True,
                    cwd=repo_path
                )
                if log_result.returncode == 0 and log_result.stdout.strip():
                    parts = log_result.stdout.strip().split('|')
                    if len(parts) >= 4:
                        commit_info = {
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3]
                        }
            
            # Check if target is a branch
            branch_exists_cmd = ["git", "branch", "--list", target]
            branch_exists_result = subprocess.run(
                branch_exists_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            is_branch = bool(branch_exists_result.stdout.strip())
            
            # Check if target is a remote branch
            remote_branch_cmd = ["git", "branch", "-r", "--list", f"origin/{target}"]
            remote_branch_result = subprocess.run(
                remote_branch_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            is_remote_branch = bool(remote_branch_result.stdout.strip())
            
            return {
                "target": target,
                "current_branch": current_branch,
                "head_hash": head_hash,
                "is_detached_head": current_branch == "" or current_branch == "HEAD",
                "is_branch": is_branch,
                "is_remote_branch": is_remote_branch,
                "commit_info": commit_info,
                "working_directory_status": len(head_status),
                "status_lines": head_status[:10]  # Limit to first 10 lines
            }
            
        except Exception:
            return {
                "target": target,
                "current_branch": "unknown",
                "head_hash": "unknown",
                "is_detached_head": False,
                "is_branch": False,
                "is_remote_branch": False,
                "commit_info": {},
                "working_directory_status": 0,
                "status_lines": []
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Checkout Git branches and files",
            "parameters": {
                "current_directory": {
                    "type": "string",
                    "description": "Current working directory where to execute git commands",
                    "required": True
                },
                "target": {
                    "type": "string",
                    "description": "Branch name, commit hash, or file path to checkout",
                    "required": True
                },
                "create_branch": {
                    "type": "boolean",
                    "description": "Create new branch if it doesn't exist",
                    "default": False
                },
                "force": {
                    "type": "boolean",
                    "description": "Force checkout (discard local changes)",
                    "default": False
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific files to checkout (optional)"
                },
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository (optional, defaults to current_directory)"
                }
            },
            "examples": [
                {
                    "description": "Switch to existing branch",
                    "params": {
                        "current_directory": ".",
                        "target": "main"
                    }
                },
                {
                    "description": "Create and switch to new branch",
                    "params": {
                        "current_directory": ".",
                        "target": "feature/new-feature",
                        "create_branch": True
                    }
                },
                {
                    "description": "Checkout specific commit",
                    "params": {
                        "current_directory": ".",
                        "target": "abc1234"
                    }
                },
                {
                    "description": "Force checkout (discard changes)",
                    "params": {
                        "current_directory": ".",
                        "target": "main",
                        "force": True
                    }
                },
                {
                    "description": "Checkout specific file",
                    "params": {
                        "current_directory": ".",
                        "target": "HEAD",
                        "files": ["file1.txt", "file2.py"]
                    }
                }
            ]
        } 