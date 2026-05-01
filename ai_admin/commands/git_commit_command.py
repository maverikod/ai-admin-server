from ai_admin.core.custom_exceptions import CustomError
"""Git commit command for committing changes.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitCommitCommand(BaseUnifiedCommand):
    """Commit changes to Git repository.

    This command supports various Git commit operations including:
    - Commit with message
    - Amend commits
    - Sign commits
    - Commit specific files
    - Allow empty commits
    """

    name = "git_commit"

    def __init__(self):
        """Initialize Git commit command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        message: str,
        amend: bool = False,
        sign: bool = False,
        files: Optional[List[str]] = None,
        allow_empty: bool = False,
        no_verify: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        author: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git commit command with unified security.

        Args:
            message: Commit message
            amend: Amend previous commit
            sign: Sign commit
            files: List of files to commit
            allow_empty: Allow empty commit
            no_verify: Skip pre-commit hooks
            verbose: Verbose output
            quiet: Quiet mode
            author: Commit author
            user_roles: List of user roles for security validation

        Returns:
            Success result with commit information
        """
        # Validate inputs
        if not message:
            return ErrorResult(message="Commit message is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            message=message,
            amend=amend,
            sign=sign,
            files=files,
            allow_empty=allow_empty,
            no_verify=no_verify,
            verbose=verbose,
            quiet=quiet,
            author=author,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git commit command."""
        return "git:commit"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git commit command logic."""
        return await self._commit_changes(**kwargs)

    async def _commit_changes(
        self,
        message: str,
        amend: bool = False,
        sign: bool = False,
        files: Optional[List[str]] = None,
        allow_empty: bool = False,
        no_verify: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        author: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Commit changes to Git repository."""
        try:
            # Build Git command
            cmd = ["git", "commit"]

            # Add options
            if amend:
                cmd.append("--amend")
            if sign:
                cmd.append("--sign")
            if allow_empty:
                cmd.append("--allow-empty")
            if no_verify:
                cmd.append("--no-verify")
            if verbose:
                cmd.append("--verbose")
            if quiet:
                cmd.append("--quiet")
            if author:
                cmd.extend(["--author", author])

            # Add message
            cmd.extend(["-m", message])

            # Add files if specified
            if files:
                cmd.extend(files)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Git commit failed: {result.stderr}")

            return {
                "message": f"Successfully committed changes",
                "commit_message": message,
                "amend": amend,
                "sign": sign,
                "files": files,
                "allow_empty": allow_empty,
                "no_verify": no_verify,
                "verbose": verbose,
                "quiet": quiet,
                "author": author,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git commit command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git commit failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git commit command parameters."""
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Commit message",
                },
                "amend": {
                    "type": "boolean",
                    "description": "Amend previous commit",
                    "default": False,
                },
                "sign": {
                    "type": "boolean",
                    "description": "Sign commit",
                    "default": False,
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files to commit",
                },
                "allow_empty": {
                    "type": "boolean",
                    "description": "Allow empty commit",
                    "default": False,
                },
                "no_verify": {
                    "type": "boolean",
                    "description": "Skip pre-commit hooks",
                    "default": False,
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Verbose output",
                    "default": False,
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Quiet mode",
                    "default": False,
                },
                "author": {
                    "type": "string",
                    "description": "Commit author",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["message"],
            "additionalProperties": False,
        }
