from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Git blame command for showing file blame information.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitBlameCommand(BaseUnifiedCommand):
    """Show Git blame information for files.

    This command supports various Git blame operations including:
    - Show blame for entire files
    - Show blame for specific lines
    - Show blame for specific commits
    - Show blame with different formats
    - Show blame with line numbers
    - Show blame with file names
    """

    name = "git_blame"

    def __init__(self):
        """Initialize Git blame command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
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
        show_filename: bool = False,
        show_linenumber: bool = True,
        show_rev: bool = True,
        show_summary: bool = False,
        show_progress: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git blame command with unified security.

        Args:
            file_path: Path to the file to blame
            commit: Specific commit to blame
            start_line: Start line number
            end_line: End line number
            line_number: Show line numbers
            show_name: Show author names
            show_email: Show author emails
            show_date: Show commit dates
            show_time: Show commit times
            show_timezone: Show timezones
            show_filename: Show filenames
            show_linenumber: Show line numbers
            show_rev: Show revision numbers
            show_summary: Show summary
            show_progress: Show progress
            user_roles: List of user roles for security validation

        Returns:
            Success result with blame information
        """
        # Validate inputs
        if not file_path:
            return ErrorResult(message="File path is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            file_path=file_path,
            commit=commit,
            start_line=start_line,
            end_line=end_line,
            line_number=line_number,
            show_name=show_name,
            show_email=show_email,
            show_date=show_date,
            show_time=show_time,
            show_timezone=show_timezone,
            show_filename=show_filename,
            show_linenumber=show_linenumber,
            show_rev=show_rev,
            show_summary=show_summary,
            show_progress=show_progress,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git blame command."""
        return "git:blame"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git blame command logic."""
        return await self._blame_file(**kwargs)

    async def _blame_file(
        self,
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
        show_filename: bool = False,
        show_linenumber: bool = True,
        show_rev: bool = True,
        show_summary: bool = False,
        show_progress: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Show Git blame information for file."""
        try:
            # Build Git command
            cmd = ["git", "blame"]

            # Add options
            if not line_number:
                cmd.append("--no-line-number")
            if not show_name:
                cmd.append("--no-name")
            if not show_email:
                cmd.append("--no-email")
            if not show_date:
                cmd.append("--no-date")
            if show_time:
                cmd.append("--show-time")
            if show_timezone:
                cmd.append("--show-timezone")
            if show_filename:
                cmd.append("--show-filename")
            if not show_linenumber:
                cmd.append("--no-linenumber")
            if not show_rev:
                cmd.append("--no-rev")
            if show_summary:
                cmd.append("--show-summary")
            if show_progress:
                cmd.append("--show-progress")

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

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Git blame failed: {result.stderr}")

            return {
                "message": f"Git blame completed for '{file_path}'",
                "file_path": file_path,
                "commit": commit,
                "start_line": start_line,
                "end_line": end_line,
                "line_number": line_number,
                "show_name": show_name,
                "show_email": show_email,
                "show_date": show_date,
                "show_time": show_time,
                "show_timezone": show_timezone,
                "show_filename": show_filename,
                "show_linenumber": show_linenumber,
                "show_rev": show_rev,
                "show_summary": show_summary,
                "show_progress": show_progress,
                "blame_output": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git blame command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git blame failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git blame command parameters."""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to blame",
                },
                "commit": {
                    "type": "string",
                    "description": "Specific commit to blame",
                },
                "start_line": {
                    "type": "integer",
                    "description": "Start line number",
                },
                "end_line": {
                    "type": "integer",
                    "description": "End line number",
                },
                "line_number": {
                    "type": "boolean",
                    "description": "Show line numbers",
                    "default": True,
                },
                "show_name": {
                    "type": "boolean",
                    "description": "Show author names",
                    "default": True,
                },
                "show_email": {
                    "type": "boolean",
                    "description": "Show author emails",
                    "default": True,
                },
                "show_date": {
                    "type": "boolean",
                    "description": "Show commit dates",
                    "default": True,
                },
                "show_time": {
                    "type": "boolean",
                    "description": "Show commit times",
                    "default": False,
                },
                "show_timezone": {
                    "type": "boolean",
                    "description": "Show timezones",
                    "default": False,
                },
                "show_filename": {
                    "type": "boolean",
                    "description": "Show filenames",
                    "default": False,
                },
                "show_linenumber": {
                    "type": "boolean",
                    "description": "Show line numbers",
                    "default": True,
                },
                "show_rev": {
                    "type": "boolean",
                    "description": "Show revision numbers",
                    "default": True,
                },
                "show_summary": {
                    "type": "boolean",
                    "description": "Show summary",
                    "default": False,
                },
                "show_progress": {
                    "type": "boolean",
                    "description": "Show progress",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["file_path"],
            "additionalProperties": False,
        }
