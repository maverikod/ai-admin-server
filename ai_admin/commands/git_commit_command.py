"""Git commit command for creating commits."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitCommitCommand(Command):
    """Create Git commits.
    
    This command supports:
    - Commit with message
    - Amend commits
    - Sign commits
    - Commit specific files
    - Allow empty commits
    """
    
    name = "git_commit"
    
    async def execute(
        self,
        current_directory: str,
        message: str,
        amend: bool = False,
        sign: bool = False,
        files: Optional[List[str]] = None,
        allow_empty: bool = False,
        no_verify: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        author: Optional[str] = None,
        date: Optional[str] = None,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Create a Git commit.
        
        Args:
            current_directory: Current working directory where to execute git commands
            message: Commit message
            amend: Amend the previous commit
            sign: Sign the commit with GPG
            files: Specific files to commit (optional)
            allow_empty: Allow empty commits
            no_verify: Skip pre-commit and commit-msg hooks
            verbose: Show detailed output
            quiet: Suppress output
            author: Override author (format: "Name <email>")
            date: Override commit date (format: "YYYY-MM-DD HH:MM:SS")
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
            
            # Validate message
            if not message and not amend:
                return ErrorResult(
                    message="Commit message is required (unless amending)",
                    code="MISSING_MESSAGE",
                    details={}
                )
            
            # Build git commit command
            cmd = ["git", "commit"]
            
            if amend:
                cmd.append("--amend")
            
            if sign:
                cmd.append("--gpg-sign")
            
            if allow_empty:
                cmd.append("--allow-empty")
            
            if no_verify:
                cmd.append("--no-verify")
            
            if verbose:
                cmd.append("--verbose")
            
            if quiet:
                cmd.append("--quiet")
            
            if author:
                cmd.extend(["--author", author])
            
            if date:
                cmd.extend(["--date", date])
            
            # Add message
            if message:
                cmd.extend(["-m", message])
            
            # Add specific files if provided
            if files:
                cmd.extend(files)
            
            # Execute git commit
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git commit failed: {result.stderr}",
                    code="GIT_COMMIT_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get commit information
            commit_info = await self._get_commit_info(repository_path)
            
            return SuccessResult(data={
                "message": f"Successfully created commit",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "commit_info": commit_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git commit: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_commit_info(self, repo_path: str) -> Dict[str, Any]:
        """Get information about the latest commit."""
        try:
            # Get commit hash
            hash_cmd = ["git", "rev-parse", "HEAD"]
            hash_result = subprocess.run(
                hash_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            commit_hash = hash_result.stdout.strip() if hash_result.returncode == 0 else "unknown"
            
            # Get commit message
            message_cmd = ["git", "log", "-1", "--pretty=format:%s"]
            message_result = subprocess.run(
                message_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            commit_message = message_result.stdout.strip() if message_result.returncode == 0 else "unknown"
            
            # Get commit author
            author_cmd = ["git", "log", "-1", "--pretty=format:%an <%ae>"]
            author_result = subprocess.run(
                author_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            commit_author = author_result.stdout.strip() if author_result.returncode == 0 else "unknown"
            
            # Get commit date
            date_cmd = ["git", "log", "-1", "--pretty=format:%cd"]
            date_result = subprocess.run(
                date_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            commit_date = date_result.stdout.strip() if date_result.returncode == 0 else "unknown"
            
            # Get files changed
            files_cmd = ["git", "diff", "--cached", "--name-only"]
            files_result = subprocess.run(
                files_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            files_changed = []
            if files_result.returncode == 0:
                files_changed = [line.strip() for line in files_result.stdout.strip().split('\n') if line.strip()]
            
            return {
                "hash": commit_hash,
                "message": commit_message,
                "author": commit_author,
                "date": commit_date,
                "files_changed": files_changed
            }
            
        except Exception:
            return {
                "hash": "unknown",
                "message": "unknown",
                "author": "unknown",
                "date": "unknown",
                "files_changed": []
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Create Git commits",
            "parameters": {
                "current_directory": {
                    "type": "string",
                    "description": "Current working directory where to execute git commands",
                    "required": True
                },
                "message": {
                    "type": "string",
                    "description": "Commit message"
                },
                "amend": {
                    "type": "boolean",
                    "description": "Amend the previous commit",
                    "default": False
                },
                "sign": {
                    "type": "boolean",
                    "description": "Sign the commit with GPG",
                    "default": False
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific files to commit (optional)"
                },
                "allow_empty": {
                    "type": "boolean",
                    "description": "Allow empty commits",
                    "default": False
                },
                "no_verify": {
                    "type": "boolean",
                    "description": "Skip pre-commit and commit-msg hooks",
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
                "author": {
                    "type": "string",
                    "description": "Override author (format: \"Name <email>\")"
                },
                "date": {
                    "type": "string",
                    "description": "Override commit date (format: \"YYYY-MM-DD HH:MM:SS\")"
                },
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository (optional, defaults to current_directory)"
                }
            },
            "examples": [
                {
                    "description": "Create a commit with message",
                    "params": {
                        "current_directory": ".",
                        "message": "Add new feature"
                    }
                },
                {
                    "description": "Amend previous commit",
                    "params": {
                        "current_directory": ".",
                        "message": "Updated commit message",
                        "amend": True
                    }
                },
                {
                    "description": "Sign commit",
                    "params": {
                        "current_directory": ".",
                        "message": "Signed commit",
                        "sign": True
                    }
                },
                {
                    "description": "Commit specific files",
                    "params": {
                        "current_directory": ".",
                        "message": "Update specific files",
                        "files": ["file1.txt", "file2.py"]
                    }
                }
            ]
        } 