"""Git show command for viewing commit and object information."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitShowCommand(Command):
    """Show Git objects and commit information.
    
    This command supports:
    - Show commit information
    - Show file contents
    - Show tree contents
    - Show tag information
    - Show diff for commits
    - Show statistics
    """
    
    name = "git_show"
    
    async def execute(
        self,
        current_directory: str,
        object_name: str = "HEAD",
        files: Optional[List[str]] = None,
        stat: bool = False,
        name_only: bool = False,
        name_status: bool = False,
        pretty: Optional[str] = None,
        format: Optional[str] = None,
        no_color: bool = False,
        color: bool = False,
        quiet: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Show Git object information.
        
        Args:
            current_directory: Current working directory where to execute git commands
            object_name: Git object to show (commit, tree, blob, tag)
            files: Specific files to show (optional)
            stat: Show diffstat
            name_only: Show only names of changed files
            name_status: Show name and status of changed files
            pretty: Pretty format (short, medium, full, fuller, email, raw, format)
            format: Custom format string
            no_color: Disable color output
            color: Force color output
            quiet: Suppress output
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
            
            # Build git show command
            cmd = ["git", "show"]
            
            if stat:
                cmd.append("--stat")
            
            if name_only:
                cmd.append("--name-only")
            
            if name_status:
                cmd.append("--name-status")
            
            if pretty:
                cmd.extend(["--pretty", pretty])
            
            if format:
                cmd.extend(["--format", format])
            
            if no_color:
                cmd.append("--no-color")
            
            if color:
                cmd.append("--color")
            
            if quiet:
                cmd.append("--quiet")
            
            # Add object name
            cmd.append(object_name)
            
            # Add specific files if provided
            if files:
                cmd.extend(files)
            
            # Execute git show
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git show failed: {result.stderr}",
                    code="GIT_SHOW_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Parse show output
            show_info = await self._parse_show_output(result.stdout, object_name)
            
            return SuccessResult(data={
                "message": f"Successfully showed information for {object_name}",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "object_name": object_name,
                "show_info": show_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git show: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _parse_show_output(self, output: str, object_name: str) -> Dict[str, Any]:
        """Parse git show output into structured data."""
        if not output.strip():
            return {"content": "", "type": "unknown"}
        
        lines = output.strip().split('\n')
        
        # Try to determine object type and parse accordingly
        if object_name.startswith('HEAD') or len(object_name) == 40:
            # Likely a commit
            return await self._parse_commit_output(lines)
        elif object_name.startswith('refs/tags/'):
            # Likely a tag
            return await self._parse_tag_output(lines)
        else:
            # Generic content
            return {
                "content": output,
                "type": "generic",
                "lines": len(lines)
            }
    
    async def _parse_commit_output(self, lines: List[str]) -> Dict[str, Any]:
        """Parse commit show output."""
        commit_info = {
            "type": "commit",
            "hash": "",
            "author": "",
            "date": "",
            "message": "",
            "diff": "",
            "files_changed": []
        }
        
        in_message = False
        in_diff = False
        message_lines = []
        diff_lines = []
        
        for line in lines:
            if line.startswith('commit '):
                commit_info["hash"] = line[7:]
            elif line.startswith('Author: '):
                commit_info["author"] = line[8:]
            elif line.startswith('Date: '):
                commit_info["date"] = line[6:]
            elif line.startswith('diff --git'):
                in_diff = True
                in_message = False
                diff_lines.append(line)
            elif in_diff:
                diff_lines.append(line)
            elif line.startswith(' ') and not in_message:
                # Start of commit message
                in_message = True
                message_lines.append(line.strip())
            elif in_message and line.startswith(' '):
                message_lines.append(line.strip())
            elif in_message and not line.startswith(' '):
                # End of message
                in_message = False
        
        commit_info["message"] = '\n'.join(message_lines)
        commit_info["diff"] = '\n'.join(diff_lines)
        
        # Extract files changed from diff
        for line in diff_lines:
            if line.startswith('diff --git a/') and ' b/' in line:
                file_path = line.split(' b/')[1]
                commit_info["files_changed"].append(file_path)
        
        return commit_info
    
    async def _parse_tag_output(self, lines: List[str]) -> Dict[str, Any]:
        """Parse tag show output."""
        tag_info = {
            "type": "tag",
            "tag": "",
            "object": "",
            "tagger": "",
            "message": "",
            "content": ""
        }
        
        in_message = False
        message_lines = []
        
        for line in lines:
            if line.startswith('tag '):
                tag_info["tag"] = line[4:]
            elif line.startswith('object '):
                tag_info["object"] = line[7:]
            elif line.startswith('tagger '):
                tag_info["tagger"] = line[7:]
            elif line.startswith(' ') and not in_message:
                # Start of tag message
                in_message = True
                message_lines.append(line.strip())
            elif in_message and line.startswith(' '):
                message_lines.append(line.strip())
            elif in_message and not line.startswith(' '):
                # End of message
                in_message = False
        
        tag_info["message"] = '\n'.join(message_lines)
        tag_info["content"] = '\n'.join(lines)
        
        return tag_info 