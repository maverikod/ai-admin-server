"""Git blame command for viewing line-by-line revision information."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitBlameCommand(Command):
    """Show line-by-line revision information for files.
    
    This command supports:
    - Show blame information for files
    - Show blame for specific lines
    - Show blame for specific commits
    - Show blame with different formats
    - Show blame with line numbers
    - Show blame with file names
    """
    
    name = "git_blame"
    
    async def execute(
        self,
        current_directory: str,
        file_path: str,
        commit: Optional[str] = None,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        line_number: bool = True,
        show_name: bool = True,
        show_email: bool = True,
        show_date: bool = True,
        show_time: bool = False,
        show_timezone: bool = False,
        show_file: bool = False,
        porcelain: bool = False,
        incremental: bool = False,
        encoding: Optional[str] = None,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Show line-by-line revision information for files.
        
        Args:
            current_directory: Current working directory where to execute git commands
            file_path: Path to the file to blame
            commit: Show blame for specific commit (optional)
            start_line: Start line number (optional)
            end_line: End line number (optional)
            line_number: Show line numbers
            show_name: Show author name
            show_email: Show author email
            show_date: Show commit date
            show_time: Show commit time
            show_timezone: Show timezone
            show_file: Show file name
            porcelain: Use porcelain format
            incremental: Use incremental format
            encoding: Specify file encoding
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
            
            # Validate file path
            if not file_path:
                return ErrorResult(
                    message="File path is required",
                    code="MISSING_FILE_PATH",
                    details={}
                )
            
            # Build git blame command
            cmd = ["git", "blame"]
            
            if porcelain:
                cmd.append("--porcelain")
            
            if incremental:
                cmd.append("--incremental")
            
            if not line_number:
                cmd.append("-l")
            
            if not show_name:
                cmd.append("-n")
            
            if not show_email:
                cmd.append("-e")
            
            if not show_date:
                cmd.append("-t")
            
            if show_time:
                cmd.append("--date=iso")
            
            if show_timezone:
                cmd.append("--date=iso-local")
            
            if show_file:
                cmd.append("-f")
            
            if encoding:
                cmd.extend(["--encoding", encoding])
            
            # Add commit if specified
            if commit:
                cmd.append(commit)
            
            # Add file path
            cmd.append(file_path)
            
            # Add line range if specified
            if start_line and end_line:
                cmd.extend(["-L", f"{start_line},{end_line}"])
            elif start_line:
                cmd.extend(["-L", f"{start_line},+1"])
            
            # Execute git blame
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git blame failed: {result.stderr}",
                    code="GIT_BLAME_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Parse blame output
            blame_info = await self._parse_blame_output(result.stdout, porcelain)
            
            return SuccessResult(data={
                "message": f"Successfully retrieved blame information for {file_path}",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "file_path": file_path,
                "blame_info": blame_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git blame: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _parse_blame_output(self, output: str, porcelain: bool) -> Dict[str, Any]:
        """Parse git blame output into structured data."""
        if not output.strip():
            return {
                "lines": [],
                "total_lines": 0,
                "commits": set(),
                "authors": set(),
                "message": "No blame information found"
            }
        
        lines = output.strip().split('\n')
        blame_lines = []
        commits = set()
        authors = set()
        
        if porcelain:
            # Parse porcelain format
            current_line = None
            current_commit = None
            current_author = None
            current_date = None
            
            for line in lines:
                if line.startswith('\t'):
                    # This is the actual line content
                    if current_line is not None:
                        blame_lines.append({
                            "line_number": current_line,
                            "commit": current_commit,
                            "author": current_author,
                            "date": current_date,
                            "content": line[1:]  # Remove leading tab
                        })
                        if current_commit:
                            commits.add(current_commit)
                        if current_author:
                            authors.add(current_author)
                elif line.startswith('author '):
                    current_author = line[7:]
                elif line.startswith('author-time '):
                    current_date = line[12:]
                elif line.startswith('committer-time '):
                    pass  # We already have author-time
                elif line.startswith('summary '):
                    pass  # Skip summary
                elif line.startswith('previous '):
                    pass  # Skip previous
                elif line.startswith('filename '):
                    pass  # Skip filename
                elif line.startswith('boundary'):
                    pass  # Skip boundary
                else:
                    # This should be the commit hash and line info
                    parts = line.split()
                    if len(parts) >= 4:
                        current_commit = parts[0]
                        current_line = int(parts[2])
        else:
            # Parse regular format
            for line in lines:
                if line.strip():
                    # Regular format: commit_hash (author date line_number) content
                    parts = line.split('(', 1)
                    if len(parts) >= 2:
                        commit_hash = parts[0].strip()
                        rest = parts[1].split(')', 1)
                        if len(rest) >= 2:
                            info = rest[0]
                            content = rest[1].strip()
                            
                            # Parse author, date, line number
                            info_parts = info.split()
                            if len(info_parts) >= 3:
                                author = info_parts[0]
                                date = info_parts[1]
                                line_num = int(info_parts[2])
                                
                                blame_lines.append({
                                    "line_number": line_num,
                                    "commit": commit_hash,
                                    "author": author,
                                    "date": date,
                                    "content": content
                                })
                                commits.add(commit_hash)
                                authors.add(author)
        
        return {
            "lines": blame_lines,
            "total_lines": len(blame_lines),
            "commits": list(commits),
            "authors": list(authors),
            "total_commits": len(commits),
            "total_authors": len(authors),
            "message": f"Found blame information for {len(blame_lines)} lines"
        } 