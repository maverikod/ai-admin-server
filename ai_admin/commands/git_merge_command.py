from ai_admin.core.custom_exceptions import CustomError
"""Git merge command for merging branches.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitMergeCommand(BaseUnifiedCommand):
    """Merge Git branches.

    This command supports various Git merge operations including:
    - Fast-forward merge
    - No-fast-forward merge
    - Squash merge
    - Merge specific commits
    - Abort merge
    - Continue merge
    """

    name = "git_merge"

    def __init__(self):
        """Initialize Git merge command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        commit: Optional[str] = None,
        no_ff: bool = False,
        squash: bool = False,
        abort: bool = False,
        continue_merge: bool = False,
        message: Optional[str] = None,
        quiet: bool = False,
        verbose: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git merge command with unified security.

        Args:
            commit: Commit or branch to merge
            no_ff: No fast-forward merge
            squash: Squash merge
            abort: Abort merge
            continue_merge: Continue merge
            message: Merge commit message
            quiet: Quiet mode
            verbose: Verbose mode
            user_roles: List of user roles for security validation

        Returns:
            Success result with merge information
        """
        # Use unified security approach
        return await super().execute(
            commit=commit,
            no_ff=no_ff,
            squash=squash,
            abort=abort,
            continue_merge=continue_merge,
            message=message,
            quiet=quiet,
            verbose=verbose,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git merge command."""
        return "git:merge"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git merge command logic."""
        return await self._merge(**kwargs)

    async def _merge(
        self,
        commit: Optional[str] = None,
        no_ff: bool = False,
        squash: bool = False,
        abort: bool = False,
        continue_merge: bool = False,
        message: Optional[str] = None,
        quiet: bool = False,
        verbose: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Merge Git branches."""
        try:
            # Build Git command
            cmd = ["git", "merge"]

            # Add options
            if no_ff:
                cmd.append("--no-ff")
            if squash:
                cmd.append("--squash")
            if abort:
                cmd.append("--abort")
            if continue_merge:
                cmd.append("--continue")
            if message:
                cmd.extend(["-m", message])
            if quiet:
                cmd.append("--quiet")
            if verbose:
                cmd.append("--verbose")

            # Add commit if specified
            if commit:
                cmd.append(commit)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise CustomError(f"Git merge failed: {result.stderr}")

            return {
                "message": f"Git merge completed successfully",
                    "commit": commit,
                "no_ff": no_ff,
                    "squash": squash,
                    "abort": abort,
                    "continue_merge": continue_merge,
                "message": message,
                "quiet": quiet,
                "verbose": verbose,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git merge command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git merge failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git merge command parameters."""
        return {
            "type": "object",
            "properties": {
                "commit": {
                    "type": "string",
                    "description": "Commit or branch to merge",
                },
                "no_ff": {
                    "type": "boolean",
                    "description": "No fast-forward merge",
                    "default": False,
                },
                "squash": {
                    "type": "boolean",
                    "description": "Squash merge",
                    "default": False,
                },
                "abort": {
                    "type": "boolean",
                    "description": "Abort merge",
                    "default": False,
                },
                "continue_merge": {
                    "type": "boolean",
                    "description": "Continue merge",
                    "default": False,
                },
                "message": {
                    "type": "string",
                    "description": "Merge commit message",
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Quiet mode",
                    "default": False,
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Verbose mode",
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
