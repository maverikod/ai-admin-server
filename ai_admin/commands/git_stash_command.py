"""Git stash command for temporarily saving changes."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitStashCommand(Command):
    """Manage Git stash.
    
    This command supports:
    - Save changes to stash
    - List stashes
    - Apply stashes
    - Pop stashes
    - Drop stashes
    - Clear all stashes
    - Show stash contents
    """
    
    name = "git_stash"
    
    async def execute(
        self,
        current_directory: str,
        action: str = "list",
        stash_name: Optional[str] = None,
        message: Optional[str] = None,
        include_untracked: bool = False,
        include_ignored: bool = False,
        keep_index: bool = False,
        patch: bool = False,
        all: bool = False,
        drop: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Manage Git stash.
        
        Args:
            current_directory: Current working directory where to execute git commands
            action: Action to perform (list, save, apply, pop, drop, clear, show)
            stash_name: Name of the stash (optional, defaults to latest)
            message: Stash message
            include_untracked: Include untracked files
            include_ignored: Include ignored files
            keep_index: Keep changes in index
            patch: Interactive patch mode
            all: Include all files
            drop: Drop stash after applying
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
            
            # Build git stash command based on action
            if action == "list":
                cmd = ["git", "stash", "list"]
                
            elif action == "save":
                cmd = ["git", "stash"]
                
                if message:
                    cmd.extend(["save", message])
                else:
                    cmd.append("push")
                
                if include_untracked:
                    cmd.append("-u")
                
                if include_ignored:
                    cmd.append("-a")
                
                if keep_index:
                    cmd.append("-k")
                
                if patch:
                    cmd.append("-p")
                
            elif action == "apply":
                cmd = ["git", "stash", "apply"]
                
                if stash_name:
                    cmd.append(stash_name)
                
            elif action == "pop":
                cmd = ["git", "stash", "pop"]
                
                if stash_name:
                    cmd.append(stash_name)
                
            elif action == "drop":
                cmd = ["git", "stash", "drop"]
                
                if stash_name:
                    cmd.append(stash_name)
                elif all:
                    cmd.append("--all")
                
            elif action == "clear":
                cmd = ["git", "stash", "clear"]
                
            elif action == "show":
                cmd = ["git", "stash", "show"]
                
                if stash_name:
                    cmd.append(stash_name)
                
                if drop:
                    cmd.append("-p")
                
            else:
                return ErrorResult(
                    message=f"Invalid action: {action}",
                    code="INVALID_ACTION",
                    details={"valid_actions": ["list", "save", "apply", "pop", "drop", "clear", "show"]}
                )
            
            # Execute git stash command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git stash {action} failed: {result.stderr}",
                    code="GIT_STASH_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get stash information
            stash_info = await self._get_stash_info(repository_path, action)
            
            return SuccessResult(data={
                "message": f"Successfully performed {action} action on stash",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "action": action,
                "stash_info": stash_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git stash: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_stash_info(self, repo_path: str, action: str) -> Dict[str, Any]:
        """Get information about stashes."""
        try:
            if action == "list":
                # Get stash list
                result = subprocess.run(
                    ["git", "stash", "list"],
                    capture_output=True,
                    text=True,
                    cwd=repo_path
                )
                
                stashes = []
                if result.returncode == 0:
                    stashes = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                
                # Get detailed stash information
                stash_details = []
                for stash in stashes[:5]:  # Limit to first 5 stashes for performance
                    stash_ref = stash.split(':')[0]
                    detail_result = subprocess.run(
                        ["git", "stash", "show", "-p", stash_ref],
                        capture_output=True,
                        text=True,
                        cwd=repo_path
                    )
                    
                    if detail_result.returncode == 0:
                        stash_details.append({
                            "ref": stash_ref,
                            "description": stash,
                            "diff": detail_result.stdout.strip()
                        })
                
                return {
                    "stashes": stashes,
                    "total_stashes": len(stashes),
                    "stash_details": stash_details
                }
            
            elif action == "save":
                return {
                    "saved_stash": "stash_info_available",
                    "message": "Changes stashed successfully"
                }
            
            elif action == "apply":
                return {
                    "applied_stash": "stash_info_available",
                    "message": "Stash applied successfully"
                }
            
            elif action == "pop":
                return {
                    "popped_stash": "stash_info_available",
                    "message": "Stash popped successfully"
                }
            
            elif action == "drop":
                return {
                    "dropped_stash": "stash_info_available",
                    "message": "Stash dropped successfully"
                }
            
            elif action == "clear":
                return {
                    "cleared_stashes": "stash_info_available",
                    "message": "All stashes cleared successfully"
                }
            
            elif action == "show":
                return {
                    "stash_content": "stash_info_available",
                    "message": "Stash content retrieved successfully"
                }
            
            return {"message": "Action completed"}
            
        except Exception:
            return {"message": "Could not retrieve stash information"} 