from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Git add command for staging files.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult, CommandResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitAddCommand(BaseUnifiedCommand):
    """Add files to Git staging area.

    This command supports various Git add operations including:
    - Adding specific files
    - Adding all files
    - Interactive adding
    - Patch mode
    - Force adding
    """

    name = "git_add"

    def __init__(self):
        """Initialize Git add command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(self, **kwargs: Any) -> CommandResult:
        """Execute Git add command with unified security.

        Args:
            files: List of files to add
            all_files: Add all files
            interactive: Interactive mode
            patch: Patch mode
            force: Force adding
            verbose: Verbose output
            dry_run: Dry run mode
            ignore_errors: Ignore errors
            user_roles: List of user roles for security validation

        Returns:
            Success result with add information
        """
        # Extract parameters from kwargs
        files = kwargs.get("files")
        all_files = kwargs.get("all_files", False)
        interactive = kwargs.get("interactive", False)
        patch = kwargs.get("patch", False)
        force = kwargs.get("force", False)
        verbose = kwargs.get("verbose", False)
        dry_run = kwargs.get("dry_run", False)
        ignore_errors = kwargs.get("ignore_errors", False)
        user_roles = kwargs.get("user_roles")

        # Use unified security approach
        return await super().execute(
            all_files=all_files,
            interactive=interactive,
            patch=patch,
            force=force,
            verbose=verbose,
            dry_run=dry_run,
            ignore_errors=ignore_errors,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git add command."""
        return "git:add"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git add command logic."""
        return await self._add_files(**kwargs)

    async def _add_files(
        self,
        files: Optional[List[str]] = None,
        all_files: bool = False,
        interactive: bool = False,
        patch: bool = False,
        force: bool = False,
        verbose: bool = False,
        dry_run: bool = False,
        ignore_errors: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Add files to Git staging area."""
        try:
            # Build Git command
            cmd = ["git", "add"]

            # Add options
            if all_files:
                cmd.append("--all")
            elif interactive:
                cmd.append("--interactive")
            elif patch:
                cmd.append("--patch")
            elif force:
                cmd.append("--force")
            elif verbose:
                cmd.append("--verbose")
            elif dry_run:
                cmd.append("--dry-run")
            elif ignore_errors:
                cmd.append("--ignore-errors")

            # Add files
            if files:
                cmd.extend(files)
            elif not all_files and not interactive and not patch:
                cmd.append(".")

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0 and not ignore_errors:
                raise CustomError(f"Git add failed: {result.stderr}")

            return {
                "message": f"Git add completed successfully",
                "files": files,
                "all_files": all_files,
                "interactive": interactive,
                "patch": patch,
                "force": force,
                "verbose": verbose,
                "dry_run": dry_run,
                "ignore_errors": ignore_errors,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git add command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git add failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git add command parameters."""
        return {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files to add",
                },
                "all_files": {
                    "type": "boolean",
                    "description": "Add all files",
                    "default": False,
                },
                "interactive": {
                    "type": "boolean",
                    "description": "Interactive mode",
                    "default": False,
                },
                "patch": {
                    "type": "boolean",
                    "description": "Patch mode",
                    "default": False,
                },
                "force": {
                    "type": "boolean",
                    "description": "Force adding",
                    "default": False,
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Verbose output",
                    "default": False,
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Dry run mode",
                    "default": False,
                },
                "ignore_errors": {
                    "type": "boolean",
                    "description": "Ignore errors",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
