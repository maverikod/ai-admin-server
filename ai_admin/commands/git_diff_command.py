"""Git diff command for viewing differences in Git."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitDiffCommand(Command):
    """Show differences in Git.
    
    This command supports:
    - Show working directory changes
    - Show staged changes
    - Show changes between commits
    - Show changes for specific files
    - Unified diff format
    - Word diff
    - Color output
    """
    
    name = "git_diff"
    
    async def execute(
        self,
        commit1: Optional[str] = None,
        commit2: Optional[str] = None,
        files: Optional[List[str]] = None,
        staged: bool = False,
        cached: bool = False,
        unified: Optional[int] = None,
        word_diff: bool = False,
        color: bool = False,
        stat: bool = False,
        name_only: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Show differences in Git.
        
        Args:
            commit1: First commit or reference (optional)
            commit2: Second commit or reference (optional)
            files: Specific files to diff (optional)
            staged: Show staged changes (--cached)
            cached: Show staged changes (alias for staged)
            unified: Number of context lines (default: 3)
            word_diff: Show word-level differences
            color: Use color output
            stat: Show diffstat instead of diff
            name_only: Show only names of changed files
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
            
            # Build git diff command
            cmd = ["git", "diff"]
            
            if staged or cached:
                cmd.append("--cached")
            
            if unified is not None:
                cmd.extend(["--unified", str(unified)])
            
            if word_diff:
                cmd.append("--word-diff")
            
            if color:
                cmd.append("--color")
            
            if stat:
                cmd.append("--stat")
            
            if name_only:
                cmd.append("--name-only")
            
            # Add commits if specified
            if commit1 and commit2:
                cmd.extend([commit1, commit2])
            elif commit1:
                cmd.append(commit1)
            
            # Add specific files if provided
            if files:
                cmd.extend(files)
            
            # Execute git diff
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git diff failed: {result.stderr}",
                    code="GIT_DIFF_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get diff information
            diff_info = await self._get_diff_info(repository_path, commit1, commit2, staged)
            
            return SuccessResult(data={
                "message": f"Successfully generated diff",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "diff_output": result.stdout,
                "diff_info": diff_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git diff: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_diff_info(self, repo_path: str, commit1: Optional[str], commit2: Optional[str], staged: bool) -> Dict[str, Any]:
        """Get information about the diff operation."""
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
            
            # Get HEAD commit
            head_cmd = ["git", "rev-parse", "HEAD"]
            head_result = subprocess.run(
                head_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            head_commit = head_result.stdout.strip() if head_result.returncode == 0 else "unknown"
            
            # Get diff stats
            stats_cmd = ["git", "diff", "--stat"]
            if staged:
                stats_cmd.append("--cached")
            stats_result = subprocess.run(
                stats_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            diff_stats = stats_result.stdout.strip() if stats_result.returncode == 0 else ""
            
            # Count changed files
            files_cmd = ["git", "diff", "--name-only"]
            if staged:
                files_cmd.append("--cached")
            files_result = subprocess.run(
                files_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            changed_files = []
            if files_result.returncode == 0:
                changed_files = [line.strip() for line in files_result.stdout.strip().split('\n') if line.strip()]
            
            return {
                "current_branch": current_branch,
                "head_commit": head_commit,
                "commit1": commit1,
                "commit2": commit2,
                "staged": staged,
                "diff_stats": diff_stats,
                "changed_files": changed_files,
                "files_count": len(changed_files)
            }
            
        except Exception:
            return {
                "current_branch": "unknown",
                "head_commit": "unknown",
                "commit1": commit1,
                "commit2": commit2,
                "staged": staged,
                "diff_stats": "",
                "changed_files": [],
                "files_count": 0
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Show differences in Git",
            "parameters": {
                "commit1": {
                    "type": "string",
                    "description": "First commit or reference (optional)"
                },
                "commit2": {
                    "type": "string",
                    "description": "Second commit or reference (optional)"
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific files to diff (optional)"
                },
                "staged": {
                    "type": "boolean",
                    "description": "Show staged changes (--cached)",
                    "default": False
                },
                "cached": {
                    "type": "boolean",
                    "description": "Show staged changes (alias for staged)",
                    "default": False
                },
                "unified": {
                    "type": "integer",
                    "description": "Number of context lines (default: 3)"
                },
                "word_diff": {
                    "type": "boolean",
                    "description": "Show word-level differences",
                    "default": False
                },
                "color": {
                    "type": "boolean",
                    "description": "Use color output",
                    "default": False
                },
                "stat": {
                    "type": "boolean",
                    "description": "Show diffstat instead of diff",
                    "default": False
                },
                "name_only": {
                    "type": "boolean",
                    "description": "Show only names of changed files",
                    "default": False
                },
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository (optional, defaults to current directory)"
                }
            },
            "examples": [
                {
                    "description": "Show working directory changes",
                    "params": {}
                },
                {
                    "description": "Show staged changes",
                    "params": {
                        "staged": True
                    }
                },
                {
                    "description": "Show changes between commits",
                    "params": {
                        "commit1": "HEAD~1",
                        "commit2": "HEAD"
                    }
                },
                {
                    "description": "Show changes for specific file",
                    "params": {
                        "files": ["README.md"]
                    }
                },
                {
                    "description": "Show diffstat",
                    "params": {
                        "stat": True
                    }
                },
                {
                    "description": "Show word-level diff",
                    "params": {
                        "word_diff": True
                    }
                },
                {
                    "description": "Show only changed file names",
                    "params": {
                        "name_only": True
                    }
                }
            ]
        } 