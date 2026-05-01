from ai_admin.core.custom_exceptions import CustomError
"""Git pull command for pulling changes from remote repositories.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitPullCommand(BaseUnifiedCommand):
    """Pull changes from remote Git repository.

    This command supports various Git pull operations including:
    - Pull from specific remote and branch
    - Rebase instead of merge
    - Fast-forward only
    - Squash commits
    - Pull with tags
    """

    name = "git_pull"

    def __init__(self):
        """Initialize Git pull command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        rebase: bool = False,
        fast_forward_only: bool = False,
        squash: bool = False,
        tags: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git pull command with unified security.

        Args:
            remote: Remote repository to pull from
            branch: Branch to pull
            rebase: Rebase instead of merge
            fast_forward_only: Fast-forward only
            squash: Squash commits
            tags: Pull tags
            verbose: Verbose mode
            quiet: Quiet mode
            user_roles: List of user roles for security validation

        Returns:
            Success result with pull information
        """
        # Use unified security approach
        return await super().execute(
            remote=remote,
            branch=branch,
            rebase=rebase,
            fast_forward_only=fast_forward_only,
            squash=squash,
            tags=tags,
            verbose=verbose,
            quiet=quiet,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git pull command."""
        return "git:pull"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git pull command logic."""
        return await self._pull(**kwargs)

    async def _pull(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        rebase: bool = False,
        fast_forward_only: bool = False,
        squash: bool = False,
        tags: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Pull changes from remote Git repository."""
        try:
            # Build Git command
            cmd = ["git", "pull"]

            # Add options
            if rebase:
                cmd.append("--rebase")
            if fast_forward_only:
                cmd.append("--ff-only")
            if squash:
                cmd.append("--squash")
            if tags:
                cmd.append("--tags")
            if verbose:
                cmd.append("--verbose")
            if quiet:
                cmd.append("--quiet")

            # Add remote
            cmd.append(remote)

            # Add branch if specified
            if branch:
                cmd.append(branch)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise CustomError(f"Git pull failed: {result.stderr}")

            return {
                "message": f"Git pull completed successfully",
                    "remote": remote,
                    "branch": branch,
                    "rebase": rebase,
                    "fast_forward_only": fast_forward_only,
                    "squash": squash,
                    "tags": tags,
                "verbose": verbose,
                "quiet": quiet,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git pull command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git pull failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git pull command parameters."""
        return {
            "type": "object",
            "properties": {
                "remote": {
                    "type": "string",
                    "description": "Remote repository to pull from",
                    "default": "origin",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch to pull",
                },
                "rebase": {
                    "type": "boolean",
                    "description": "Rebase instead of merge",
                    "default": False,
                },
                "fast_forward_only": {
                    "type": "boolean",
                    "description": "Fast-forward only",
                    "default": False,
                },
                "squash": {
                    "type": "boolean",
                    "description": "Squash commits",
                    "default": False,
                },
                "tags": {
                    "type": "boolean",
                    "description": "Pull tags",
                    "default": False,
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Verbose mode",
                    "default": False,
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Quiet mode",
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
