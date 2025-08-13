"""Git grep command for searching in Git repository."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitGrepCommand(Command):
    """Search for patterns in Git repository.
    
    This command supports:
    - Search in tracked files
    - Search in specific commits
    - Case insensitive search
    - Regular expression search
    - Show line numbers
    - Show file names only
    - Search in specific files
    """
    
    name = "git_grep"
    
    async def execute(
        self,
        current_directory: str,
        pattern: str,
        files: Optional[List[str]] = None,
        commit: Optional[str] = None,
        case_insensitive: bool = False,
        regex: bool = False,
        extended_regex: bool = False,
        fixed_strings: bool = False,
        line_number: bool = True,
        name_only: bool = False,
        count: bool = False,
        ignore_case: bool = False,
        word_regexp: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Search for patterns in Git repository.
        
        Args:
            current_directory: Current working directory where to execute git commands
            pattern: Search pattern
            files: Specific files to search in (optional)
            commit: Search in specific commit (optional)
            case_insensitive: Case insensitive search
            regex: Use regular expressions
            extended_regex: Use extended regular expressions
            fixed_strings: Treat pattern as fixed string
            line_number: Show line numbers
            name_only: Show only file names
            count: Show only count of matches
            ignore_case: Ignore case differences
            word_regexp: Match whole words only
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
            
            # Validate pattern
            if not pattern:
                return ErrorResult(
                    message="Search pattern is required",
                    code="MISSING_PATTERN",
                    details={}
                )
            
            # Build git grep command
            cmd = ["git", "grep"]
            
            if case_insensitive or ignore_case:
                cmd.append("-i")
            
            if regex:
                cmd.append("-E")
            elif extended_regex:
                cmd.append("-E")
            elif fixed_strings:
                cmd.append("-F")
            
            if not line_number:
                cmd.append("-h")
            
            if name_only:
                cmd.append("-l")
            
            if count:
                cmd.append("-c")
            
            if word_regexp:
                cmd.append("-w")
            
            # Add pattern
            cmd.append(pattern)
            
            # Add commit if specified
            if commit:
                cmd.append(commit)
            
            # Add specific files if provided
            if files:
                cmd.extend(files)
            
            # Execute git grep
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            # Git grep returns 1 when no matches found, which is not an error
            if result.returncode not in [0, 1]:
                return ErrorResult(
                    message=f"Git grep failed: {result.stderr}",
                    code="GIT_GREP_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Parse grep output
            grep_info = await self._parse_grep_output(result.stdout, count)
            
            return SuccessResult(data={
                "message": f"Successfully searched for pattern '{pattern}'",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "pattern": pattern,
                "grep_info": grep_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git grep: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _parse_grep_output(self, output: str, count: bool) -> Dict[str, Any]:
        """Parse git grep output into structured data."""
        if not output.strip():
            return {
                "matches": [],
                "total_matches": 0,
                "files_with_matches": [],
                "message": "No matches found"
            }
        
        lines = output.strip().split('\n')
        matches = []
        files_with_matches = set()
        
        if count:
            # Parse count output
            for line in lines:
                if ':' in line:
                    file_path, count_str = line.split(':', 1)
                    try:
                        count_val = int(count_str.strip())
                        matches.append({
                            "file": file_path.strip(),
                            "count": count_val
                        })
                        if count_val > 0:
                            files_with_matches.add(file_path.strip())
                    except ValueError:
                        continue
        else:
            # Parse regular output
            for line in lines:
                if ':' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        file_path = parts[0]
                        line_number = parts[1]
                        content = parts[2]
                        
                        matches.append({
                            "file": file_path,
                            "line": line_number,
                            "content": content
                        })
                        files_with_matches.add(file_path)
                    elif len(parts) == 2:
                        # File name only mode
                        file_path = parts[0]
                        files_with_matches.add(file_path)
        
        return {
            "matches": matches,
            "total_matches": len(matches),
            "files_with_matches": list(files_with_matches),
            "total_files": len(files_with_matches),
            "message": f"Found {len(matches)} matches in {len(files_with_matches)} files"
        } 