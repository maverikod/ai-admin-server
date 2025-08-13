"""Git log command for viewing commit history."""

import os
import subprocess
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitLogCommand(Command):
    """View Git commit history.
    
    This command supports:
    - View commit history
    - Filter by author, date, file
    - Show specific number of commits
    - Pretty format output
    - Graph visualization
    - Search commits
    """
    
    name = "git_log"
    
    async def execute(
        self,
        current_directory: str,
        max_count: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        committer: Optional[str] = None,
        grep: Optional[str] = None,
        files: Optional[List[str]] = None,
        pretty: Optional[str] = None,
        oneline: bool = False,
        graph: bool = False,
        stat: bool = False,
        name_only: bool = False,
        reverse: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        View Git commit history.
        
        Args:
            current_directory: Current working directory where to execute git commands
            max_count: Maximum number of commits to show
            since: Show commits after this date
            until: Show commits before this date
            author: Filter by author
            committer: Filter by committer
            grep: Search commit messages
            files: Show commits that touch specified files
            pretty: Pretty format (short, medium, full, fuller, email, raw, format)
            oneline: Show one line per commit
            graph: Show ASCII graph of commit history
            stat: Show diffstat
            name_only: Show only names of changed files
            reverse: Show commits in reverse order
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
            
            # Build git log command
            cmd = ["git", "log"]
            
            if max_count:
                cmd.extend(["-n", str(max_count)])
            
            if since:
                cmd.extend(["--since", since])
            
            if until:
                cmd.extend(["--until", until])
            
            if author:
                cmd.extend(["--author", author])
            
            if committer:
                cmd.extend(["--committer", committer])
            
            if grep:
                cmd.extend(["--grep", grep])
            
            if pretty:
                cmd.extend(["--pretty", pretty])
            elif oneline:
                cmd.append("--oneline")
            
            if graph:
                cmd.append("--graph")
            
            if stat:
                cmd.append("--stat")
            
            if name_only:
                cmd.append("--name-only")
            
            if reverse:
                cmd.append("--reverse")
            
            # Add files if specified
            if files:
                cmd.extend(files)
            
            # Execute git log
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git log failed: {result.stderr}",
                    code="GIT_LOG_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Parse log output
            log_entries = await self._parse_log_output(result.stdout, oneline)
            
            return SuccessResult(data={
                "message": f"Successfully retrieved commit history",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "log_entries": log_entries,
                "total_commits": len(log_entries),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git log: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _parse_log_output(self, output: str, oneline: bool) -> List[Dict[str, Any]]:
        """Parse git log output into structured data."""
        if not output.strip():
            return []
        
        entries = []
        lines = output.strip().split('\n')
        
        if oneline:
            # Simple oneline format
            for line in lines:
                if line.strip():
                    parts = line.split(' ', 1)
                    if len(parts) >= 2:
                        entries.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "format": "oneline"
                        })
        else:
            # Try to parse detailed format
            current_entry = {}
            for line in lines:
                line = line.strip()
                if not line:
                    if current_entry:
                        entries.append(current_entry)
                        current_entry = {}
                    continue
                
                if line.startswith('commit '):
                    if current_entry:
                        entries.append(current_entry)
                    current_entry = {"hash": line[7:], "format": "detailed"}
                elif line.startswith('Author: '):
                    current_entry["author"] = line[8:]
                elif line.startswith('Date: '):
                    current_entry["date"] = line[6:]
                elif line.startswith('Merge: '):
                    current_entry["merge"] = line[7:]
                elif not line.startswith('    '):
                    # This might be a message line
                    if "message" not in current_entry:
                        current_entry["message"] = line
                    else:
                        current_entry["message"] += "\n" + line
                else:
                    # Indented line - part of commit message
                    if "message" in current_entry:
                        current_entry["message"] += "\n" + line[4:]
                    else:
                        current_entry["message"] = line[4:]
            
            # Add the last entry
            if current_entry:
                entries.append(current_entry)
        
        return entries 