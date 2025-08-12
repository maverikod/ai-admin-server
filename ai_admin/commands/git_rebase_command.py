"""Git rebase command for rebasing branches in Git."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitRebaseCommand(Command):
    """Rebase Git branches.
    
    This command supports:
    - Interactive rebase
    - Continue/abort/skip rebase
    - Rebase onto specific branch
    - Preserve merges
    - Squash commits
    """
    
    name = "git_rebase"
    
    async def execute(
        self,
        current_directory: str,
        action: str = "start",
        base: Optional[str] = None,
        branch: Optional[str] = None,
        interactive: bool = False,
        preserve_merges: bool = False,
        squash: bool = False,
        continue_rebase: bool = False,
        abort: bool = False,
        skip: bool = False,
        quiet: bool = False,
        verbose: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Rebase Git branches.
        
        Args:
            current_directory: Current working directory where to execute git commands
            action: Action to perform (start, continue, abort, skip)
            base: Base branch or commit to rebase onto
            branch: Branch to rebase (optional, uses current branch if not specified)
            interactive: Use interactive rebase
            preserve_merges: Preserve merge commits
            squash: Squash commits into one
            continue_rebase: Continue rebase after resolving conflicts
            abort: Abort rebase
            skip: Skip current commit in rebase
            quiet: Suppress output
            verbose: Show detailed output
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
            
            # Build git rebase command based on action
            if action == "start":
                if not base:
                    return ErrorResult(
                        message="base is required for start action",
                        code="MISSING_BASE",
                        details={}
                    )
                
                cmd = ["git", "rebase"]
                
                if interactive:
                    cmd.append("--interactive")
                
                if preserve_merges:
                    cmd.append("--preserve-merges")
                
                if squash:
                    cmd.append("--squash")
                
                if quiet:
                    cmd.append("--quiet")
                
                if verbose:
                    cmd.append("--verbose")
                
                # Add base
                cmd.append(base)
                
                # Add branch if specified
                if branch:
                    cmd.append(branch)
                
            elif action == "continue":
                cmd = ["git", "rebase", "--continue"]
                
            elif action == "abort":
                cmd = ["git", "rebase", "--abort"]
                
            elif action == "skip":
                cmd = ["git", "rebase", "--skip"]
                
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="UNKNOWN_ACTION",
                    details={"valid_actions": ["start", "continue", "abort", "skip"]}
                )
            
            # Execute git rebase
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git rebase failed: {result.stderr}",
                    code="GIT_REBASE_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get rebase information
            rebase_info = await self._get_rebase_info(repository_path, action, base)
            
            return SuccessResult(data={
                "message": f"Successfully executed git rebase {action}",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "rebase_info": rebase_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git rebase: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_rebase_info(self, repo_path: str, action: str, base: Optional[str] = None) -> Dict[str, Any]:
        """Get information about the rebase operation."""
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
            

        # Check if rebase is in progress
            rebase_merge_cmd = ["git", "rev-parse", "--git-path", "rebase-merge"]
            rebase_merge_result = subprocess.run(
                rebase_merge_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            rebase_merge_dir = rebase_merge_result.stdout.strip() if rebase_merge_result.returncode == 0 else ""
            is_rebasing = os.path.exists(rebase_merge_dir)
            
            # Get current branch
            branch_cmd = ["git", "branch", "--show-current"]
            branch_result = subprocess.run(
                branch_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            # Get HEAD
            head_cmd = ["git", "rev-parse", "HEAD"]
            head_result = subprocess.run(
                head_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            current_head = head_result.stdout.strip() if head_result.returncode == 0 else "unknown"
            
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
            
            # Get recent commits
            log_cmd = ["git", "log", "--oneline", "-5"]
            log_result = subprocess.run(
                log_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            recent_commits = []
            if log_result.returncode == 0:
                recent_commits = [line.strip() for line in log_result.stdout.strip().split('\n') if line.strip()]
            
            return {
                "action": action,
                "base": base,
                "is_rebasing": is_rebasing,
                "current_branch": current_branch,
                "current_head": current_head,
                "working_directory_status": len(status_lines),
                "status_lines": status_lines[:10],  # Limit to first 10 lines
                "recent_commits": recent_commits
            }
            
        except Exception:
            return {
                "action": action,
                "base": base,
                "is_rebasing": False,
                "current_branch": "unknown",
                "current_head": "unknown",
                "working_directory_status": 0,
                "status_lines": [],
                "recent_commits": []
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Rebase Git branches",
            "parameters": {
                "current_directory": {
                    "type": "string",
                    "description": "Current working directory where to execute git commands",
                    "required": True
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "default": "start",
                    "enum": ["start", "continue", "abort", "skip"]
                },
                "base": {
                    "type": "string",
                    "description": "Base branch or commit to rebase onto"
                },
                "branch": {
                    "type": "string",
                    "description": "Branch to rebase (optional, uses current branch if not specified)"
                },
                "interactive": {
                    "type": "boolean",
                    "description": "Use interactive rebase",
                    "default": False
                },
                "preserve_merges": {
                    "type": "boolean",
                    "description": "Preserve merge commits",
                    "default": False
                },
                "squash": {
                    "type": "boolean",
                    "description": "Squash commits into one",
                    "default": False
                },
                "continue_rebase": {
                    "type": "boolean",
                    "description": "Continue rebase after resolving conflicts",
                    "default": False
                },
                "abort": {
                    "type": "boolean",
                    "description": "Abort rebase",
                    "default": False
                },
                "skip": {
                    "type": "boolean",
                    "description": "Skip current commit in rebase",
                    "default": False
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
                },
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository (optional, defaults to current_directory)"
                }
            },
            "examples": [
                {
                    "description": "Start rebase onto main branch",
                    "params": {
                        "current_directory": ".",
                        "action": "start",
                        "base": "main"
                    }
                },
                {
                    "description": "Interactive rebase",
                    "params": {
                        "current_directory": ".",
                        "action": "start",
                        "base": "main",
                        "interactive": True
                    }
                },
                {
                    "description": "Continue rebase",
                    "params": {
                        "current_directory": ".",
                        "action": "continue"
                    }
                },
                {
                    "description": "Abort rebase",
                    "params": {
                        "current_directory": ".",
                        "action": "abort"
                    }
                },
                {
                    "description": "Skip current commit",
                    "params": {
                        "current_directory": ".",
                        "action": "skip"
                    }
                },
                {
                    "description": "Squash rebase",
                    "params": {
                        "current_directory": ".",
                        "action": "start",
                        "base": "main",
                        "squash": True
                    }
                }
            ]
        } 