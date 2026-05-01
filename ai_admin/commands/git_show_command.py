from ai_admin.core.custom_exceptions import CustomError
"""Git show command for showing Git objects.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitShowCommand(BaseUnifiedCommand):
    """Show Git objects.

    This command supports various Git show operations including:
    - Show commit information
    - Show file contents
    - Show tree contents
    - Show tag information
    - Show diff for commits
    - Show statistics
    """

    name = "git_show"

    def __init__(self):
        """Initialize Git show command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        object_name: str = "HEAD",
        files: Optional[List[str]] = None,
        stat: bool = False,
        name_only: bool = False,
        name_status: bool = False,
        pretty: Optional[str] = None,
        format: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git show command with unified security.

        Args:
            object_name: Git object to show
            files: List of files to show
            stat: Show statistics
            name_only: Show file names only
            name_status: Show name and status
            pretty: Pretty format
            format: Custom format
            user_roles: List of user roles for security validation

        Returns:
            Success result with show information
        """
        # Use unified security approach
        return await super().execute(
            object_name=object_name,
            files=files,
            stat=stat,
            name_only=name_only,
            name_status=name_status,
            pretty=pretty,
            format=format,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git show command."""
        return "git:show"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git show command logic."""
        return await self._show(**kwargs)

    async def _show(
        self,
        object_name: str = "HEAD",
        files: Optional[List[str]] = None,
        stat: bool = False,
        name_only: bool = False,
        name_status: bool = False,
        pretty: Optional[str] = None,
        format: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Show Git object."""
        try:
            # Build Git command
            cmd = ["git", "show"]

            # Add options
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

            # Add object name
            cmd.append(object_name)

            # Add files if specified
            if files:
                cmd.extend(files)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Git show failed: {result.stderr}")

            return {
                "message": f"Git show completed for '{object_name}'",
                "object_name": object_name,
                "files": files,
                "stat": stat,
                "name_only": name_only,
                "name_status": name_status,
                "pretty": pretty,
                "format": format,
                "content": result.stdout,
                "raw_output": result.stdout,
                    "command": " ".join(cmd),
                }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git show command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git show failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git show command parameters."""
        return {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Git object to show",
                    "default": "HEAD",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files to show",
                },
                "stat": {
                    "type": "boolean",
                    "description": "Show statistics",
                    "default": False,
                },
                "name_only": {
                    "type": "boolean",
                    "description": "Show file names only",
                    "default": False,
                },
                "name_status": {
                    "type": "boolean",
                    "description": "Show name and status",
                    "default": False,
                },
                "pretty": {
                    "type": "string",
                    "description": "Pretty format",
                },
                "format": {
                    "type": "string",
                    "description": "Custom format",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
