"""Git reset command for resetting changes in Git."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitResetCommand(Command):
    """Reset Git repository state.
    
    This command supports:
    - Soft reset (keep changes in staging area)
    - Mixed reset (default, keep changes in working directory)
    - Hard reset (discard all changes)
    - Reset specific files
    - Reset to specific commit
    """
    
    name = "git_reset"
    
    async def execute(
        self,
        commit: str = "HEAD",
        mode: str = "mixed",
        files: Optional[List[str]] = None,
        quiet: bool = False,
        verbose: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Reset Git repository state.
        
        Args:
            commit: Commit to reset to (default: HEAD)
            mode: Reset mode (soft, mixed, hard)
            files: Specific files to reset (optional)
            quiet: Suppress output
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
            
            # Validate mode
            valid_modes = ["soft", "mixed", "hard"]
            if mode not in valid_modes:
                return ErrorResult(
                    message=f"Invalid reset mode: {mode}",
                    code="INVALID_MODE",
                    details={"valid_modes": valid_modes}
                )
            
            # Build git reset command
            cmd = ["git", "reset"]
            
            if mode == "soft":
                cmd.append("--soft")
            elif mode == "hard":
                cmd.append("--hard")
            # mixed is default, no flag needed
            
            if quiet:
                cmd.append("--quiet")
            
            if verbose:
                cmd.append("--verbose")
            
            # Add commit
            cmd.append(commit)
            
            # Add specific files if provided
            if files:
                cmd.extend(files)
            
            # Execute git reset
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git reset failed: {result.stderr}",
                    code="GIT_RESET_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get reset information
            reset_info = await self._get_reset_info(repository_path, commit, mode)
            
            return SuccessResult(data={
                "message": f"Successfully reset to {commit} ({mode} mode)",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "reset_info": reset_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git reset: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_reset_info(self, repo_path: str, commit: str, mode: str) -> Dict[str, Any]:
        """Get information about the reset operation."""
        try:
            # Get current HEAD
            head_cmd = ["git", "rev-parse", "HEAD"]
            head_result = subprocess.run(
                head_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            current_head = head_result.stdout.strip() if head_result.returncode == 0 else "unknown"
            
            # Get commit info
            log_cmd = ["git", "log", "-1", "--pretty=format:%H|%s|%an|%cd"]
            log_result = subprocess.run(
                log_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            commit_info = {}
            if log_result.returncode == 0 and log_result.stdout.strip():
                parts = log_result.stdout.strip().split('|')
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
            
            # Get staged files
            staged_cmd = ["git", "diff", "--cached", "--name-only"]
            staged_result = subprocess.run(
                staged_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            staged_files = []
            if staged_result.returncode == 0:
                staged_files = [line.strip() for line in staged_result.stdout.strip().split('\n') if line.strip()]
            
            return {
                "target_commit": commit,
                "current_head": current_head,
                "reset_mode": mode,
                "commit_info": commit_info,
                "working_directory_status": len(status_lines),
                "staged_files_count": len(staged_files),
                "status_lines": status_lines[:10],  # Limit to first 10 lines
                "staged_files": staged_files[:10]   # Limit to first 10 files
            }
            
        except Exception:
            return {
                "target_commit": commit,
                "current_head": "unknown",
                "reset_mode": mode,
                "commit_info": {},
                "working_directory_status": 0,
                "staged_files_count": 0,
                "status_lines": [],
                "staged_files": []
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Reset Git repository state",
            "parameters": {
                "commit": {
                    "type": "string",
                    "description": "Commit to reset to",
                    "default": "HEAD"
                },
                "mode": {
                    "type": "string",
                    "description": "Reset mode",
                    "default": "mixed",
                    "enum": ["soft", "mixed", "hard"]
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific files to reset (optional)"
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
                    "description": "Path to repository (optional, defaults to current directory)"
                }
            },
            "examples": [
                {
                    "description": "Soft reset to previous commit",
                    "params": {
                        "commit": "HEAD~1",
                        "mode": "soft"
                    }
                },
                {
                    "description": "Hard reset to specific commit",
                    "params": {
                        "commit": "abc1234",
                        "mode": "hard"
                    }
                },
                {
                    "description": "Mixed reset (default)",
                    "params": {
                        "commit": "HEAD"
                    }
                },
                {
                    "description": "Reset specific files",
                    "params": {
                        "commit": "HEAD",
                        "files": ["file1.txt", "file2.py"]
                    }
                },
                {
                    "description": "Reset to remote branch",
                    "params": {
                        "commit": "origin/main",
                        "mode": "hard"
                    }
                }
            ]
        } 