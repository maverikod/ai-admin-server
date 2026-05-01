from ai_admin.core.custom_exceptions import CustomError
"""Git rebase command for rebasing commits.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitRebaseCommand(BaseUnifiedCommand):
    """Rebase Git commits.

    This command supports various Git rebase operations including:
    - Interactive rebase
    - Continue/abort/skip rebase
    - Rebase onto specific branch
    - Preserve merges
    - Squash commits
    """

    name = "git_rebase"

    def __init__(self):
        """Initialize Git rebase command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        action: str = "start",
        base: Optional[str] = None,
        branch: Optional[str] = None,
        interactive: bool = False,
        preserve_merges: bool = False,
        squash: bool = False,
        continue_rebase: bool = False,
        abort: bool = False,
        skip: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git rebase command with unified security.

        Args:
            action: Rebase action (start, continue, abort, skip)
            base: Base branch to rebase onto
            branch: Branch to rebase
            interactive: Interactive rebase
            preserve_merges: Preserve merges
            squash: Squash commits
            continue_rebase: Continue rebase
            abort: Abort rebase
            skip: Skip commit
            user_roles: List of user roles for security validation

        Returns:
            Success result with rebase information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            base=base,
            branch=branch,
            interactive=interactive,
            preserve_merges=preserve_merges,
            squash=squash,
            continue_rebase=continue_rebase,
            abort=abort,
            skip=skip,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git rebase command."""
        return "git:rebase"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git rebase command logic."""
        return await self._rebase(**kwargs)

    async def _rebase(
        self,
        action: str = "start",
        base: Optional[str] = None,
        branch: Optional[str] = None,
        interactive: bool = False,
        preserve_merges: bool = False,
        squash: bool = False,
        continue_rebase: bool = False,
        abort: bool = False,
        skip: bool = False,
        auto_stash: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Rebase Git commits."""
        try:
            # Check for uncommitted changes and stash if needed
            stash_created = False
            if action == "start" and auto_stash:
                stash_result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if stash_result.returncode == 0 and stash_result.stdout.strip():
                    # There are uncommitted changes, create stash
                    stash_cmd = subprocess.run(
                        ["git", "stash", "push", "-m", "Auto-stash before rebase"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if stash_cmd.returncode == 0:
                        stash_created = True
                        logger.info("Auto-stashed uncommitted changes before rebase")
                    else:
                        logger.warning(f"Failed to auto-stash: {stash_cmd.stderr}")

            # Build Git command
            cmd = ["git", "rebase"]

            # Add options
            if interactive:
                cmd.append("--interactive")
            if preserve_merges:
                cmd.append("--preserve-merges")
            if squash:
                cmd.append("--squash")
            if continue_rebase:
                cmd.append("--continue")
            if abort:
                cmd.append("--abort")
            if skip:
                cmd.append("--skip")

            # Add base and branch for start action
            if action == "start" and base:
                cmd.append(base)
                if branch:
                    cmd.append(branch)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                # If rebase failed and we created a stash, restore it
                if stash_created:
                    restore_result = subprocess.run(
                        ["git", "stash", "pop"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if restore_result.returncode == 0:
                        logger.info("Restored auto-stashed changes after failed rebase")
                raise CustomError(f"Git rebase failed: {result.stderr}")

            # If rebase succeeded and we created a stash, restore it
            if stash_created:
                restore_result = subprocess.run(
                    ["git", "stash", "pop"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if restore_result.returncode == 0:
                    logger.info("Restored auto-stashed changes after successful rebase")
                else:
                    logger.warning(f"Failed to restore auto-stash: {restore_result.stderr}")

            return {
                "message": f"Git rebase {action} completed successfully",
                "action": action,
                "base": base,
                "branch": branch,
                "interactive": interactive,
                "preserve_merges": preserve_merges,
                "squash": squash,
                "continue_rebase": continue_rebase,
                "abort": abort,
                "skip": skip,
                "auto_stash": auto_stash,
                "stash_created": stash_created,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git rebase command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git rebase failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git rebase command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Rebase action (start, continue, abort, skip)",
                    "default": "start",
                    "enum": ["start", "continue", "abort", "skip"],
                },
                "base": {
                    "type": "string",
                    "description": "Base branch to rebase onto",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch to rebase",
                },
                "interactive": {
                    "type": "boolean",
                    "description": "Interactive rebase",
                    "default": False,
                },
                "preserve_merges": {
                    "type": "boolean",
                    "description": "Preserve merges",
                    "default": False,
                },
                "squash": {
                    "type": "boolean",
                    "description": "Squash commits",
                    "default": False,
                },
                "continue_rebase": {
                    "type": "boolean",
                    "description": "Continue rebase",
                    "default": False,
                },
                "abort": {
                    "type": "boolean",
                    "description": "Abort rebase",
                    "default": False,
                },
                "skip": {
                    "type": "boolean",
                    "description": "Skip commit",
                    "default": False,
                },
                "auto_stash": {
                    "type": "boolean",
                    "description": "Automatically stash uncommitted changes before rebase",
                    "default": True,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
