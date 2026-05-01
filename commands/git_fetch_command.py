from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Git fetch command for fetching from remote repositories.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitFetchCommand(BaseUnifiedCommand):
    """Fetch changes from remote Git repositories.

    This command supports various Git fetch operations including:
    - Fetch from specific remote
    - Fetch specific branches
    - Fetch all remotes
    - Fetch tags
    - Prune remote-tracking branches
    - Deepen history
    """

    name = "git_fetch"

    def __init__(self):
        """Initialize Git fetch command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        remote: Optional[str] = None,
        branch: Optional[str] = None,
        all_remotes: bool = False,
        tags: bool = False,
        prune: bool = False,
        prune_tags: bool = False,
        depth: Optional[int] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git fetch command with unified security.

        Args:
            remote: Remote repository to fetch from
            branch: Branch to fetch
            all_remotes: Fetch from all remotes
            tags: Fetch tags
            prune: Prune remote-tracking branches
            prune_tags: Prune tags
            depth: Shallow fetch depth
            user_roles: List of user roles for security validation

        Returns:
            Success result with fetch information
        """
        # Use unified security approach
        return await super().execute(
            remote=remote,
            branch=branch,
            all_remotes=all_remotes,
            tags=tags,
            prune=prune,
            prune_tags=prune_tags,
            depth=depth,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git fetch command."""
        return "git:fetch"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git fetch command logic."""
        return await self._fetch(**kwargs)

    async def _fetch(
        self,
        remote: Optional[str] = None,
        branch: Optional[str] = None,
        all_remotes: bool = False,
        tags: bool = False,
        prune: bool = False,
        prune_tags: bool = False,
        depth: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Fetch from remote Git repository."""
        try:
            # Build Git command
            cmd = ["git", "fetch"]

            # Add options
            if all_remotes:
                cmd.append("--all")
            if tags:
                cmd.append("--tags")
            if prune:
                cmd.append("--prune")
            if prune_tags:
                cmd.append("--prune-tags")
            if depth:
                cmd.extend(["--depth", str(depth)])

            # Add remote if specified
            if remote:
                cmd.append(remote)

            # Add branch if specified
            if branch:
                cmd.append(branch)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise CustomError(f"Git fetch failed: {result.stderr}")

            return {
                "message": f"Git fetch completed successfully",
                "remote": remote,
                "branch": branch,
                "all_remotes": all_remotes,
                "tags": tags,
                "prune": prune,
                "prune_tags": prune_tags,
                "depth": depth,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git fetch command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git fetch failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git fetch command parameters."""
        return {
            "type": "object",
            "properties": {
                "remote": {
                    "type": "string",
                    "description": "Remote repository to fetch from",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch to fetch",
                },
                "all_remotes": {
                    "type": "boolean",
                    "description": "Fetch from all remotes",
                    "default": False,
                },
                "tags": {
                    "type": "boolean",
                    "description": "Fetch tags",
                    "default": False,
                },
                "prune": {
                    "type": "boolean",
                    "description": "Prune remote-tracking branches",
                    "default": False,
                },
                "prune_tags": {
                    "type": "boolean",
                    "description": "Prune tags",
                    "default": False,
                },
                "depth": {
                    "type": "integer",
                    "description": "Shallow fetch depth",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
