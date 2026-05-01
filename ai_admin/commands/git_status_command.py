from ai_admin.core.custom_exceptions import CustomError
"""Git status command for showing repository status.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitStatusCommand(BaseUnifiedCommand):
    """Show Git repository status.

    This command supports various Git status operations including:
    - Working directory changes
    - Staged changes
    - Untracked files
    - Branch information
    - Commit status
    """

    name = "git_status"

    def __init__(self):
        """Initialize Git status command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        repository_path: Optional[str] = None,
        porcelain: bool = False,
        branch: bool = False,
        show_stash: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git status command with unified security.

        Args:
            repository_path: Path to repository
            porcelain: Porcelain format
            branch: Show branch information
            show_stash: Show stash information
            user_roles: List of user roles for security validation

        Returns:
            Success result with status information
        """
        # Use unified security approach
        return await super().execute(
            repository_path=repository_path,
            porcelain=porcelain,
            branch=branch,
            show_stash=show_stash,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git status command."""
        return "git:status"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git status command logic."""
        return await self._show_status(**kwargs)

    async def _show_status(
        self,
        repository_path: Optional[str] = None,
        porcelain: bool = False,
        branch: bool = False,
        show_stash: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Show Git repository status."""
        try:
            # Build Git command
            cmd = ["git", "status"]

            # Add options
            if porcelain:
                cmd.append("--porcelain")
            if branch:
                cmd.append("--branch")
            if show_stash:
                cmd.append("--show-stash")

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git status failed: {result.stderr}")

            # Parse status output
            status_lines = result.stdout.strip().split("\n")
            staged_files = []
            unstaged_files = []
            untracked_files = []
            branch_info = ""

            for line in status_lines:
                if line.startswith("On branch"):
                    branch_info = line
                elif line.startswith("Changes to be committed"):
                    continue
                elif line.startswith("Changes not staged for commit"):
                    continue
                elif line.startswith("Untracked files"):
                    continue
                elif line.startswith("\t") and line.strip():
                    if line.strip().startswith("new file:") or line.strip().startswith("modified:") or line.strip().startswith("deleted:"):
                        staged_files.append(line.strip())
                    elif line.strip().startswith("(use \"git add"):
                        continue
                    else:
                        unstaged_files.append(line.strip())
                elif line.strip() and not line.startswith("On branch") and not line.startswith("Changes") and not line.startswith("Untracked"):
                    if line.strip().startswith("??"):
                        untracked_files.append(line.strip())

            return {
                "message": f"Git status completed successfully",
                "repository_path": repository_path,
                "porcelain": porcelain,
                "branch": branch,
                "show_stash": show_stash,
                "branch_info": branch_info,
                "staged_files": staged_files,
                "unstaged_files": unstaged_files,
                "untracked_files": untracked_files,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git status command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git status failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git status command parameters."""
        return {
            "type": "object",
            "properties": {
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository",
                },
                "porcelain": {
                    "type": "boolean",
                    "description": "Porcelain format",
                    "default": False,
                },
                "branch": {
                    "type": "boolean",
                    "description": "Show branch information",
                    "default": False,
                },
                "show_stash": {
                    "type": "boolean",
                    "description": "Show stash information",
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
