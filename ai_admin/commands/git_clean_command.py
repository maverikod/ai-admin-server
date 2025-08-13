"""Git clean command for removing untracked files."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitCleanCommand(Command):
    """Remove untracked files from Git repository.
    
    This command supports:
    - Remove untracked files
    - Remove untracked directories
    - Dry run mode
    - Force removal
    - Interactive mode
    - Remove ignored files
    """
    
    name = "git_clean"
    
    async def execute(
        self,
        current_directory: str,
        force: bool = False,
        dry_run: bool = True,
        directories: bool = False,
        ignored: bool = False,
        interactive: bool = False,
        quiet: bool = False,
        paths: Optional[List[str]] = None,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Remove untracked files from Git repository.
        
        Args:
            current_directory: Current working directory where to execute git commands
            force: Force removal (required for actual deletion)
            dry_run: Show what would be removed without actually removing
            directories: Remove untracked directories too
            ignored: Remove ignored files too
            interactive: Interactive mode
            quiet: Suppress output
            paths: Specific paths to clean (optional)
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
            
            # Build git clean command
            cmd = ["git", "clean"]
            
            if dry_run:
                cmd.append("-n")
            
            if force:
                cmd.append("-f")
            
            if directories:
                cmd.append("-d")
            
            if ignored:
                cmd.append("-x")
            
            if interactive:
                cmd.append("-i")
            
            if quiet:
                cmd.append("-q")
            
            # Add specific paths if provided
            if paths:
                cmd.extend(paths)
            
            # Execute git clean
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git clean failed: {result.stderr}",
                    code="GIT_CLEAN_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Parse clean output
            clean_info = await self._parse_clean_output(result.stdout, dry_run)
            
            return SuccessResult(data={
                "message": f"Successfully {'simulated' if dry_run else 'performed'} git clean",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "dry_run": dry_run,
                "clean_info": clean_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git clean: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _parse_clean_output(self, output: str, dry_run: bool) -> Dict[str, Any]:
        """Parse git clean output into structured data."""
        if not output.strip():
            return {
                "files_to_remove": [],
                "directories_to_remove": [],
                "total_items": 0,
                "message": "No untracked files found"
            }
        
        lines = output.strip().split('\n')
        files_to_remove = []
        directories_to_remove = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse git clean output format
            if line.startswith('Would remove ') or line.startswith('Removing '):
                # Extract file/directory path
                if line.startswith('Would remove '):
                    path = line[13:]  # Remove "Would remove "
                else:
                    path = line[10:]  # Remove "Removing "
                
                # Determine if it's a directory or file
                if path.endswith('/'):
                    directories_to_remove.append(path.rstrip('/'))
                else:
                    files_to_remove.append(path)
        
        return {
            "files_to_remove": files_to_remove,
            "directories_to_remove": directories_to_remove,
            "total_items": len(files_to_remove) + len(directories_to_remove),
            "message": f"{'Would remove' if dry_run else 'Removed'} {len(files_to_remove)} files and {len(directories_to_remove)} directories"
        } 