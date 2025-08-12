"""Git add command for staging files."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitAddCommand(Command):
    """Add files to Git staging area.
    
    This command supports:
    - Adding specific files
    - Adding all files
    - Interactive adding
    - Patch mode
    - Force adding
    """
    
    name = "git_add"
    
    async def execute(
        self,
        current_directory: str,
        files: Optional[List[str]] = None,
        all_files: bool = False,
        interactive: bool = False,
        patch: bool = False,
        force: bool = False,
        verbose: bool = False,
        dry_run: bool = False,
        ignore_errors: bool = False,
        ignore_missing: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Add files to Git staging area.
        
        Args:
            current_directory: Current working directory where to execute git commands
            files: List of files to add (optional)
            all_files: Add all files (equivalent to git add .)
            interactive: Use interactive mode
            patch: Use patch mode (interactive selection of hunks)
            force: Force add files (ignore .gitignore)
            verbose: Show detailed output
            dry_run: Show what would be added without actually adding
            ignore_errors: Continue even if some files cannot be added
            ignore_missing: Ignore missing files
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
            
            # Validate parameters
            if not files and not all_files and not interactive:
                return ErrorResult(
                    message="Must specify files, all_files=True, or interactive=True",
                    code="INVALID_PARAMETERS",
                    details={}
                )
            
            # Build git add command
            cmd = ["git", "add"]
            
            if interactive:
                cmd.append("--interactive")
            elif patch:
                cmd.append("--patch")
            
            if force:
                cmd.append("--force")
            
            if verbose:
                cmd.append("--verbose")
            
            if dry_run:
                cmd.append("--dry-run")
            
            if ignore_errors:
                cmd.append("--ignore-errors")
            
            if ignore_missing:
                cmd.append("--ignore-missing")
            
            # Add files or use . for all files
            if all_files:
                cmd.append(".")
            elif files:
                cmd.extend(files)
            
            # Execute git add
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git add failed: {result.stderr}",
                    code="GIT_ADD_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get staging area status
            staged_files = await self._get_staged_files(repository_path)
            
            return SuccessResult(data={
                "message": f"Successfully added files to staging area",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "staged_files": staged_files,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git add: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_staged_files(self, repo_path: str) -> List[str]:
        """Get list of staged files."""
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
            

        # Get staged files using git diff --cached --name-only
            cmd = ["git", "diff", "--cached", "--name-only"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            else:
                return []
                
        except Exception:
            return []
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Add files to Git staging area",
            "parameters": {
                "current_directory": {
                    "type": "string",
                    "description": "Current working directory where to execute git commands",
                    "required": True
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files to add (optional)"
                },
                "all_files": {
                    "type": "boolean",
                    "description": "Add all files (equivalent to git add .)",
                    "default": False
                },
                "interactive": {
                    "type": "boolean",
                    "description": "Use interactive mode",
                    "default": False
                },
                "patch": {
                    "type": "boolean",
                    "description": "Use patch mode (interactive selection of hunks)",
                    "default": False
                },
                "force": {
                    "type": "boolean",
                    "description": "Force add files (ignore .gitignore)",
                    "default": False
                },
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository (optional, defaults to current_directory)"
                }
            },
            "examples": [
                {
                    "description": "Add specific files",
                    "params": {
                        "current_directory": ".",
                        "files": ["file1.txt", "file2.py"]
                    }
                },
                {
                    "description": "Add all files",
                    "params": {
                        "current_directory": ".",
                        "all_files": True
                    }
                },
                {
                    "description": "Interactive add",
                    "params": {
                        "current_directory": ".",
                        "interactive": True
                    }
                },
                {
                    "description": "Force add ignored files",
                    "params": {
                        "current_directory": ".",
                        "files": ["ignored_file.txt"],
                        "force": True
                    }
                }
            ]
        } 