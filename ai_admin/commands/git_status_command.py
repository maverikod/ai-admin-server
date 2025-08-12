"""Git status command for checking repository status."""

import os
import subprocess
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitStatusCommand(Command):
    """Check the status of a Git repository.
    
    This command provides detailed information about:
    - Working directory status
    - Staged changes
    - Untracked files
    - Branch information
    - Commit status
    """
    
    name = "git_status"
    
    async def execute(
        self,
        current_directory: str,
        repository_path: Optional[str] = None,
        porcelain: bool = False,
        branch: bool = False,
        show_stash: bool = False,
        **kwargs
    ):
        """
        Get Git repository status.
        
        Args:
            current_directory: Current working directory where to execute git commands
            repository_path: Path to repository (optional, defaults to current_directory)
            porcelain: Use porcelain format for machine-readable output
            branch: Show branch information
            show_stash: Include stash information
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
            
            # Build git status command
            cmd = ["git", "status"]
            
            if porcelain:
                cmd.append("--porcelain")
            else:
                # Use normal format to get untracked files info
                pass  # Default format shows untracked files
            
            if branch:
                cmd.append("--branch")
            
            # Execute git status
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git status failed: {result.stderr}",
                    code="GIT_STATUS_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Parse status output
            status_info = await self._parse_status_output(result.stdout, repository_path)
            
            # Get untracked files separately
            untracked_files = await self._get_untracked_files(repository_path)
            status_info["untracked"] = untracked_files
            if untracked_files:
                status_info["clean"] = False
            
            # Add stash information if requested
            if show_stash:
                stash_info = await self._get_stash_info(repository_path)
                status_info["stash"] = stash_info
            
            return SuccessResult(data={
                "message": f"Git status for repository at '{repository_path}'",
                "repository_path": os.path.abspath(repository_path),
                "status": status_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git status: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _parse_status_output(self, output: str, repo_path: str) -> Dict[str, Any]:
        """Parse git status output into structured data."""
        lines = output.strip().split('\n')
        
        status_info = {
            "branch": "unknown",
            "upstream": None,
            "ahead": 0,
            "behind": 0,
            "staged": [],
            "modified": [],
            "untracked": [],
            "deleted": [],
            "renamed": [],
            "conflicts": [],
            "clean": True
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse branch information
            if line.startswith("On branch "):
                status_info["branch"] = line[11:]
            elif line.startswith("HEAD detached at "):
                status_info["branch"] = line[17:]
            elif "Your branch is ahead of" in line:
                status_info["ahead"] = int(line.split()[6])
            elif "Your branch is behind" in line:
                status_info["behind"] = int(line.split()[6])
            elif "Your branch and" in line and "have diverged" in line:
                parts = line.split()
                status_info["ahead"] = int(parts[6])
                status_info["behind"] = int(parts[10])
            
            # Parse file status (porcelain format)
            elif len(line) >= 2 and line[0] in 'MADRCU' and line[1] in 'MADRCU':
                status_code = line[:2]
                file_path = line[3:]
                
                if status_code[0] == 'M' or status_code[1] == 'M':
                    status_info["modified"].append(file_path)
                elif status_code[0] == 'A' or status_code[1] == 'A':
                    status_info["staged"].append(file_path)
                elif status_code[0] == 'D' or status_code[1] == 'D':
                    status_info["deleted"].append(file_path)
                elif status_code[0] == 'R' or status_code[1] == 'R':
                    status_info["renamed"].append(file_path)
                elif status_code[0] == 'U' or status_code[1] == 'U':
                    status_info["conflicts"].append(file_path)
                
                status_info["clean"] = False
            
            # Parse untracked files
            elif line.startswith("Untracked files:"):
                continue
            elif line.startswith("  ") and not line.startswith("   "):
                file_path = line.strip()
                if file_path and not file_path.startswith("("):
                    status_info["untracked"].append(file_path)
                    status_info["clean"] = False
        
        # Get additional repository info
        repo_info = await self._get_repository_info(repo_path)
        status_info.update(repo_info)
        
        return status_info
    
    async def _get_untracked_files(self, repo_path: str) -> List[str]:
        """Get list of untracked files."""
        try:
            cmd = ["git", "ls-files", "--others", "--exclude-standard"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            if result.returncode == 0:
                files = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                return files
            else:
                return []
        except Exception:
            return []
    
    async def _get_repository_info(self, repo_path: str) -> Dict[str, Any]:
        """Get additional repository information."""
        try:
            # Get current commit
            commit_cmd = ["git", "rev-parse", "HEAD"]
            commit_result = subprocess.run(
                commit_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            current_commit = commit_result.stdout.strip() if commit_result.returncode == 0 else "unknown"
            
            # Get commit message
            message_cmd = ["git", "log", "-1", "--pretty=format:%s"]
            message_result = subprocess.run(
                message_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            commit_message = message_result.stdout.strip() if message_result.returncode == 0 else "unknown"
            
            # Get remote information
            remote_cmd = ["git", "remote", "-v"]
            remote_result = subprocess.run(
                remote_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            remotes = {}
            if remote_result.returncode == 0:
                for line in remote_result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            remote_name = parts[0]
                            remote_url = parts[1]
                            remotes[remote_name] = remote_url
            
            return {
                "current_commit": current_commit,
                "commit_message": commit_message,
                "remotes": remotes
            }
            
        except Exception:
            return {
                "current_commit": "unknown",
                "commit_message": "unknown",
                "remotes": {}
            }
    
    async def _get_stash_info(self, repo_path: str) -> List[Dict[str, Any]]:
        """Get stash information."""
        try:
            stash_cmd = ["git", "stash", "list", "--format=format:%H|%s|%D"]
            stash_result = subprocess.run(
                stash_cmd,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            stashes = []
            if stash_result.returncode == 0:
                for line in stash_result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            stashes.append({
                                "hash": parts[0],
                                "message": parts[1],
                                "date": parts[2]
                            })
            
            return stashes
            
        except Exception:
            return []
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "name": cls.name,
            "description": "Check the status of a Git repository",
            "parameters": {
                "current_directory": {
                    "type": "string",
                    "description": "Current working directory where to execute git commands",
                    "required": True
                },
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository (optional, defaults to current_directory)"
                },
                "porcelain": {
                    "type": "boolean",
                    "description": "Use porcelain format for machine-readable output",
                    "default": False
                },
                "branch": {
                    "type": "boolean",
                    "description": "Show branch information",
                    "default": False
                },
                "show_stash": {
                    "type": "boolean",
                    "description": "Include stash information",
                    "default": False
                }
            },
            "examples": [
                {
                    "description": "Check status of current repository",
                    "params": {
                        "current_directory": ".",}
                },
                {
                    "description": "Check status with branch info",
                    "params": {
                        "current_directory": ".",
                        "branch": True,
                        "show_stash": True
                    }
                },
                {
                    "description": "Check status of specific repository",
                    "params": {
                        "current_directory": ".",
                        "repository_path": "/path/to/repo"
                    }
                }
            ]
        } 