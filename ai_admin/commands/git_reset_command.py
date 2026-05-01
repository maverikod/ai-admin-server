from ai_admin.core.custom_exceptions import CustomError
"""Git reset command for resetting repository state.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitResetCommand(BaseUnifiedCommand):
    """Reset Git repository state.

    This command supports various Git reset operations including:
    - Soft reset (keep changes in staging area)
    - Mixed reset (default, keep changes in working directory)
    - Hard reset (discard all changes)
    - Reset specific files
    - Reset to specific commit
    """

    name = "git_reset"

    def __init__(self):
        """Initialize Git reset command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        commit: str = "HEAD",
        mode: str = "mixed",
        files: Optional[List[str]] = None,
        quiet: bool = False,
        verbose: bool = False,
        repository_path: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git reset command with unified security.

        Args:
            commit: Commit to reset to
            mode: Reset mode (soft, mixed, hard)
            files: List of files to reset
            quiet: Quiet mode
            verbose: Verbose mode
            repository_path: Path to repository
            user_roles: List of user roles for security validation

        Returns:
            Success result with reset information
        """
        # Use unified security approach
        return await super().execute(
            commit=commit,
            mode=mode,
            files=files,
            quiet=quiet,
            verbose=verbose,
            repository_path=repository_path,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git reset command."""
        return "git:reset"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git reset command logic."""
        return await self._reset(**kwargs)

    async def _reset(
        self,
        commit: str = "HEAD",
        mode: str = "mixed",
        files: Optional[List[str]] = None,
        quiet: bool = False,
        verbose: bool = False,
        repository_path: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Reset Git repository state."""
        try:
            # Build Git command
            cmd = ["git", "reset"]

            # Add mode
            if mode == "soft":
                cmd.append("--soft")
            elif mode == "mixed":
                cmd.append("--mixed")
            elif mode == "hard":
                cmd.append("--hard")

            # Add options
            if quiet:
                cmd.append("--quiet")
            if verbose:
                cmd.append("--verbose")

            # Add commit
            cmd.append(commit)

            # Add files if specified
            if files:
                cmd.extend(files)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Git reset failed: {result.stderr}")

            return {
                "message": f"Git reset completed successfully",
                "commit": commit,
                "mode": mode,
                "files": files,
                "quiet": quiet,
                "verbose": verbose,
                "repository_path": repository_path,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git reset command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git reset failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git reset command parameters."""
        return {
            "type": "object",
            "properties": {
                "commit": {
                    "type": "string",
                    "description": "Commit to reset to",
                    "default": "HEAD",
                },
                "mode": {
                    "type": "string",
                    "description": "Reset mode (soft, mixed, hard)",
                    "default": "mixed",
                    "enum": ["soft", "mixed", "hard"],
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files to reset",
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
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
