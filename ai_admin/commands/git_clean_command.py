from ai_admin.core.custom_exceptions import CustomError
"""Git clean command for removing untracked files.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitCleanCommand(BaseUnifiedCommand):
    """Remove untracked files from Git repository.

    This command supports various Git clean operations including:
    - Remove untracked files
    - Remove untracked directories
    - Dry run mode
    - Force removal
    - Interactive mode
    - Remove ignored files
    """

    name = "git_clean"

    def __init__(self):
        """Initialize Git clean command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        force: bool = False,
        dry_run: bool = False,
        directories: bool = False,
        ignored: bool = False,
        interactive: bool = False,
        quiet: bool = False,
        paths: Optional[List[str]] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git clean command with unified security.

        Args:
            force: Force removal
            dry_run: Dry run mode
            directories: Remove directories
            ignored: Remove ignored files
            interactive: Interactive mode
            quiet: Quiet mode
            paths: Specific paths to clean
            user_roles: List of user roles for security validation

        Returns:
            Success result with clean information
        """
        # Use unified security approach
        return await super().execute(
            force=force,
            dry_run=dry_run,
            directories=directories,
            ignored=ignored,
            interactive=interactive,
            quiet=quiet,
            paths=paths,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git clean command."""
        return "git:clean"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git clean command logic."""
        return await self._clean(**kwargs)

    async def _clean(
        self,
        force: bool = False,
        dry_run: bool = False,
        directories: bool = False,
        ignored: bool = False,
        interactive: bool = False,
        quiet: bool = False,
        paths: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Clean Git repository."""
        try:
            # Build Git command
            cmd = ["git", "clean"]

            # Add options
            if force:
                cmd.append("--force")
            if dry_run:
                cmd.append("--dry-run")
            if directories:
                cmd.append("-d")
            if ignored:
                cmd.append("-x")
            if interactive:
                cmd.append("--interactive")
            if quiet:
                cmd.append("--quiet")

            # Add paths if specified
            if paths:
                cmd.extend(paths)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Git clean failed: {result.stderr}")

            return {
                "message": f"Git clean completed successfully",
                "force": force,
                "dry_run": dry_run,
                "directories": directories,
                "ignored": ignored,
                "interactive": interactive,
                "quiet": quiet,
                "paths": paths,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git clean command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git clean failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git clean command parameters."""
        return {
            "type": "object",
            "properties": {
                "force": {
                    "type": "boolean",
                    "description": "Force removal",
                    "default": False,
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Dry run mode",
                    "default": False,
                },
                "directories": {
                    "type": "boolean",
                    "description": "Remove directories",
                    "default": False,
                },
                "ignored": {
                    "type": "boolean",
                    "description": "Remove ignored files",
                    "default": False,
                },
                "interactive": {
                    "type": "boolean",
                    "description": "Interactive mode",
                    "default": False,
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Quiet mode",
                    "default": False,
                },
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific paths to clean",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
