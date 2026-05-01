from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Git push command for pushing changes to remote repositories.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitPushCommand(BaseUnifiedCommand):
    """Push changes to remote Git repository.

    This command supports various Git push operations including:
    - Push to specific remote and branch
    - Force push
    - Push all branches
    - Push tags
    - Set upstream
    """

    name = "git_push"

    def __init__(self):
        """Initialize Git push command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        force_with_lease: bool = False,
        all_branches: bool = False,
        tags: bool = False,
        set_upstream: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git push command with unified security.

        Args:
            remote: Remote repository to push to
            branch: Branch to push
            force: Force push
            force_with_lease: Force push with lease
            all_branches: Push all branches
            tags: Push tags
            set_upstream: Set upstream
            verbose: Verbose mode
            quiet: Quiet mode
            user_roles: List of user roles for security validation

        Returns:
            Success result with push information
        """
        # Use unified security approach
        return await super().execute(
            remote=remote,
            branch=branch,
            force=force,
            force_with_lease=force_with_lease,
            all_branches=all_branches,
            tags=tags,
            set_upstream=set_upstream,
            verbose=verbose,
            quiet=quiet,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git push command."""
        return "git:push"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git push command logic."""
        return await self._push(**kwargs)

    async def _push(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        force_with_lease: bool = False,
        all_branches: bool = False,
        tags: bool = False,
        set_upstream: bool = False,
        verbose: bool = False,
        quiet: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Push changes to remote Git repository."""
        try:
            # Build Git command
            cmd = ["git", "push"]

            # Add options
            if force:
                cmd.append("--force")
            if force_with_lease:
                cmd.append("--force-with-lease")
            if all_branches:
                cmd.append("--all")
            if tags:
                cmd.append("--tags")
            if set_upstream:
                cmd.append("--set-upstream")
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
                raise CustomError(f"Git push failed: {result.stderr}")

            return {
                "message": f"Git push completed successfully",
                    "remote": remote,
                    "branch": branch,
                    "force": force,
                    "force_with_lease": force_with_lease,
                    "all_branches": all_branches,
                    "tags": tags,
                "set_upstream": set_upstream,
                "verbose": verbose,
                "quiet": quiet,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git push command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git push failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git push command parameters."""
        return {
            "type": "object",
            "properties": {
                "remote": {
                    "type": "string",
                    "description": "Remote repository to push to",
                    "default": "origin",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch to push",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force push",
                    "default": False,
                },
                "force_with_lease": {
                    "type": "boolean",
                    "description": "Force push with lease",
                    "default": False,
                },
                "all_branches": {
                    "type": "boolean",
                    "description": "Push all branches",
                    "default": False,
                },
                "tags": {
                    "type": "boolean",
                    "description": "Push tags",
                    "default": False,
                },
                "set_upstream": {
                    "type": "boolean",
                    "description": "Set upstream",
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
