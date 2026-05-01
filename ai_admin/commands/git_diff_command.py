from ai_admin.core.custom_exceptions import CustomError
"""Git diff command for showing differences.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitDiffCommand(BaseUnifiedCommand):
    """Show differences in Git repository.

    This command supports various Git diff operations including:
    - Show working directory changes
    - Show staged changes
    - Show changes between commits
    - Show changes for specific files
    - Unified diff format
    - Word diff
    - Color output
    """

    name = "git_diff"

    def __init__(self):
        """Initialize Git diff command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        commit1: Optional[str] = None,
        commit2: Optional[str] = None,
        files: Optional[List[str]] = None,
        staged: bool = False,
        cached: bool = False,
        unified: Optional[int] = None,
        word_diff: bool = False,
        color: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git diff command with unified security.

        Args:
            commit1: First commit to compare
            commit2: Second commit to compare
            files: List of files to diff
            staged: Show staged changes
            cached: Show cached changes
            unified: Number of context lines
            word_diff: Show word diff
            color: Color output
            user_roles: List of user roles for security validation

        Returns:
            Success result with diff information
        """
        # Use unified security approach
        return await super().execute(
            commit1=commit1,
            commit2=commit2,
            files=files,
            staged=staged,
            cached=cached,
            unified=unified,
            word_diff=word_diff,
            color=color,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git diff command."""
        return "git:diff"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git diff command logic."""
        return await self._show_diff(**kwargs)

    async def _show_diff(
        self,
        commit1: Optional[str] = None,
        commit2: Optional[str] = None,
        files: Optional[List[str]] = None,
        staged: bool = False,
        cached: bool = False,
        unified: Optional[int] = None,
        word_diff: bool = False,
        color: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Show Git diff."""
        try:
            # Build Git command
            cmd = ["git", "diff"]

            # Add options
            if staged or cached:
                cmd.append("--cached")
            if unified:
                cmd.extend(["--unified", str(unified)])
            if word_diff:
                cmd.append("--word-diff")
            if color:
                cmd.append("--color")

            # Add commits
            if commit1 and commit2:
                cmd.extend([commit1, commit2])
            elif commit1:
                cmd.append(commit1)

            # Add files if specified
            if files:
                cmd.extend(files)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Git diff failed: {result.stderr}")

            return {
                "message": f"Git diff completed successfully",
                "commit1": commit1,
                "commit2": commit2,
                "files": files,
                "staged": staged,
                "cached": cached,
                "unified": unified,
                "word_diff": word_diff,
                "color": color,
                "diff_output": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git diff command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git diff failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git diff command parameters."""
        return {
            "type": "object",
            "properties": {
                "commit1": {
                    "type": "string",
                    "description": "First commit to compare",
                },
                "commit2": {
                    "type": "string",
                    "description": "Second commit to compare",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files to diff",
                },
                "staged": {
                    "type": "boolean",
                    "description": "Show staged changes",
                    "default": False,
                },
                "cached": {
                    "type": "boolean",
                    "description": "Show cached changes",
                    "default": False,
                },
                "unified": {
                    "type": "integer",
                    "description": "Number of context lines",
                },
                "word_diff": {
                    "type": "boolean",
                    "description": "Show word diff",
                    "default": False,
                },
                "color": {
                    "type": "boolean",
                    "description": "Color output",
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
