from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Git cherry-pick command for applying commits.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitCherryPickCommand(BaseUnifiedCommand):
    """Cherry-pick Git commits.

    This command supports various Git cherry-pick operations including:
    - Cherry-pick single commit
    - Cherry-pick multiple commits
    - Continue cherry-pick after conflicts
    - Abort cherry-pick
    - Skip commit
    - Edit commit message
    - Sign commits
    """

    name = "git_cherry_pick"

    def __init__(self):
        """Initialize Git cherry-pick command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        commits: List[str],
        continue_pick: bool = False,
        abort: bool = False,
        skip: bool = False,
        edit: bool = False,
        signoff: bool = False,
        sign: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git cherry-pick command with unified security.

        Args:
            commits: List of commits to cherry-pick
            continue_pick: Continue cherry-pick after conflicts
            abort: Abort cherry-pick
            skip: Skip commit
            edit: Edit commit message
            signoff: Add signoff
            sign: Sign commit
            user_roles: List of user roles for security validation

        Returns:
            Success result with cherry-pick information
        """
        # Validate inputs
        if not commits and not continue_pick and not abort and not skip:
            return ErrorResult(message="Commits or action is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            commits=commits,
            continue_pick=continue_pick,
            abort=abort,
            skip=skip,
            edit=edit,
            signoff=signoff,
            sign=sign,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git cherry-pick command."""
        return "git:cherry_pick"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git cherry-pick command logic."""
        return await self._cherry_pick(**kwargs)

    async def _cherry_pick(
        self,
        commits: List[str],
        continue_pick: bool = False,
        abort: bool = False,
        skip: bool = False,
        edit: bool = False,
        signoff: bool = False,
        sign: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Cherry-pick Git commits."""
        try:
            # Build Git command
            cmd = ["git", "cherry-pick"]

            # Add options
            if continue_pick:
                cmd.append("--continue")
            elif abort:
                cmd.append("--abort")
            elif skip:
                cmd.append("--skip")
            else:
                if edit:
                    cmd.append("--edit")
                if signoff:
                    cmd.append("--signoff")
                if sign:
                    cmd.append("--sign")

                # Add commits
                cmd.extend(commits)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise CustomError(f"Git cherry-pick failed: {result.stderr}")

            return {
                "message": f"Cherry-pick completed successfully",
                "commits": commits,
                "continue_pick": continue_pick,
                "abort": abort,
                "skip": skip,
                "edit": edit,
                "signoff": signoff,
                "sign": sign,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git cherry-pick command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git cherry-pick failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git cherry-pick command parameters."""
        return {
            "type": "object",
            "properties": {
                "commits": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of commits to cherry-pick",
                },
                "continue_pick": {
                    "type": "boolean",
                    "description": "Continue cherry-pick after conflicts",
                    "default": False,
                },
                "abort": {
                    "type": "boolean",
                    "description": "Abort cherry-pick",
                    "default": False,
                },
                "skip": {
                    "type": "boolean",
                    "description": "Skip commit",
                    "default": False,
                },
                "edit": {
                    "type": "boolean",
                    "description": "Edit commit message",
                    "default": False,
                },
                "signoff": {
                    "type": "boolean",
                    "description": "Add signoff",
                    "default": False,
                },
                "sign": {
                    "type": "boolean",
                    "description": "Sign commit",
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
